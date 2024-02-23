import os
import sqlite3
import typing
from os import path

import click
import flask
from passlib.hash import pbkdf2_sha256
from werkzeug import exceptions

type papeis = typing.Literal["admin", "comum"]

APP: typing.Final[flask.Flask] = flask.Flask(__name__)
APP.secret_key = "segredo"
os.makedirs(APP.instance_path, exist_ok=True)
BANCO_DE_DADOS: typing.Final[str] = path.join(APP.instance_path, "at2.db")
with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
    CONNECTION.execute(
        """
        CREATE TABLE IF NOT EXISTS login(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            papel TEXT CHECK(papel IN ('admin', 'comum')) NOT NULL
        )"""
    ).close()


@APP.cli.command()
def add_admin():
    """Adiciona um usuário admin no banco de dados."""
    LOGIN: typing.Final[str] = click.prompt("Login", type=str)
    SENHA: typing.Final[str] = pbkdf2_sha256.hash(
        click.prompt("Senha", hide_input=True, type=str)
    )
    with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
        CURSOR: typing.Final[sqlite3.Cursor] = CONNECTION.execute(
            "INSERT INTO login(login, senha, papel) VALUES(?, ?, ?)",
            (LOGIN, SENHA, "admin"),
        )
        CONNECTION.commit()
        CURSOR.close()


@APP.route("/")
def index():
    LOGIN: typing.Final[str | None] = typing.cast(
        str | None, flask.session.get("login")
    )
    if LOGIN is None:
        return flask.redirect("/login")
    return flask.render_template("index.html", login=LOGIN)


@APP.route("/login", methods=("POST", "GET"))
def login():
    match flask.request.method:
        case "GET":
            SESSION_LOGIN: typing.Final[str | None] = typing.cast(
                str | None, flask.session.get("login")
            )
            if SESSION_LOGIN is not None:
                return flask.redirect("/")
            return flask.render_template("login.html")
        case "POST":
            FORM_LOGIN: typing.Final[str | None] = flask.request.form.get(
                "login", type=str
            )
            FORM_SENHA: typing.Final[str | None] = flask.request.form.get(
                "senha", type=str
            )
            if not FORM_LOGIN or not FORM_SENHA:
                flask.abort(400, "Login e senha são obrigatórios")
            with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
                CURSOR: typing.Final[sqlite3.Cursor] = CONNECTION.execute(
                    "SELECT senha, papel FROM login WHERE login = ?", (FORM_LOGIN,)
                )
                USUARIO: typing.Final[tuple[str, papeis]] = CURSOR.fetchone()
                CURSOR.close()
            if USUARIO and pbkdf2_sha256.verify(FORM_SENHA, USUARIO[0]):
                flask.session["login"] = FORM_LOGIN
                match USUARIO[1]:
                    case "admin":
                        return flask.redirect("/admin")
                    case "comum":
                        return flask.redirect("/perfil")
                    case _:
                        return flask.redirect("/")
            flask.abort(401, "Login ou senha inválidos")
        case _:
            flask.abort(405, "Método não permitido")


@APP.route("/registro", methods=("POST", "GET"))
def registrar():
    SESSION_LOGIN: typing.Final[str | None] = typing.cast(
        str | None, flask.session.get("login")
    )
    if SESSION_LOGIN is None:
        flask.abort(
            403, "Acesso negado, contate o administrador para registrar usuários"
        )
    with sqlite3.connect(BANCO_DE_DADOS) as connection:
        cursor: sqlite3.Cursor = connection.execute(
            "SELECT papel FROM login WHERE login = ?", (SESSION_LOGIN,)
        )
        SESSION_PAPEL: typing.Final[str | None] = cursor.fetchone()[0]
        cursor.close()
    if SESSION_PAPEL != "admin":
        flask.abort(403, "Acesso negado")
    match flask.request.method:
        case "GET":
            return flask.render_template("registro.html")
        case "POST":
            FORM_LOGIN: typing.Final[str | None] = flask.request.form.get(
                "login", type=str
            )
            FORM_SENHA: typing.Final[str | None] = flask.request.form.get(
                "senha", type=str
            )
            FORM_PAPEL: typing.Final[str | None] = flask.request.form.get(
                "papel", type=str
            )
            if not FORM_LOGIN or not FORM_SENHA or not FORM_PAPEL:
                flask.abort(400, "Todos os campos são obrigatórios")
            HASH: typing.Final[str] = pbkdf2_sha256.hash(FORM_SENHA)
            connection: sqlite3.Connection = sqlite3.connect(BANCO_DE_DADOS)
            try:
                cursor: sqlite3.Cursor = connection.execute(
                    "INSERT INTO login(login, senha, papel) VALUES(?, ?, ?)",
                    (FORM_LOGIN, HASH, FORM_PAPEL),
                )
            except sqlite3.IntegrityError:
                flask.abort(400, "Erro ao inserir registro, tente novamente")
            else:
                connection.commit()
                cursor.close()
            finally:
                connection.close()
            return flask.render_template("sucesso.html", login=FORM_LOGIN)
        case _:
            flask.abort(405, "Método não permitido")


@APP.route("/logout")
def logout():
    flask.session.pop("login")
    return flask.redirect("/login")


@APP.route("/admin")
def admin():
    SESSION_LOGIN: typing.Final[str | None] = typing.cast(
        str | None, flask.session.get("login")
    )
    with sqlite3.connect(BANCO_DE_DADOS) as CONNECITON:
        CURSOR: typing.Final[sqlite3.Cursor] = CONNECITON.execute(
            "SELECT papel FROM login WHERE login = ?", (SESSION_LOGIN,)
        )
        PAPEL: typing.Final[str | None] = CURSOR.fetchone()[0]
        CURSOR.close()
    if SESSION_LOGIN is None:
        return flask.redirect("/login")
    if PAPEL != "admin":
        flask.abort(403, "Acesso negado")
    return flask.render_template("admin.html", login=SESSION_LOGIN)


@APP.route("/perfil")
def perfil():
    LOGIN: typing.Final[str | None] = typing.cast(
        str | None, flask.session.get("login")
    )
    if LOGIN is None:
        return flask.redirect("/login")
    return flask.render_template("perfil.html", login=LOGIN)


@APP.errorhandler(Exception)
def tratar_erro(erro: Exception):
    flask.current_app.logger.exception(erro)
    if isinstance(erro, exceptions.HTTPException):
        return flask.render_template("erro.html", erro=erro), (erro.code or 500)
    return flask.render_template("erro.html", erro=erro), 500

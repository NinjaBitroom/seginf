import os
import sqlite3
import typing
from os import path

import flask
from passlib.hash import pbkdf2_sha256
from werkzeug import exceptions

APP: typing.Final[flask.Flask] = flask.Flask(__name__)
APP.secret_key = "segredo"
os.makedirs(APP.instance_path, exist_ok=True)
BANCO_DE_DADOS: typing.Final[str] = path.join(APP.instance_path, "at1.db")


with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
    CONNECTION.execute(
        """
        CREATE TABLE IF NOT EXISTS login(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL
        )"""
    ).close()


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
                    "SELECT senha FROM login WHERE login = ?", (FORM_LOGIN,)
                )
                HASH_SENHA: typing.Final[tuple[str]] = CURSOR.fetchone()
                CURSOR.close()
            if HASH_SENHA and pbkdf2_sha256.verify(FORM_SENHA, HASH_SENHA[0]):
                flask.session["login"] = FORM_LOGIN
                return flask.redirect("/")
            flask.abort(401, "Login ou senha inválidos")
        case _:
            flask.abort(405, "Método não permitido")


@APP.route("/registro", methods=("POST", "GET"))
def registrar():
    match flask.request.method:
        case "GET":
            SESSION_LOGIN: typing.Final[str | None] = typing.cast(
                str | None, flask.session.get("login")
            )
            if SESSION_LOGIN is not None:
                return flask.redirect("/")
            return flask.render_template("registro.html")
        case "POST":
            FORM_LOGIN: typing.Final[str | None] = flask.request.form.get(
                "login", type=str
            )
            FORM_SENHA: typing.Final[str | None] = flask.request.form.get(
                "senha", type=str
            )
            if not FORM_LOGIN or not FORM_SENHA:
                flask.abort(400, "Login e senha são obrigatórios")
            HASH: typing.Final[str] = pbkdf2_sha256.hash(FORM_SENHA)
            CONNECTION: typing.Final[sqlite3.Connection] = sqlite3.connect(
                BANCO_DE_DADOS
            )
            try:
                CURSOR: typing.Final[sqlite3.Cursor] = CONNECTION.execute(
                    "INSERT INTO login(login, senha) VALUES(?, ?)", (FORM_LOGIN, HASH)
                )
            except sqlite3.IntegrityError:
                flask.abort(400, "Login já existe")
            else:
                CONNECTION.commit()
                CURSOR.close()
            finally:
                CONNECTION.close()
            flask.session["login"] = FORM_LOGIN
            return flask.redirect("/")
        case _:
            flask.abort(405, "Método não permitido")


@APP.route("/logout")
def logout():
    flask.session.pop("login")
    return flask.redirect("/login")


@APP.errorhandler(Exception)
def tratar_erro(erro: Exception):
    flask.current_app.logger.exception(erro)
    if isinstance(erro, exceptions.HTTPException):
        return flask.render_template("erro.html", erro=erro), (erro.code or 500)
    return flask.render_template("erro.html", erro=erro), 500

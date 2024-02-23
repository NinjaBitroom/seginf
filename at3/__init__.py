import os
import sqlite3
import typing
from os import path

import flask
from passlib.hash import pbkdf2_sha256
from werkzeug import exceptions

type tipos = typing.Literal["corrente", "poupanca"]
type tupla_conta = tuple[int, tipos, int, float]

APP: typing.Final[flask.Flask] = flask.Flask(__name__)
APP.secret_key = "segredo"
os.makedirs(APP.instance_path, exist_ok=True)
BANCO_DE_DADOS: typing.Final[str] = path.join(APP.instance_path, "at3.db")


with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
    CURSOR: typing.Final[sqlite3.Cursor] = CONNECTION.cursor()
    CURSOR.execute(
        """
        CREATE TABLE IF NOT EXISTS conta(
            numero INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo TEXT CHECK(tipo IN ('corrente', 'poupanca')) NOT NULL,
            agencia INTEGER NOT NULL,
            saldo_inicial REAL NOT NULL,
            saldo REAL NOT NULL
        )"""
    )
    CURSOR.execute(
        """
        CREATE TABLE IF NOT EXISTS historico(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT CHECK(
                tipo IN ('saque', 'deposito', 'transferencia')
            ) NOT NULL,
            valor REAL NOT NULL,
            num_conta INTEGER NOT NULL,
            num_conta_destino INTEGER,
            FOREIGN KEY(num_conta) REFERENCES conta(numero),
            FOREIGN KEY(num_conta_destino) REFERENCES conta(numero)
        )"""
    )
    CURSOR.close()


@APP.route("/")
def index():
    LOGIN: typing.Final[str | None] = typing.cast(
        str | None,
        flask.session.get("login"),  # type: ignore
    )
    if LOGIN is None:
        return flask.redirect("/login")
    with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
        CURSOR: sqlite3.Cursor = CONNECTION.execute(
            "SELECT numero, tipo, agencia, saldo FROM conta WHERE login = ?", (LOGIN,)
        )
        CONTA: typing.Final[tupla_conta] = CURSOR.fetchone()
        CURSOR.close()
    return flask.render_template("index.html", conta=CONTA)


@APP.route("/login", methods=("POST", "GET"))
def login():
    match flask.request.method:
        case "GET":
            SESSION_LOGIN: typing.Final[str | None] = typing.cast(
                str | None,
                flask.session.get("login"),  # type: ignore
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
                    "SELECT senha FROM conta WHERE login = ?", (FORM_LOGIN,)
                )
                SENHA_HASH: typing.Final[str] = CURSOR.fetchone()
                CURSOR.close()
            if SENHA_HASH and pbkdf2_sha256.verify(FORM_SENHA, SENHA_HASH[0]):
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
                str | None,
                flask.session.get("login"),  # type: ignore
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
            FORM_TIPO: typing.Final[str | None] = flask.request.form.get(
                "tipo", type=str
            )
            FORM_AGENCIA: typing.Final[int] = flask.request.form.get("agencia", 0, int)
            FORM_SALDO: typing.Final[float] = flask.request.form.get(
                "saldo", 0.0, float
            )
            if not FORM_LOGIN or not FORM_SENHA:
                flask.abort(400, "Login e senha são obrigatórios")
            HASH: typing.Final[str] = pbkdf2_sha256.hash(FORM_SENHA)
            CONNECTION: typing.Final[sqlite3.Connection] = sqlite3.connect(
                BANCO_DE_DADOS
            )
            try:
                CURSOR: typing.Final[sqlite3.Cursor] = CONNECTION.execute(
                    """
                    INSERT INTO
                    conta(login, senha, tipo, agencia, saldo_inicial, saldo)
                    VALUES(?, ?, ?, ?, ?, ?)""",
                    (FORM_LOGIN, HASH, FORM_TIPO, FORM_AGENCIA, FORM_SALDO, FORM_SALDO),
                )
            except sqlite3.IntegrityError as e:
                print(e)
                flask.abort(400, "Erro no registro")
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
    flask.session.pop("login")  # type: ignore
    return flask.redirect("/login")


@APP.route("/sacar", methods=("POST",))
def saque():
    VALOR: typing.Final[float] = flask.request.form.get("valor", 0.0, float)
    if VALOR <= 0:
        flask.abort(400, "Valor inválido")
    LOGIN: typing.Final[str | None] = typing.cast(
        str | None,
        flask.session.get("login"),  # type: ignore
    )
    with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
        CURSOR: typing.Final[sqlite3.Cursor] = CONNECTION.execute(
            "SELECT saldo FROM conta WHERE login = ?", (LOGIN,)
        )
        SALDO: typing.Final[float] = CURSOR.fetchone()[0]
        if SALDO < VALOR:
            flask.abort(400, "Saldo insuficiente")
        CURSOR.execute(
            "UPDATE conta SET saldo = saldo - ? WHERE login = ?", (VALOR, LOGIN)
        )
        CURSOR.execute("SELECT numero FROM conta WHERE login = ?", (LOGIN,))
        NUMERO: typing.Final[int] = CURSOR.fetchone()[0]
        CURSOR.execute(
            """INSERT INTO historico(tipo, valor, num_conta)
            VALUES('saque', ?, ?)""",
            (VALOR, NUMERO),
        )
        CONNECTION.commit()
        CURSOR.close()
    return flask.redirect("/")


@APP.route("/depositar", methods=("POST",))
def deposito():
    VALOR: typing.Final[float] = flask.request.form.get("valor", 0.0, float)
    if VALOR <= 0:
        flask.abort(400, "Valor inválido")
    LOGIN: typing.Final[str | None] = typing.cast(
        str | None,
        flask.session.get("login"),  # type: ignore
    )
    with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
        CURSOR: typing.Final[sqlite3.Cursor] = CONNECTION.execute(
            "UPDATE conta SET saldo = saldo + ? WHERE login = ?", (VALOR, LOGIN)
        )
        CURSOR.execute("SELECT numero FROM conta WHERE login = ?", (LOGIN,))
        NUMERO: typing.Final[int] = CURSOR.fetchone()[0]
        CURSOR.execute(
            """INSERT INTO historico(tipo, valor, num_conta)
            VALUES('deposito', ?, ?)""",
            (VALOR, NUMERO),
        )
        CONNECTION.commit()
        CURSOR.close()
    return flask.redirect("/")


@APP.route("/transferir", methods=("POST",))
def transferencia():
    VALOR: typing.Final[float] = flask.request.form.get("valor", 0.0, float)
    NUM_DESTINO: typing.Final[int] = flask.request.form.get("destino", 0, int)
    if VALOR <= 0:
        flask.abort(400, "Valor inválido")
    LOGIN: typing.Final[str | None] = typing.cast(
        str | None,
        flask.session.get("login"),  # type: ignore
    )
    with sqlite3.connect(BANCO_DE_DADOS) as CONNECTION:
        CURSOR: typing.Final[sqlite3.Cursor] = CONNECTION.execute(
            "SELECT saldo FROM conta WHERE login = ?", (LOGIN,)
        )
        SALDO: typing.Final[float] = CURSOR.fetchone()[0]
        CURSOR.execute("SELECT numero FROM conta WHERE login = ?", (LOGIN,))
        NUMERO: typing.Final[int] = CURSOR.fetchone()[0]
        if NUMERO == NUM_DESTINO:
            flask.abort(400, "Conta destino inválida")
        if SALDO < VALOR:
            flask.abort(400, "Saldo insuficiente")
        CURSOR.execute("SELECT * FROM conta WHERE numero = ?", (NUM_DESTINO,))
        if not CURSOR.fetchone():
            flask.abort(400, "Conta destino inválida")
        CURSOR.execute(
            "UPDATE conta SET saldo = saldo - ? WHERE numero = ?", (VALOR, NUMERO)
        )
        CURSOR.execute(
            "UPDATE conta SET saldo = saldo + ? WHERE numero = ?", (VALOR, NUM_DESTINO)
        )
        CURSOR.execute(
            """INSERT INTO historico(tipo, valor, num_conta, num_conta_destino)
            VALUES('transferencia', ?, ?, ?)""",
            (VALOR, NUMERO, NUM_DESTINO),
        )
        CONNECTION.commit()
        CURSOR.close()
    return flask.redirect("/")


@APP.errorhandler(Exception)
def tratar_erro(erro: Exception):
    flask.current_app.logger.exception(erro)
    if isinstance(erro, exceptions.HTTPException):
        return flask.render_template("erro.html", erro=erro), (erro.code or 500)
    return flask.render_template("erro.html", erro=erro), 500

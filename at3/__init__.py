import os
import sqlite3
import typing
from os import path

import flask
from passlib.hash import pbkdf2_sha256
from werkzeug import exceptions

type tipos = typing.Literal['corrente', 'poupanca']
type tupla_conta = tuple[int, tipos, int, float]

app: flask.Flask = flask.Flask(__name__)
app.secret_key = 'segredo'
os.makedirs(app.instance_path, exist_ok=True)
con: sqlite3.Connection = sqlite3.connect(
    path.join(app.instance_path, 'at3.db')
)
cur: sqlite3.Cursor = con.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS conta(
        numero INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('corrente', 'poupanca')) NOT NULL,
        agencia INTEGER NOT NULL,
        saldo_inicial REAL NOT NULL,
        saldo REAL NOT NULL
    )
""")
cur.execute("""
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
    )
""")
con.commit()
cur.close()
con.close()


@app.route('/')
def index():
    login: str | None = flask.session.get('login')
    if login is None:
        return flask.redirect('/login')
    with sqlite3.connect(path.join(app.instance_path, 'at3.db')) as con:
        cur = con.execute(
            "SELECT numero, tipo, agencia, saldo FROM conta WHERE login = ?",
            (login,)
        )
        conta: tupla_conta = cur.fetchone()
        cur.close()
    return flask.render_template('index.html', conta=conta)


@app.route('/login', methods=('POST', 'GET'))
def login():
    match flask.request.method:
        case 'GET':
            login: str | None = flask.session.get('login')
            if login is not None:
                return flask.redirect('/')
            return flask.render_template('login.html')
        case 'POST':
            login: str | None = flask.request.form.get('login')
            senha: str | None = flask.request.form.get('senha')
            if not login or not senha:
                flask.abort(400, 'Login e senha são obrigatórios')
            con: sqlite3.Connection = sqlite3.connect(
                path.join(app.instance_path, 'at3.db')
            )
            cur: sqlite3.Cursor = con.execute(
                "SELECT senha FROM conta WHERE login = ?",
                (login,)
            )
            senha_hash: str = cur.fetchone()
            cur.close()
            con.close()
            if senha_hash and pbkdf2_sha256.verify(senha, senha_hash[0]):
                flask.session['login'] = login
                return flask.redirect('/')
            flask.abort(401, 'Login ou senha inválidos')
        case _:
            flask.abort(405, 'Método não permitido')


@app.route('/registro', methods=('POST', 'GET'))
def registrar():
    match flask.request.method:
        case 'GET':
            login: str | None = flask.session.get('login')
            if login is not None:
                return flask.redirect('/')
            return flask.render_template('registro.html')
        case 'POST':
            login: str | None = flask.request.form.get('login')
            senha: str | None = flask.request.form.get('senha')
            tipo: str | None = flask.request.form.get('tipo')
            agencia: int = int(flask.request.form.get('agencia', 0))
            saldo: float = float(flask.request.form.get('saldo', 0))
            if not login or not senha:
                flask.abort(400, 'Login e senha são obrigatórios')
            hash: str = pbkdf2_sha256.hash(senha)
            con: sqlite3.Connection = sqlite3.connect(
                path.join(app.instance_path, 'at3.db')
            )
            try:
                cur: sqlite3.Cursor = con.execute("""INSERT INTO
                    conta(login, senha, tipo, agencia, saldo_inicial, saldo)
                    VALUES(?, ?, ?, ?, ?, ?)""",
                    (login, hash, tipo, agencia, saldo, saldo),
                )
            except sqlite3.IntegrityError as e:
                print(e)
                flask.abort(400, 'Erro no registro')
            else:
                con.commit()
                cur.close()
            finally:
                con.close()
            flask.session['login'] = login
            return flask.redirect('/')
        case _:
            flask.abort(405, 'Método não permitido')


@app.route('/logout')
def logout():
    flask.session.pop('login')
    return flask.redirect('/login')


@app.route('/sacar', methods=('POST',))
def saque():
    valor: float = float(flask.request.form.get('valor', 0))
    if valor <= 0:
        flask.abort(400, 'Valor inválido')
    login: str | None = flask.session.get('login')
    with sqlite3.connect(path.join(app.instance_path, 'at3.db')) as con:
        cur: sqlite3.Cursor = con.execute(
            "SELECT saldo FROM conta WHERE login = ?",
            (login,)
        )
        saldo: float = cur.fetchone()[0]
        if saldo < valor:
            flask.abort(400, 'Saldo insuficiente')
        cur.execute(
            "UPDATE conta SET saldo = saldo - ? WHERE login = ?",
            (valor, login)
        )
        cur.execute("SELECT numero FROM conta WHERE login = ?", (login,))
        numero: int = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO historico(tipo, valor, num_conta)
            VALUES('saque', ?, ?)""",
            (valor, numero)
        )
        con.commit()
        cur.close()
    return flask.redirect('/')


@app.route('/depositar', methods=('POST',))
def deposito():
    valor: float = float((flask.request.form).get('valor', 0))
    if valor <= 0:
        flask.abort(400, 'Valor inválido')
    login: str | None = flask.session.get('login')
    with sqlite3.connect(path.join(app.instance_path, 'at3.db')) as con:
        cur: sqlite3.Cursor = con.execute(
            "UPDATE conta SET saldo = saldo + ? WHERE login = ?",
            (valor, login)
        )
        cur.execute("SELECT numero FROM conta WHERE login = ?", (login,))
        numero: int = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO historico(tipo, valor, num_conta)
            VALUES('deposito', ?, ?)""",
            (valor, numero)
        )
        con.commit()
        cur.close()
    return flask.redirect('/')


@app.route('/transferir', methods=('POST',))
def transferencia():
    valor: float = float(flask.request.form.get('valor', 0))
    num_destino: int = int(flask.request.form.get('destino', 0))
    if valor <= 0:
        flask.abort(400, 'Valor inválido')
    login: str | None = flask.session.get('login')
    with sqlite3.connect(path.join(app.instance_path, 'at3.db')) as con:
        cur: sqlite3.Cursor = con.execute(
            "SELECT saldo FROM conta WHERE login = ?",
            (login,)
        )
        saldo: float = cur.fetchone()[0]
        cur.execute("SELECT numero FROM conta WHERE login = ?", (login,))
        numero: int = cur.fetchone()[0]
        if numero == num_destino:
            flask.abort(400, 'Conta destino inválida')
        if saldo < valor:
            flask.abort(400, 'Saldo insuficiente')
        cur.execute(
            "SELECT * FROM conta WHERE numero = ?",
            (num_destino,)
        )
        if not cur.fetchone():
            flask.abort(400, 'Conta destino inválida')
        cur.execute(
            "UPDATE conta SET saldo = saldo - ? WHERE numero = ?",
            (valor, numero)
        )
        cur.execute(
            "UPDATE conta SET saldo = saldo + ? WHERE numero = ?",
            (valor, num_destino)
        )
        cur.execute(
            """INSERT INTO historico(tipo, valor, num_conta, num_conta_destino)
            VALUES('transferencia', ?, ?, ?)""",
            (valor, numero, num_destino)
        )
        con.commit()
        cur.close()
    return flask.redirect('/')


@app.errorhandler(Exception)
def tratar_erro(e: Exception):
    flask.current_app.logger.exception(e)
    if isinstance(e, exceptions.HTTPException):
        return flask.render_template('erro.html', erro=e), (e.code or 500)
    return flask.render_template('erro.html', erro=e), 500

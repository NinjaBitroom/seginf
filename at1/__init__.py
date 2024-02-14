import flask
import sqlite3
import os
from os import path
from passlib.hash import pbkdf2_sha256
from werkzeug import exceptions


app: flask.Flask = flask.Flask(__name__)
app.secret_key = 'segredo'
os.makedirs(app.instance_path, exist_ok=True)
con: sqlite3.Connection = sqlite3.connect(
    path.join(app.instance_path, 'at1.db')
)
cur: sqlite3.Cursor = con.execute("""
    CREATE TABLE IF NOT EXISTS login(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL
    )
""")
cur.close()
con.close()


@app.route('/')
def index():
    logado: bool = flask.session.get('logado', False)
    if not logado:
        return flask.redirect('/login')
    return flask.render_template('index.html')


@app.route('/login', methods=('POST', 'GET'))
def login():
    match flask.request.method:
        case 'GET':
            logado: bool = flask.session.get('logado', False)
            if logado:
                return flask.redirect('/')
            return flask.render_template('login.html')
        case 'POST':
            login: str = flask.request.form.get('login')
            senha: str = flask.request.form.get('senha')
            if not login or not senha:
                flask.abort(400, 'Login e senha são obrigatórios')
            con: sqlite3.Connection = sqlite3.connect(
                path.join(app.instance_path, 'at1.db')
            )
            cur: sqlite3.Cursor = con.execute(
                "SELECT senha FROM login WHERE login = ?",
                (login,)
            )
            senha_hash: tuple[str] = cur.fetchone()
            cur.close()
            con.close()
            if senha_hash and pbkdf2_sha256.verify(senha, senha_hash[0]):
                flask.session['logado'] = True
                return flask.redirect('/')
            flask.abort(401, 'Login ou senha inválidos')
        case _:
            flask.abort(405, 'Método não permitido')


@app.route('/registro', methods=('POST', 'GET'))
def registrar():
    match flask.request.method:
        case 'GET':
            logado: bool = flask.session.get('logado', False)
            if logado:
                return flask.redirect('/')
            return flask.render_template('registro.html')
        case 'POST':
            login: str = flask.request.form.get('login')
            senha: str = flask.request.form.get('senha')
            if not login or not senha:
                flask.abort(400, 'Login e senha são obrigatórios')
            hash: str = pbkdf2_sha256.hash(senha)
            con: sqlite3.Connection = sqlite3.connect(
                path.join(app.instance_path, 'at1.db')
            )
            try:
                cur = con.execute(
                    "INSERT INTO login(login, senha) VALUES(?, ?)",
                    (login, hash)
                )
            except sqlite3.IntegrityError:
                flask.abort(400, 'Login já existe')
            else:
                con.commit()
                cur.close()
            finally:
                con.close()
            flask.session['logado'] = True
            return flask.redirect('/')
        case _:
            flask.abort(405, 'Método não permitido')


@app.route('/logout')
def logout():
    flask.session.pop('logado')
    return flask.redirect('/login')


@app.errorhandler(Exception)
def tratar_erro(e: Exception):
    flask.current_app.logger.exception(e)
    if isinstance(e, exceptions.HTTPException):
        return flask.render_template('erro.html', erro=e), (e.code or 500)
    return flask.render_template('erro.html', erro=e), 500

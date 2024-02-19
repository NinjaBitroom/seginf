import os
import sqlite3
import typing
from os import path

import click
import flask
from passlib.hash import pbkdf2_sha256
from werkzeug import exceptions

type papeis = typing.Literal['admin', 'comum']

app: flask.Flask = flask.Flask(__name__)
app.secret_key = 'segredo'
os.makedirs(app.instance_path, exist_ok=True)
con: sqlite3.Connection = sqlite3.connect(
    path.join(app.instance_path, 'at2.db')
)
cur: sqlite3.Cursor = con.execute("""
    CREATE TABLE IF NOT EXISTS login(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        papel TEXT CHECK(papel IN ('admin', 'comum')) NOT NULL
    )
""")
cur.close()
con.close()


@app.cli.command()
def add_admin():
    """Adiciona um usuário admin no banco de dados."""
    login: str = click.prompt('Login', type=str)
    senha: str = pbkdf2_sha256.hash(
        click.prompt('Senha', hide_input=True, type=str)
    )
    con: sqlite3.Connection = sqlite3.connect(
        path.join(app.instance_path, 'at2.db')
    )
    cur: sqlite3.Cursor = con.execute(
        "INSERT INTO login(login, senha, papel) VALUES(?, ?, ?)",
        (login, senha, 'admin')
    )
    con.commit()
    cur.close()
    con.close()


@app.route('/')
def index():
    login: str | None = flask.session.get('login')
    if login is None:
        return flask.redirect('/login')
    return flask.render_template('index.html', login=login)


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
                path.join(app.instance_path, 'at2.db')
            )
            cur: sqlite3.Cursor = con.execute(
                "SELECT senha, papel FROM login WHERE login = ?",
                (login,)
            )
            usuario: tuple[str, papeis] = cur.fetchone()
            cur.close()
            con.close()
            if usuario and pbkdf2_sha256.verify(senha, usuario[0]):
                flask.session['login'] = login
                match usuario[1]:
                    case 'admin':
                        return flask.redirect('/admin')
                    case 'comum':
                        return flask.redirect('/perfil')
                    case _:
                        return flask.redirect('/')
            flask.abort(401, 'Login ou senha inválidos')
        case _:
            flask.abort(405, 'Método não permitido')


@app.route('/registro', methods=('POST', 'GET'))
def registrar():
    login: str | None = flask.session.get('login')
    if login is None:
        flask.abort(
            403,
            'Acesso negado, contate o administrador para registrar usuários'
        )
    con: sqlite3.Connection = sqlite3.connect(
        path.join(app.instance_path, 'at2.db')
    )
    cur: sqlite3.Cursor = con.execute(
        "SELECT papel FROM login WHERE login = ?",
        (login,)
    )
    papel: str | None = cur.fetchone()[0]
    cur.close()
    con.close()
    if papel != 'admin':
        flask.abort(403, 'Acesso negado')
    match flask.request.method:
        case 'GET':
            return flask.render_template('registro.html')
        case 'POST':
            login: str | None = flask.request.form.get('login')
            senha: str | None = flask.request.form.get('senha')
            papel = flask.request.form.get('papel')
            if not login or not senha or not papel:
                flask.abort(400, 'Todos os campos são obrigatórios')
            hash: str = pbkdf2_sha256.hash(senha)
            con: sqlite3.Connection = sqlite3.connect(
                path.join(app.instance_path, 'at2.db')
            )
            try:
                cur: sqlite3.Cursor = con.execute(
                    "INSERT INTO login(login, senha, papel) VALUES(?, ?, ?)",
                    (login, hash, papel)
                )
            except sqlite3.IntegrityError:
                flask.abort(400, 'Erro ao inserir registro, tente novamente')
            else:
                con.commit()
                cur.close()
            finally:
                con.close()
            return flask.render_template(
                'sucesso.html',
                login=login
            )
        case _:
            flask.abort(405, 'Método não permitido')


@app.route('/logout')
def logout():
    flask.session.pop('login')
    return flask.redirect('/login')


@app.route('/admin')
def admin():
    login: str | None = flask.session.get('login')
    con: sqlite3.Connection = sqlite3.connect(
        path.join(app.instance_path, 'at2.db')
    )
    cur: sqlite3.Cursor = con.execute(
        "SELECT papel FROM login WHERE login = ?",
        (login,)
    )
    papel: str | None = cur.fetchone()[0]
    cur.close()
    con.close()
    if login is None:
        return flask.redirect('/login')
    if papel != 'admin':
        flask.abort(403, 'Acesso negado')
    return flask.render_template('admin.html', login=login)


@app.route('/perfil')
def perfil():
    login: str | None = flask.session.get('login')
    if login is None:
        return flask.redirect('/login')
    return flask.render_template('perfil.html', login=login)


@app.errorhandler(Exception)
def tratar_erro(e: Exception):
    flask.current_app.logger.exception(e)
    if isinstance(e, exceptions.HTTPException):
        return flask.render_template('erro.html', erro=e), (e.code or 500)
    return flask.render_template('erro.html', erro=e), 500

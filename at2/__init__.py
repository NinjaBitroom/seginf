import flask
import sqlite3
from passlib.hash import pbkdf2_sha256
import typing
import click
import os
from os import path

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
def admin():
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
                flask.session['logado'] = True
                flask.session['papel'] = usuario[1]
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
    papel_sessao: papeis = flask.session.get('papel')
    if papel_sessao != 'admin':
        flask.abort(403, 'Acesso negado')
    match flask.request.method:
        case 'GET':
            return flask.render_template('registro.html')
        case 'POST':
            login: str = flask.request.form.get('login')
            senha: str = flask.request.form.get('senha')
            papel: str = flask.request.form.get('papel')
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
            return flask.render_template_string(
                'Registro de {{ login }} realizado com sucesso',
                login=login
            )
        case _:
            flask.abort(405, 'Método não permitido')


@app.route('/logout')
def logout():
    flask.session.pop('logado')
    flask.session.pop('papel')
    return flask.redirect('/login')


@app.route('/admin')
def admin():
    logado: bool = flask.session.get('logado', False)
    papel: papeis = flask.session.get('papel')
    if (not logado):
        return flask.redirect('/login')
    if papel != 'admin':
        flask.abort(403, 'Acesso negado')
    return flask.render_template('admin.html')


@app.route('/perfil')
def perfil():
    logado: bool = flask.session.get('logado', False)
    if not logado:
        return flask.redirect('/login')
    return flask.render_template('perfil.html')


if __name__ == '__main__':
    app.run()

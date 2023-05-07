from flask import Flask, render_template, request, make_response, redirect, send_file
from hashlib import md5
import sqlite3 as sql

import utils.util as utils


app = Flask(__name__)

conn = sql.connect('database.db', check_same_thread=False)

cookies = {}

@app.route('/')
def index():
    # check cookie
    c = request.cookies.get('session')
    if c in cookies:
        return redirect('/dashboard')
    
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    cur = conn.cursor()
    hashed_password = utils.hash_password(password)
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
    user = cur.fetchone()
    if user:
        c = utils.generate_cookie()
        cookies[c] = user
        r = make_response()
        r.set_cookie('session', c)
        r.status_code = 302
        r.headers['Location'] = '/dashboard'
        return r
    else:
        return render_template('login.html', error='Invalid username or password')

@app.route('/register')
def register():
    # check cookie
    c = request.cookies.get('session')
    if c in cookies:
        return redirect('/dashboard')
    
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form['username']
    password = request.form['password']
    inviter = request.form['inviter']

    cur = conn.cursor()

    # count inviter exists = 1
    count = cur.execute(f"SELECT COUNT(*) FROM users WHERE username = '{inviter}'").fetchone()[0]
    if count < 1:
        return render_template('register.html', error='Invalid inviter')
    
    # check if username exists
    count = cur.execute(f"SELECT COUNT(*) FROM users WHERE username = ?", (username,)).fetchone()[0]
    if count != 0:
        return render_template('register.html', error='Username already exists')
    

    hashed_password = utils.hash_password(password)
    uid = utils.generate_user_id()
    cur.execute("INSERT INTO users (id, username, password) VALUES (?, ?, ?)", (uid, username, hashed_password))
    conn.commit()
    return render_template('index.html', error='Account created successfully')

@app.route('/dashboard', methods=['GET'])
def dashboard():
    # check cookie
    c = request.cookies.get('session')
    if c not in cookies:
        return render_template('index.html', error='Please login first')
    user = cookies[c]

    # get files from db
    cur = conn.cursor()
    files = cur.execute(f"SELECT files.id, files.owner, files.name, users.username FROM files LEFT JOIN users ON files.owner = users.id").fetchall()
    return render_template('dashboard.html', files=files, user=user)

@app.route('/upload', methods=['GET'])
def upload():
    # check cookie
    c = request.cookies.get('session')
    if c not in cookies:
        return render_template('index.html', error='Please login first')
    user = cookies[c]

    return render_template('upload.html', user=user)

@app.route('/upload', methods=['POST'])
def upload_post():
    # check cookie
    c = request.cookies.get('session')
    if c not in cookies:
        return render_template('index.html', error='Please login first')
    user = cookies[c]

    u_file = request.files['file']
    name = u_file.filename

    cur = conn.cursor()
    file_h = md5()
    file_h.update(name.encode())
    file_id = file_h.hexdigest()

    # check if id exists
    count = cur.execute(f"SELECT COUNT(*) FROM files WHERE id = ?", (file_id,)).fetchone()[0]
    if count != 0:
        file_id = utils.generate_user_id()

    cur.execute("INSERT INTO files (id, name, owner) VALUES (?, ?, ?)", (file_id, name, user[0]))
    conn.commit()

    if count == 0:
        u_file.save(f'files/{file_id}-{name}')

    return redirect('/dashboard')

@app.route('/download/<file_id>', methods=['GET'])
def download(file_id):
    # check cookie
    c = request.cookies.get('session')
    if c not in cookies:
        return render_template('index.html', error='Please login first')
    user = cookies[c]

    cur = conn.cursor()
    d_file = cur.execute("SELECT * FROM files WHERE id = ? AND owner = ?", (file_id, user[0])).fetchone()
    if not d_file:
        return render_template('dashboard.html', error='File not found')

    h = md5()
    h.update(d_file[2].encode())
    hashed = h.hexdigest()

    return send_file(f'files/{hashed}-{d_file[2]}', as_attachment=True)


@app.route('/logout', methods=['GET'])
def logout():
    # check cookie
    c = request.cookies.get('session')
    if c not in cookies:
        return render_template('index.html', error='Please login first')
    user = cookies[c]

    cookies.pop(c)
    r = make_response()
    r.set_cookie('session', '', expires=0)
    r.status_code = 302
    r.headers['Location'] = '/'
    return r

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
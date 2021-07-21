from typing import Counter
from flask import Flask, json, request, render_template, make_response, jsonify
import sqlite3
import config
import secrets

app = Flask(__name__)
conn = sqlite3.connect(config.USER_DATABASE, check_same_thread=False)
cur = conn.cursor()

@app.route('/', methods=['POST', 'GET'])
def main_page():
    #TODO : admin panel site
    pass

@app.route('/login', methods=['POST'])
def login():
    data = request.form
    username = data['username']
    password = data['password']
    email = data['email']

    cur.execute(f'SELECT * FROM users WHERE username = \"{username}\" AND passsword = \"{password}\" AND email = "{email}";')
    login_check = cur.fetchall()
    try:
        if login_check[0]:
            return "Login seccsfully"
    except IndexError:
        return "username or password or email is incorrect"

@app.route('/add_user', methods=['POST'])
def add_user():
    pass
    data = request.form
    username = data['username']
    password = data['password']
    email = data['email']

    cur.execute(f'SELECT * FROM users WHERE username = "{username}";')
    username_check = cur.fetchall()
    cur.execute(f'SELECT * FROM users WHERE email = "{email}";')
    email_check = cur.fetchall()

    try:
        if username_check[0]:
            username_check = False
    except IndexError:
        username_check = True

    try:
        if email_check[0]:
            email_check = False
    except IndexError:
        email_check = True

    if username_check and email_check:
        response = "NO MATCH FOUND"
    elif not username_check and email_check:
        return jsonify({"status" : "USERNAME MATCH FOUND"})
    elif username_check and not email_check:
        return jsonify({"status" : "EMAIL MATCH FOUND"})
    else:
        return jsonify({"status" : "MATCH FOUND"})
    
    if response == "NO MATCH FOUND":
        loop = True
        while loop:
            token = secrets.token_hex(24)
            cur.execute(f'SELECT * FROM users WHERE token = "{token}";')
            token_check = cur.fetchall()
            try:
                if token_check[0]:
                    continue
            except IndexError:
                token_check = True
                loop = False

    cur.execute(f'INSERT INTO users (username, password, token, email) VALUES ("{username}", "{password}", "{token}", "{email}");')
    conn.commit()
    send_data = {"status" : "OK", "token" : token}
    return send_data

if __name__ == "__main__":
    app.run('0.0.0.0', 5000, debug=True)
    conn.close()
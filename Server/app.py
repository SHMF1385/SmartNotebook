from flask import Flask, json, request, render_template, make_response, jsonify
import sqlite3
import config

app = Flask(__name__)
conn = sqlite3.connect(config.USER_DATABASE, check_same_thread=False)
cur = conn.cursor()

@app.route('/', methods=['POST', 'GET'])
def main_page():
    #TODO : admin panel site
    pass

@app.route('/check_user', methods=['POST'])
def check_user():
    username = request.form.get('username')
    password = request.form.get('password')
    cur.execute(f"SELECT * FROM users WHERE username == \"{username}\" AND passsword == \"{password}\";")
    fetch = cur.fetchall()
    try:
        if fetch[0]:
            return "username and password is correct"
    except IndexError:
        return "username or password is incorrect"

if __name__ == "__main__":
    app.run('0.0.0.0', 5000, debug=True)
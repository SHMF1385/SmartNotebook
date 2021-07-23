from typing import Counter
from flask import Flask, json, request, render_template, make_response, jsonify
import sqlite3
import config
import secrets
import random
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
def signup():
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

def send_vrification_code_email(sender_email_addr, receiver_email_addr, sender_email_password):
    verification_code = ""
    for i in range(5):
        j = random.randint(0,9)
        verification_code += str(j)
    
    message = MIMEMultipart("alternative")
    message['Subject'] = "code taeed"
    message['From'] = sender_email_addr
    message['To'] = receiver_email_addr

    Message = """\
        <!DOCTYPE html>
        <meta charset="utf-8">
        <html>
            <body>
                <div dir="rtl">
                <p>کد تایید دفترچه یادداشت : {}</p>
                </div>
            </body>
        </html>"""

    attach_html = MIMEText(Message, "html")
    message.attach(attach_html)

    contex = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=contex) as server:
        server.login(sender_email_addr, sender_email_password)
        server.sendmail(sender_email_addr, receiver_email_addr, message.as_string())
        server.close()
    
    return verification_code


if __name__ == "__main__":
    app.run('0.0.0.0', 5000, debug=True)
    conn.close()
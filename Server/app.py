from flask import Flask, json, request, render_template, make_response, jsonify
import sqlite3
import config
import secrets
import random
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import socket

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
    username = data['username'].upper()
    password = data['password']
    email = data['email'].split('@')
    email[0] = email[0].replace('.', '')
    email = email[0] + '@' + email[1]

    cur.execute(f'SELECT * FROM users WHERE username = \"{username}\" AND passsword = \"{password}\" AND email = "{email}";')
    login_check = cur.fetchall()
    try:
        if login_check[0]:
            pass
    except IndexError:
        return jsonify({"status" : "MATCH NOT FOUND"})
    
    verification = send_vrification_code_email(config.SENDER_EMAIL, email, config.SENDER_EMAIL_PASSWORD)
    if verificate_email(verification):
        cur.execute(f'SELECT * FROM users WHERE username = "{username}" AND password = "{password}"')
        user_token = cur.fetchall()[0][2]
        send_data = {"status" : "OK", "TOEKN" : user_token}
        return jsonify(send_data)
    else:
        return jsonify({"status" : "VERIFICATION FAILED"})

@app.route('/signup', methods=['POST'])
def signup():
    pass
    data = request.form
    username = data['username'].upper()
    password = data['password']
    email = data['email'].split('@')
    email[0] = email[0].replace('.', '')
    email = email[0] + '@' + email[1]

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
        pass
    elif not username_check and email_check:
        return jsonify({"status" : "USERNAME MATCH FOUND"})
    elif username_check and not email_check:
        return jsonify({"status" : "EMAIL MATCH FOUND"})
    else:
        return jsonify({"status" : "MATCH FOUND"})

    verification = send_vrification_code_email(config.SENDER_EMAIL, email, config.SENDER_EMAIL_PASSWORD)
    if verificate_email(verification):
        pass
    else:
        return jsonify({"status" : "VERIFICATION FAILED"})
    
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
    return jsonify(send_data)

@app.route('/verificate_email', methods = ['POST'])
def verificate_email(verification_code):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5001))
    server.listen(1)
    server.settimeout(10)

    connection, addr = server.accept()
    verification_key = connection.recv(1024).decode()
    if int(verification_key):
        if verification_key == verification_code:
            return True
        else:
            return False
    else:
        return False

def send_vrification_code_email(sender_email_addr, receiver_email_addr, sender_email_password):
    verification_code = ""
    for i in range(5):
        j = random.randint(0,9)
        verification_code += str(j)
    
    message = MIMEMultipart("alternative")
    message['Subject'] = "کد تایید"
    message['From'] = sender_email_addr
    message['To'] = receiver_email_addr

    Message = f"""\
        <!DOCTYPE html>
        <meta charset="utf-8">
        <html>
            <body>
                <div dir="rtl">
                <p>کد تایید دفترچه یادداشت : {verification_code}</p>
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
    cur.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT, token TEXT, email TEXT);')
    app.run('0.0.0.0', 5000, debug=True)
    conn.close()
import sqlite3
import secrets
import random
import smtplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

import config
from flask import Flask, request, render_template, jsonify, redirect, flash, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from github import Github

app = Flask(__name__)
conn = sqlite3.connect(config.DATABASE_FILE_NAME, check_same_thread=False)
cur = conn.cursor()
Gdatabase = Github(config.GITHUB_DATABASE_ACCESS_TOKEN)
app.config['SECRET_KEY'] = config.SECRET_KEY
limiter = Limiter(app, key_func=get_remote_address)
admin_loged_in = False

@app.route('/')
def main_page():
    #home page
    pass

@app.route('/admin', methods=['POST', 'GET'])
@limiter.limit('5 per minute')
def admin():
    if request.method == 'GET':
        return render_template('login.html')
    if request.method == 'POST':
        data = request.form
        username = data['username']
        password = data['password']
        if (username == config.ADMIN_USERNAME) and (password == config.ADMIN_PASSWORD):
            cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("ادمین", "ورود ادمین", "{get_date()}", "{get_time()}", "موفق");')
            flash('شما با موفقیت وارد شدید', 'success')
            admin_loged_in = True
            cur.execute('SELECT count FROM created_files_status;')
            created_files_count = cur.fetchone()[0]
            cur.execute('SELECT count FROM updated_files_status;')
            updated_files_count = cur.fetchone()[0]
            cur.execute('SELECT count FROM actived_users_status;')
            actived_users_count = cur.fetchone()[0]
            cur.execute('SELECT count FROM deleted_users_status;')
            deleted_users_count = cur.fetchone()[0]
            cur.execute('SELECT * FROM logs;')
            logs = cur.fetchall()
            logs = logs[::-1]
            logs_value= []
            for i in logs:
                logs_value.append({'username': i[0], 'work': i[1], 'date': i[2], 'time': i[3], 'status': i[4]})
            conn.commit()
            return render_template('index.html', data={'created_files_count': str(created_files_count), 'updated_files_count': str(updated_files_count), 'actived_users_count': str(actived_users_count), 'deleted_users_count': str(deleted_users_count), 'logs': logs_value})
        else:
            flash('نام کاربری یا گذرواژه اشتباه است', 'danger')
            cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("ادمین", "ورود ادمین", "{get_date()}", "{get_time()}", "نا موفق");')
            conn.commit()
            return redirect(request.url)

@app.route('/admin/settings')
def admin_settings():
    # TODO: admin settings
    pass

@app.route('/admin/logout')
def admin_logout():
    if admin_loged_in:
        admin_loged_in = False
        return redirect('/')
    else:
        return abort(401)

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
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ورود", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({"status" : "MATCH NOT FOUND"})

        cur.execute(f'SELECT * FROM users WHERE username = "{username}" AND password = "{password}"')
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ورود", "{get_date()}", "{get_time()}", "موفق");')
        user_token = cur.fetchall()[0][2]
        send_data = {"status" : "OK", "Token" : user_token}
        return jsonify(send_data)

@app.route('/signup', methods=['POST'])
def signup():
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
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ایجاد حساب", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({"status" : "USERNAME MATCH FOUND"})
    elif username_check and not email_check:
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ایجاد حساب", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({"status" : "EMAIL MATCH FOUND"})
    else:
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ایجاد حساب", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({"status" : "MATCH FOUND"})

    verification = send_vrification_code_email(config.SENDER_EMAIL, email, config.SENDER_EMAIL_PASSWORD)
    if verificate_email(verification):
        pass
    else:
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ایجاد حساب", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
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
    cur.execute('SELECT count FROM actived_users_status;')
    actived_users_count = cur.fetchone()[0]
    cur.execute(f'UPDATE actived_users_status SET count = {actived_users_count + 1};')
    cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ایجاد حساب", "{get_date()}", "{get_time()}", "موفق");')
    conn.commit()
    send_data = {"status" : "OK", "Token" : token}
    return jsonify(send_data)

@app.route('/del_user', methods= ['POST'])
def del_user():
    data = request.form
    username = data['username'].upper()
    token = data['token']

    cur.execute(f'SELECT * FROM users WHERE username = "{username}" AND token = "{token}";')
    check = cur.fetchall()
    try:
        if check[0]:
            pass
    except IndexError:
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "حذف حساب", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({'status': 'TOKEN NOT MATCHED'})
    cur.execute(f'DELETE FROM users WHERE username="{username}";')
    repo = Gdatabase.get_repo(config.GDATABASE_REPO)
    contents = repo.get_contents(f"{username}")
    for filename in contents:
        repo.delete_file(filename.path, f"DELETE USER FILES {username} {get_datetime()}", filename.sha)
    cur.execute('SELECT count FROM deleted_users_status;')
    deleted_users_count = cur.fetchone()[0]
    cur.execute(f'UPDATE deleted_users_status SET count = {deleted_users_count + 1};')
    cur.execute('SELECT count FROM actived_users_status;')
    actived_users_count = cur.fetchone()[0]
    cur.execute(f'UPDATE actived_users_status SET count = {actived_users_count - 1};')
    cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "delete user", "{get_date()}", "{get_time()}", "OK");')
    conn.commit()
    return jsonify({'status': 'USER DELETED'})

@app.route('/verificate_email', methods = ['POST'])
def verificate_email(verification_code):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5001))
    server.listen(1)
    server.settimeout(60)

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
        rand = random.randint(0,9)
        verification_code += str(rand)

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

@app.route('/create_file', methods=['POST'])
def create_file():
    username = request.form['username']
    token = request.form['token']
    filename = request.form['filename']
    content = request.form['content']

    cur.execute(f'SELECT * FROM users WHERE username="{username}" AND token="{token}";')
    check = cur.fetchall()

    try:
        if check[0]:
            pass
    except IndexError:
        return jsonify({'status': 'AUTHENTICATION FAILED'})

    try:
        repo = Gdatabase.get_repo(config.GDATABASE_REPO)
        repo.create_file(f"{username}/{filename}.note", f"CREATE {username}/{filename} {get_datetime()}", str(content))
        cur.execute('SELECT count FROM created_files_status;')
        created_files_count = cur.fetchone()[0]
        cur.execute(f'UPDATE created_files_status SET count = {created_files_count + 1};')
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ایجاد فایل", "{get_date()}", "{get_time()}", "موفق");')
        conn.commit()
        return jsonify({'status': 'FILE CREATED'})
    except:
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "ایجاد فایل", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({'status': 'CREATE FILE FAILED'})

@app.route('/get_file', methods=['POST'])
def get_file():
    data = request.form
    username = data['username'].upper()
    token = data['token']
    filename = data['filename']

    cur.execute(f'SELECT * FROM users WHERE username = "{username}" AND token = "{token}"')
    check = cur.fetchone()

    try:
        if check[0]:
            pass
    except IndexError:
        return jsonify({'status': 'AUTHENTICATION FAILED'})

    try:
        repo = Gdatabase.get_repo(config.GDATABASE_REPO)
        file = repo.get_contents(f"{username}/{filename}.note")
        file_content = file.decoded_content.decode()
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "دریافت محتوای فایل", "{get_date()}", "{get_time()}", "موفق");')
        conn.commit()
        return jsonify({'content': file_content})
    except:
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "دریافت محتوای فایل", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({'status': 'CREATE FILE FAILED'})

@app.route('/update_file', methods=['POST'])
def update_file():
    username = request.form['username']
    token = request.form['token']
    filename = request.form['filename']
    content = request.form['content']

    cur.execute(f'SELECT * FROM users WHERE username = "{username}" AND token = "{token}";')
    check = cur.fetchall()

    try:
        if check[0]:
            pass
    except IndexError:
        return jsonify({'status': 'AUTHENTICATION FAILED'})
    try:
        repo = Gdatabase.get_repo(config.GDATABASE_REPO)
        contents = repo.get_contents(f"{username}/{filename}.note")
        repo.update_file(contents.path, f"UPDATE {username}/{filename} {get_datetime()}" , content, contents.sha)
        cur.execute('SELECT count FROM updated_files_status;')
        updated_files_count = cur.fetchone()[0]
        cur.execute(f'UPDATE updated_files_status SET count = {updated_files_count + 1};')
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "به روزرسانی فایل", "{get_date()}", "{get_time()}", "موفق");')
        conn.commit()
        return jsonify({'status': 'FILE UPDATED'})
    except:
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "به روزرسانی فایل", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({'status': "UPDATE FILE FAILED"})

@app.route('/delete_file', methods=['POST'])
def delete_file():
    username = request.form['username']
    token = request.form['token']
    filename = request.form['filename']

    cur.execute(f'SELECT * FROM users WHERE username = "{username}" AND token = "{token}";')
    check = cur.fetchall()

    try:
        if check[0]:
            pass
    except IndexError:
        return jsonify({'status': 'AUTHENTICATION FAILED'})

    try:
        repo = Gdatabase.get_repo(config.GDATABASE_REPO)
        contents = repo.get_contents(f"{username}/{filename}.note")
        repo.delete_file(contents.path, f"DELETE {username}/{filename} {get_datetime()}", contents.sha)
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "حذف فایل", "{get_date()}", "{get_time()}", "موفق");')
        conn.commit()
        return jsonify({'status': 'FILE DELETED'})
    except:
        cur.execute(f'INSERT INTO logs (username, work, date, time, status) VALUES ("{username}", "حذف فایل", "{get_date()}", "{get_time()}", "نا موفق");')
        conn.commit()
        return jsonify({'status': 'DELETE FILE FAILED'})

def get_date():
    now = datetime.now()
    return( str(now.year) + '/' + str(now.month) + '/' + str(now.day) )

@app.route('/get_time', methods=['GET'])
def get_time():
    now = datetime.now()
    return( str(now.hour) + ":" + str(now.minute) + ":" + str(now.second) )

def get_datetime():
    now = datetime.now()
    return( str(now.year) + '/' + str(now.month) + '/' + str(now.day) + '-' + str(now.hour) + ':' + str(now.minute) + ':' + str(now.second) )

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(401)
def access_denid(error):
    return render_template('401.html'), 401

if __name__ == "__main__":
    cur.execute('CREATE TABLE IF NOT EXISTS users (username TEXT NOT NULL, password TEXT NOT NULL, token TEXT NOT NULL, email TEXT NOT NULL);')
    cur.execute('CREATE TABLE IF NOT EXISTS logs (username TEXT NOT NULL, work TEXT NOT NULL, date TEXT NOT NULL, time TEXT NOT NULL, status TEXT NOT NULL)')
    cur.execute('CREATE TABLE IF NOT EXISTS created_files_status (count INT);')
    cur.execute('CREATE TABLE IF NOT EXISTS updated_files_status (count INT);')
    cur.execute('CREATE TABLE IF NOT EXISTS actived_users_status (count INT);')
    cur.execute('CREATE TABLE IF NOT EXISTS deleted_users_status (count INT);')

    cur.execute('SELECT count FROM created_files_status;')
    cur.execute('SELECT count FROM updated_files_status;')
    cur.execute('SELECT count FROM actived_users_status;')
    cur.execute('SELECT count FROM deleted_users_status;')
    resault = cur.fetchmany(4)
    if resault == []:
        cur.execute('INSERT INTO created_files_status (count) VALUES (0);')
        cur.execute('INSERT INTO updated_files_status (count) VALUES (0);')
        cur.execute('INSERT INTO actived_users_status (count) VALUES (0);')
        cur.execute('INSERT INTO deleted_users_status (count) VALUES (0);')
        conn.commit()
    app.run('0.0.0.0', 5000, debug=True)
    conn.commit()
    conn.close()

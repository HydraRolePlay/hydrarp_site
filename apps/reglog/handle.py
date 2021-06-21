from flask import Blueprint, request, render_template
from flask_login import current_user
from data import db_session
from data.users import User
from data.confirmed import C_User
from flask_login import login_user
from settings import DEFAULT_MAIL_SENDER, DEFAULT_MAIL_PASSWORD
from apps.mailer.mailer import send_email
from functions import set_urls, get_themes, push_new_theme, get_last_messages, push_new_message, delete_message, delete_subtheme, close_theme, upload_image, push_new_subtheme, close_subtheme, get_themes_search, get_usr_image
from flask import render_template, redirect, url_for, request
import requests
import json


SECRET_SERVER_KEY = '6LefcOwZAAAAAFOqBF50HPSHpQCY1b8Ce2vGg4l7'

def check_captca(token, ip):
    r = requests.post('https://www.google.com/recaptcha/api/siteverify',
                      {"secret": SECRET_SERVER_KEY, "response": token, "remoteip": ip},
                      headers={'User-Agent': 'DebuguearApi-Browser', "Content-Type": "application/x-www-form-urlencoded"})
    if r.status_code != 200:
        print(r.status_code)
        return False
    else:
        answer = r.json()
        print(answer)
        if 'success' in answer.keys() and answer['success']:
            return True
    return False

reglog = Blueprint('reglog', __name__, template_folder='reglog_temps')


@reglog.route('/handlelogin', methods=['POST'])
def handle_login():
    # log in
    usr_ip = request.remote_addr
    response = {}
    if 'login' in request.form and 'password' in request.form and request.form['login'] and request.form['password'] and request.form.get('secret'):
        if not check_captca(request.form.get('secret'), usr_ip):
            return '', 418  # fix
        session = db_session.create_session()
        user = session.query(User).filter(User.email == request.form['login']).first()
        if not user:
            user = session.query(User).filter(User.login == request.form['login']).first()
        # if isset and correct
        if user and user.check_password(request.form['password']):
            # if confirmed
            cuser = session.query(C_User).filter(C_User.login == user.login).first()
            if not cuser or cuser.is_confirmed():
                if request.form.get('remember'):
                    login_user(user, remember=True)
                else:
                    login_user(user)
                response['state'] = 'success'
                response['msg'] = ''
            else:
                response['state'] = 'error'
                response['msg'] = 'Подтвердите почту'
            session.close()
            return json.dumps(response)
        response['state'] = 'error'
        response['msg'] = 'Неправильные E-mail / Логин или пароль'
        session.close()
        return json.dumps(response)
    return '', 418 # fix


@reglog.route('/handlesignin', methods=['POST'])
def handle_signin():
    usr_ip = request.remote_addr
    response = {}
    # if not emty
    if ('login' in request.form and 
        'email' in request.form and 
        'password1' in request.form and 
        'password2' in request.form and
        request.form['login'] and
        request.form['email'] and
        request.form['password1'] and
        request.form['password2'] and request.form.get('secret')):
        if not check_captca(request.form.get('secret'), usr_ip):
            return '', 418  # fix
        # if isset user with login / email
        session = db_session.create_session()
        e = session.query(User).filter(User.email == request.form['email']).first()
        if not e:
            if 'admin' in request.form['login'].lower():
                response['state'] = 'error'
                response['msg'] = 'Нельзя использовать такой логин'
                session.close()
                return json.dumps(response)
            l = session.query(User).filter(User.login == request.form['login']).first()
            if not l:
                if len(request.form['password1']) >= 8 and len(request.form['password1']) < 128:
                    # if pass1 == pass2
                    if request.form['password1'] == request.form['password2']:
                        # send email
                        cuser = C_User(login=request.form['login'])
                        cuser.generate_verification()
                        send_email(receive=request.form['email'],
                                    subject='Подтверждение почты',
                                    text='Ваш код:\n'+cuser.verify_code,
                                    html=render_template('inlineemail.html', code=cuser.verify_code),
                                    sender=DEFAULT_MAIL_SENDER,
                                    password=DEFAULT_MAIL_PASSWORD)
                        # commit
                        user = User(
                            login=request.form['login'],
                            email=request.form['email'],
                        )
                        user.set_password(request.form['password1'])
                        session.add(user)
                        session.add(cuser)
                        session.commit()
                        response['state'] = 'confirm'
                        response['msg'] = 'Осталось лишь подтвердить Вашу почту'
                        session.close()
                        return json.dumps(response)
                    response['state'] = 'error'
                    response['msg'] = 'Пароли не совпадают'
                    session.close()
                    return json.dumps(response)
                response['state'] = 'error'
                response['msg'] = 'Пароль должен быть длиннее 8 символов'
                session.close()
                return json.dumps(response) 
            response['state'] = 'error'
            response['msg'] = 'Пользователь с таким логином уже зарегистрирован'
            session.close()
            return json.dumps(response)   
        response['state'] = 'error'
        response['msg'] = 'Пользователь с такой почтой уже зарегистрирован'
        session.close()
        return json.dumps(response)
    return '', 418 # fix

# confirm
@reglog.route('/handleconfirm', methods=['POST'])
def handle_confirm():
    response = {}
    if ('login' in request.form and 
    'code' in request.form and 
    request.form['code'] and 
    request.form['login']):
        session = db_session.create_session() 
        cuser = session.query(C_User).filter(C_User.login == request.form['login']).first()
        if cuser:
            if cuser.verify_code == request.form['code']:
                cuser.confirm()
                session.commit()
                response['state'] = 'success'
                response['msg'] = 'OK'
                user = session.query(User).filter(User.login == cuser.login).first()
                login_user(user)
                session.close()
                return json.dumps(response)
        session.close()
        return '', 418 # fix
    return '', 418 # fix

# remove 
@reglog.route('/handleremove', methods=['POST'])
def handle_remove():
    response = {}
    if 'login' in request.form and request.form['login']:
        session = db_session.create_session()
        user = session.query(User).filter(User.login == request.form['login']).first()
        cuser = session.query(C_User).filter(C_User.login == request.form['login']).first()
        if user and cuser:
            if not cuser.is_confirmed():
                session.delete(user)
                session.delete(cuser)
                session.commit()
            response['state'] = 'success'
            response['msg'] = ''
            session.close()
            return json.dumps(response)
        response['state'] = 'error'
        response['msg'] = 'Не существет такого пользователя'
        session.close()
        return json.dumps(response)
    return '', 418 # fix


@reglog.route('/create_theme', methods=['POST'])
def handle_forum_create_theme():
    usr_ip = request.remote_addr
    response = {}
    if request.form.get('name-of-theme') and request.form.get('keywords-of-theme') and request.form.get('link-of-theme') and request.form.get('secret') and request.form.get('link') and current_user.is_authenticated:
        if not check_captca(request.form.get('secret'), usr_ip):
            return '', 418  # fix
        push_new_theme(request.form.get('name-of-theme'), request.form.get('link-of-theme'), request.form.get('keywords-of-theme'), request.form.get('link'))
        return json.dumps(response)
    return '', 418 # fix


@reglog.route('/sendforummessage', methods=['POST'])
def handle_forum_create_sub_theme():
    usr_ip = request.remote_addr
    response = {}
    if request.form.get('name-of-theme') and request.form.get('keywords-of-theme') and request.form.get('text-of-theme') and request.form.get('secret') and request.form.get('link') and current_user.is_authenticated:
        if not check_captca(request.form.get('secret'), usr_ip):
            return '', 418  # fix
        push_new_subtheme(request.form.get('name-of-theme'), request.form.get('keywords-of-theme'), request.form.get('text-of-theme'), request.form.get('link'))
        return json.dumps(response)
    return '', 418 # fix


@reglog.route('/check_forum_message', methods=['POST'])
def handle_forum_check_message():
    response = {"messages": []}
    if request.form.get('last-message') and request.form.get('link') and current_user.is_authenticated:
        response["messages"] = get_last_messages(request.form.get('link'), request.form.get('last-message'))
    return json.dumps(response)


@reglog.route('/send_forum_new_message', methods=['POST'])
def handle_forum_send_message():
    usr_ip = request.remote_addr
    response = {}
    if request.form.get('text-of-theme') and request.form.get('link') and request.form.get('secret') and request.form.get('useranswer') and current_user.is_authenticated:
        if not check_captca(request.form.get('secret'), usr_ip):
            return json.dumps(response)
        push_new_message(request.form.get('text-of-theme'), request.form.get('link'), request.form.get('useranswer').split('user-name-')[1])  # third parametr - answer message
    return json.dumps(response)


@reglog.route('/delete_forum_message', methods=['POST'])
def handle_delete_forum_message():
    usr_ip = request.remote_addr
    response = {}
    if request.form.get('login') and request.form.get('link') and request.form.get('secret') and request.form.get('time') and current_user.is_authenticated:
        if not check_captca(request.form.get('secret'), usr_ip):
            return json.dumps(response)
        delete_message(request.form.get('login'), request.form.get('time'), request.form.get('link'))
    return json.dumps(response)


@reglog.route('/close_forum_theme', methods=['POST'])
def handle_close_forum_theme():
    usr_ip = request.remote_addr
    response = {}
    if request.form.get('link') and request.form.get('secret') and current_user.is_authenticated:
        if not check_captca(request.form.get('secret'), usr_ip):
            return json.dumps(response)
        close_theme(request.form.get('link'))
    return json.dumps(response)


@reglog.route('/close_forum_subtheme', methods=['POST'])
def handle_close_forum_subtheme():
    usr_ip = request.remote_addr
    response = {}
    if request.form.get('link') and request.form.get('secret') and current_user.is_authenticated:
        if not check_captca(request.form.get('secret'), usr_ip):
            return json.dumps(response)
        close_subtheme(request.form.get('link'))
    return json.dumps(response)


@reglog.route('/delete_forum_subtheme', methods=['POST'])
def handle_delete_forum_subtheme():
    usr_ip = request.remote_addr
    response = {}
    if request.form.get('link') and request.form.get('secret') and current_user.is_authenticated:
        if not check_captca(request.form.get('secret'), usr_ip):
            return json.dumps(response)
        delete_subtheme(request.form.get('link'))
    return json.dumps(response)
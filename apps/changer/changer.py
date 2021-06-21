from flask import Blueprint, request, render_template
from data import db_session
from data.users import User
from data.confirmed import C_User
from apps.mailer.mailer import send_email
from functions import set_urls
from settings import DEFAULT_MAIL_SENDER, DEFAULT_MAIL_PASSWORD
import json


changer = Blueprint('changer', __name__, template_folder='changer_temps')


@changer.route('/changepassword', methods=['GET'])
def change_password():
    params = {}
    set_urls(params)
    return render_template('changer.html', **params)


@changer.route('/handlechangepassword', methods=['POST'])
def handle_change_password():
    response = {}
    if ('login' in request.form and
        not 'code' in request.form and
        not 'password1' in request.form and
        not 'password2' in request.form and
        request.form['login']):
        session = db_session.create_session()
        user = session.query(User).filter(User.email == request.form['login']).first()
        if not user:
            user = session.query(User).filter(User.login == request.form['login']).first()
        if user:
            cuser = session.query(C_User).filter(C_User.login == user.login).first()
            if not cuser:
                cuser = C_User(login=user.login)
                cuser.confirm()
                session.add(cuser)
            cuser.generate_changer()
            session.commit()
            send_email(receive=user.email,
                        subject='Изменение пароля',
                        text='Ваш код:\n'+cuser.changer,
                        html=render_template('inlineemail.html', code=cuser.changer),
                        sender=DEFAULT_MAIL_SENDER,
                        password=DEFAULT_MAIL_PASSWORD)
            session.close()
            response['state'] = 'checking'
            response['msg'] = ''
            return json.dumps(response)
        session.close()
        response['state'] = 'error'
        response['msg'] = 'Такого пользователя не существует'
        return json.dumps(response)

    if ('login' in request.form and
        'code' in request.form and
        not 'password1' in request.form and
        not 'password2' in request.form and
        request.form['login'] and
        request.form['code']):
        session = db_session.create_session()
        user = session.query(User).filter(User.email == request.form['login']).first()
        if not user:
            user = session.query(User).filter(User.login == request.form['login']).first()
        cuser = session.query(C_User).filter(C_User.login == user.login).first()
        if not cuser:
            return '', 418 # fix
        if cuser.changer == request.form['code']:
            response['state'] = 'changing'
            response['msg'] = ''
            session.close()
            return json.dumps(response)
        response['state'] = 'error'
        response['msg'] = 'Неправильный код'
        session.close()
        return json.dumps(response)

    if ('password1' in request.form and
        'password2' in request.form and
        'login' in request.form and
        'code' in request.form and
        request.form['password1'] and
        request.form['password2'] and
        request.form['login'] and
        request.form['code']):
        response = {}
        session = db_session.create_session()
        user = session.query(User).filter(User.email == request.form['login']).first()
        if not user:
            user = session.query(User).filter(User.login == request.form['login']).first()
        if user:
            cuser = session.query(C_User).filter(C_User.login == user.login).first()
            if cuser and cuser.changer == request.form['code']:
                # eq
                if len(request.form['password1']) >= 8 and len(request.form['password1']) < 128:
                    if request.form['password1'] == request.form['password2']:
                        # simple # fix
                        user.set_password(request.form['password1'])
                        session.commit()
                        response['state'] = 'success'
                        response['msg'] = 'Вы успешно изменили пароль'
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
        session.close()
    return '', 418 # fix
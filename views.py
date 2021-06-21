import flask
from flask_socketio import SocketIO, emit
from flask import render_template, redirect, url_for, request, jsonify, make_response
from flask import send_file
from flask_login import current_user, logout_user, login_user
from data import db_session
from data.users import User
from data.players import Player
from init import app, login_manager
from functions import set_urls, get_news, get_themes, get_themes_search, get_themes_chat, get_forum_data, get_usr_image, upload_image, get_another_usr_image, get_usr_data, update_last_online_time, get_vk_music
from settings import GAMEPLAYSERVER_IP
from urllib.parse import urlparse, urlunparse
from datetime import datetime
import requests
import os.path
import os
import json
import time
socket = SocketIO(app)

@app.before_request
def before_request():
    urlparts = urlparse(request.url)
    if urlparts.netloc == 'forum.hydrarp.ru':
        parsed = urlparts
        parsed = parsed._replace(netloc='hydrarp.ru')
        parsed = parsed._replace(path=urlparts.path.replace("/", "/forum/"))
        return redirect(parsed.geturl(), code=301)
    if request.url.startswith('http://') and '/set_num_players' not in request.url and '/music' not in request.url:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


@app.route('/ar', methods=['GET'])
def ar_index():
    params = {}
    set_urls(params)
    get_usr_image(params)
    params['main_header'] = "Hydra RolePlay | Главная страница"
    params['main_desc'] = "Заходи на Hydra RP сервер. Лучший в своем роде РП проект голосовым чатом, уникальными системами и множеством игроков онлайн!"
    return render_template('ar_index.html', **params)


@app.route('/', methods=['GET'])
def index():
    params = {}
    set_urls(params)
    get_usr_image(params)
    params['main_header'] = "Hydra RolePlay | Главная страница"
    params['main_desc'] = "Заходи на Hydra RP сервер. Лучший в своем роде РП проект голосовым чатом, уникальными системами и множеством игроков онлайн!"
    return render_template('index.html', **params)


@app.route('/forum/search_page', methods=['GET'])
def forum_search_theme():
    params = {}
    if current_user.is_authenticated and not request.args.get('search', None) is None:
        set_urls(params)
        get_usr_image(params)
        a = get_themes_search(params, request.args.get('search', None))
        if not a:
            return redirect('/forum', 302)
        params['main_header'] = "Hydra RolePlay | " + request.args.get('search', None)
        params['main_desc'] = request.args.get('search', None)
        return render_template('forum-search-list.html', **params)
    else:
        return redirect('/forum', 302)


@app.route('/forum/<theme_link>/new', methods=['GET'])
@app.route('/forum/<theme_link>/new/', methods=['GET'])
def forum_create_theme(theme_link):
    if current_user.is_authenticated and current_user.admin:
        params = {}
        get_usr_image(params)
        set_urls(params)
        a = get_themes(params, theme_link)
        if not a:
            return redirect('/forum', 302)
        params['main_header'] = "Hydra RolePlay | Создание нового раздела на форуме"
        params['main_desc'] = "Создание нового раздела на форуме"
        return render_template('forum-create.html', **params)
    else:
        return redirect('/forum', 302)


@app.route('/forum/<theme_link>/<subtheme_link>/new', methods=['GET'])
@app.route('/forum/<theme_link>/<subtheme_link>/new/', methods=['GET'])
def forum_create_subtheme(theme_link, subtheme_link):
    if current_user.is_authenticated:
        params = {}
        get_usr_image(params)
        set_urls(params)
        a = get_themes(params, theme_link, subtheme_link)
        if not a:
            return redirect('/forum', 302)
        if int(params['forum']['blocked']) and not int(current_user.admin):
            return redirect('/forum', 302)
        params['main_header'] = "Hydra RolePlay | Создание новой темы на форуме"
        params['main_desc'] = "Создание новой темы на форуме"
        return render_template('forum-create-subtheme.html', **params)
    else:
        return redirect('/forum', 302)


@app.route('/forum/<theme_link>/<subtheme_link>', methods=['GET'])
@app.route('/forum/<theme_link>/<subtheme_link>/', methods=['GET'])
def forum_subthemes(theme_link, subtheme_link):
    params = {}
    set_urls(params)
    get_usr_image(params)
    a = get_themes(params, theme_link, subtheme_link)
    if not a:
        return redirect('/forum', 302)
    params['main_header'] = "Hydra RolePlay | " + params['forum']['theme']
    params['main_desc'] = params['forum']['theme']
    return render_template('forum-subtheme.html', **params)


@app.route('/forum/<theme_link>/<subtheme_link>/<thread_id>', methods=['GET'])
@app.route('/forum/<theme_link>/<subtheme_link>/<thread_id>/', methods=['GET'])
def forum_chat(theme_link, subtheme_link, thread_id):
    params = {}
    set_urls(params)
    get_usr_image(params)
    a = get_themes_chat(params, theme_link, subtheme_link, thread_id)
    if not a:
        return redirect('/forum', 302)
    params['main_header'] = "Hydra RolePlay | " + params['forum']['thread_title']
    params['main_desc'] = params['forum']['thread_title']
    return render_template('forum-messages.html', **params)

@app.route('/forum/<theme_link>', methods=['GET'])
@app.route('/forum/<theme_link>/', methods=['GET'])
def forum_themes(theme_link):
    params = {}
    set_urls(params)
    get_usr_image(params)
    a = get_themes(params, theme_link)
    if not a:
        return redirect('/forum', 302)
    params['main_header'] = "Hydra RolePlay | " + params['forum']['theme']
    params['main_desc'] = params['forum']['theme']
    return render_template('forum-theme.html', **params)

@app.route('/forum/', methods=['GET'])
@app.route('/forum', methods=['GET'])
def forum_index():
    params = {}
    set_urls(params)
    get_news(params)
    get_usr_image(params)
    get_forum_data(params)
    params['main_header'] = "Hydra RolePlay | Главная страница форума"
    params['main_desc'] = 'Добро пожаловать на форум проекта Hydra RolePlay! Присоединяйся!'
    return render_template('forum-index.html', **params)

@app.route('/news/<news_id>', methods=['GET'])
@app.route('/news/<news_id>/', methods=['GET'])
def news_info(news_id):
    params = {}
    set_urls(params)
    get_usr_image(params)
    get_news(params, news_id)
    if not params['news'] or type(params['news']) == dict:
        return redirect('/', 302)
    params['main_header'] = "Hydra RolePlay | " + params['news'][0]['title'] + " - Новости"
    params['main_desc'] = params['news'][0]['text']
    return render_template('forum-news-item.html', **params)

@app.route('/news/', methods=['GET'])
@app.route('/news', methods=['GET'])
def news_index():
    params = {}
    set_urls(params)
    get_news(params)
    get_usr_image(params)
    params['main_header'] = "Hydra RolePlay | Новости"
    params['main_desc'] = 'Добро пожаловать на сайт проекта Hydra RolePlay! Последние новости'
    return render_template('forum-news.html', **params)

@app.route('/profile/', methods=['GET'])
@app.route('/profile', methods=['GET'])
def profile():
    if current_user.is_authenticated:
        params = {}
        set_urls(params)
        session = db_session.create_session()
        players = session.query(Player).filter(Player.login == current_user.login).all()
        get_usr_image(params)
        params['players'] = players
        session.close()
        params['main_header'] = "Hydra RolePlay | " + current_user.login + " - профиль"
        params['main_desc'] = "Профиль"
        return render_template('profile.html', **params)
    else:
        return redirect('/', 302)


@app.route('/members/<member_login>', methods=['GET'])
@app.route('/members/<member_login>/', methods=['GET'])
def member_profile(member_login):
    params = {}
    set_urls(params)
    if current_user.is_authenticated:
        get_usr_image(params)
    a = get_usr_data(params, member_login)
    if not a:
        return redirect('/', 302)
    params['user']['login'] = member_login
    params['main_header'] = "Hydra RolePlay | " + member_login
    params['main_desc'] = "Профиль пользователя " + member_login
    return render_template('forum-user.html', **params)


@app.route('/doc/<file_name>', methods=['GET'])
def doc_downloader(file_name):
    if os.path.exists('doc/' + file_name):
        return send_file('doc/' + file_name, mimetype='application/pdf')
    return redirect('/')


@app.route('/get_vk_new_link', methods=['POST'])
def music_vk_link_answer():
    if request.form.get('link'):
        download = requests.get(request.form.get('link'))
        print(download.status_code)
        music_time = str(time.time())
        with open('music/' + music_time + '.mp3', 'wb') as f:
            f.write(download.content)
        return json.dumps({'link': 'https://hydrarp.ru/vk-music/' + music_time + '.mp3'})
    return redirect('/')


@app.route('/delete_track', methods=['POST'])
def music_vk_link_delete():
    if request.form.get('link'):
        os.remove('/home/todolist/music/' + request.form.get('link').split('/')[-1])
    return redirect('/')


@app.route('/vk-music/<file_name>', methods=['GET'])
def music_vk_downloader(file_name):
    if os.path.exists('music/' + file_name):
        return send_file('music/' + file_name, mimetype='application/mpeg', as_attachment=True)
    return redirect('/')


@app.route('/music/<file_name>', methods=['GET'])
def music_downloader(file_name):
    if os.path.exists('music/' + file_name):
        return send_file('music/' + file_name, mimetype='application/mpeg', as_attachment=True)
    return redirect('/')

# Backend here
@app.route('/delete_pers', methods=['POST'])
def delete_pers():
    response = {}
    if ('nickname' in request.form and
        request.form['nickname'] and
        current_user.is_authenticated):
        session = db_session.create_session()
        player = session.query(Player).filter(Player.nickname == request.form['nickname']).first()
        if player.login == current_user.login:
            session.delete(player)
            session.commit()
            response['state'] = 'success'
            response['msg'] = 'Персонаж был успешно удален'
            session.close()
            return json.dumps(response)
        response['state'] = 'error'
        response['msg'] = 'errno 2'
        session.close()
        return json.dumps(response)
    response['state'] = 'error'
    response['msg'] = 'errno 1'
    return json.dumps(response)


@app.route('/getplayerimage', methods=['POST'])
def get_usr_img():
    params = {}
    if request.form.get('login'):
        get_another_usr_image(params, request.form.get('login'))
        return json.dumps(params)
    return redirect('/', 302)


@app.route('/music/get/server', methods=['POST', "OPTIONS"])
def get_music_vk():
    if request.method == "OPTIONS":
        return _build_cors_prelight_response()
    elif request.method == "POST":
        params = {}
        if request.form.get('id') and request.form.get('call'):
            if request.form.get('text'):
                get_vk_music(params, request.form.get('id'), request.form.get('call'), request.form.get('text'))
            else:
                get_vk_music(params, request.form.get('id'), request.form.get('call'))
            return json.dumps(params)
        return redirect('/', 302)


def _build_cors_prelight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add('Access-Control-Allow-Headers', "*")
    response.headers.add('Access-Control-Allow-Methods', "*")
    return response

@app.after_request
def after_request_func(response):
    origin = request.headers.get('Origin')
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', '"')
        response.headers.add('Access-Control-Allow-Methods',
                            'GET, POST, OPTIONS, PUT, PATCH, DELETE')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', '*')
    else:
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        if origin:
            response.headers.add('Access-Control-Allow-Origin', '*')

    return response


@app.route('/set_user_info', methods=['POST'])
def online_or_offline():
    if request.form.get('active'):
        data = int(request.form.get('active'))
        update_last_online_time(data, datetime.today().strftime('%d.%m.%Y - %H:%M'))
        return '', 302
    else:
        return '', 418


@app.errorhandler(404)
def not_found_error(error):
    return redirect('/', 302)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    ret = session.query(User).get(user_id)
    session.close()
    return ret


@app.route("/logout")
def logout():
    if current_user.is_authenticated:
         logout_user()
    else:
         pass
    return redirect('/')


@app.route('/uploadAva', methods=['POST'])
def handle_upload_img():
    response = {}
    if request.files.get('file') and current_user.is_authenticated:
        isthisFile = request.files.get('file')
        now_time = str(time.time())
        if isthisFile.filename.split('.')[-1] not in ['gif', 'png', 'jpg', 'svg', 'jpeg', 'jpe', 'bmp', 'ico', 'webp']:
            return
        upload_image(now_time + '.' + isthisFile.filename.split('.')[-1])
        isthisFile.save("/home/todolist/static/img/" + now_time + '.' + isthisFile.filename.split('.')[-1])
    return json.dumps(response)
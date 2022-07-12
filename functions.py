from flask import url_for
from data.users import User
from flask_login import current_user
from datetime import datetime
from data import db_session
import requests, hashlib, urllib, random, string, re, json, sys, time
import sqlite3
import json
import os


class VkAndroidApi(object):
    session = requests.Session()
    session.headers = {"User-Agent": "VKAndroidApp/4.13.1-1206 (Android 4.4.3; SDK 19; armeabi; ; ru)",
                       "Accept": "image/gif, image/x-xbitmap, image/jpeg, image/pjpeg, */*"}
    # proxies = {'https': 'https://95.105.102.124:8080'}
    # session.proxies.update(proxies)
    def __init__(self, login=None, password=None, token=None, secret=None, v=5.95):
        self.v = v
        self.device_id = "".join(random.choice(string.ascii_lowercase + string.digits) for i in range(16))

        if token is not None and secret is not None:
            self.token = token
            self.secret = secret
            return
        # Генерируем рандомный device_id
        answer = self.session.get(
            "https://oauth.vk.com/token?grant_type=password&scope=nohttps,audio&client_id=2274003&client_secret=hHbZxrka2uZ6jB1inYsH&username={login}&password={password}".format(
                login=login,
                password=password
            ),
            headers={'User-Agent': 'Mozilla/4.0 (compatible; ICS)'}).json()
        print(answer)
        if "error" in answer: raise PermissionError("invalid login|password!")
        self.secret = answer["secret"]
        self.token = answer["access_token"]
        # Методы, "Открывающие" доступ к аудио. Без них, аудио получить не получится
        self.method('execute.getUserInfo', func_v=9),
        self._send('/method/auth.refreshToken?access_token={token}&v={v}&device_id={device_id}&lang=ru'.format(
            token=self.token, v=v, device_id=self.device_id))

    def method(self, method, **params):
        url = ("/method/{method}?v={v}&access_token={token}&device_id={device_id}".format(method=method, v=self.v,
                                                                                          token=self.token,
                                                                                          device_id=self.device_id)
               + "".join("&%s=%s" % (i, params[i]) for i in params if params[i] is not None)
               )  # генерация ссылки по которой будет генерироваться md5-подпись
        # обратите внимание - в даннаой ссылке нет urlencode параметров
        return self._send(url, params, method)

    def _send(self, url, params=None, method=None, headers=None):
        hash = hashlib.md5((url + self.secret).encode()).hexdigest()
        if method is not None and params is not None:
            url = ("/method/{method}?v={v}&access_token={token}&device_id={device_id}".format(method=method,
                                                                                              token=self.token,
                                                                                              device_id=self.device_id,
                                                                                              v=self.v)
                   + "".join(
                        "&" + i + "=" + urllib.parse.quote_plus(str(params[i])) for i in params if
                        (params[i] is not None)
                    ))
        if headers is None:
            return self.session.get('https://api.vk.com' + url + "&sig=" + hash).json()
        else:
            return self.session.get('https://api.vk.com' + url + "&sig=" + hash, headers=headers).json()

    _pattern = re.compile(r'/[a-zA-Z\d]{6,}(/.*?[a-zA-Z\d]+?)/index.m3u8()')

    def get_albums(self, owner_id=None):
        if owner_id is None:
            return
        answer = self.method("audio.getPlaylists", owner_id=owner_id)['response']['items']
        new_answer = []
        for i in answer:
            if 'photo' in i.keys():
                img = i['photo'][list(i['photo'].keys())[len(i['photo'].keys()) - 1]]
            else:
                if 'thumbs' in i.keys():
                    img = i['thumbs'][0][list(i['thumbs'][0].keys())[len(i['thumbs'][0]) - 1]]
                else:
                    img = 'first.png'
            try:
                new_answer.append({'title': i['title'], 'img': img, 'owner_id': i['original']['owner_id'], 'id': i['original']['playlist_id'], "access_hash": i['original']['access_key']})
            except:
                pass
        return new_answer

    def search(self, q=None, count=100):
        if q is None or len(q) < 2:
            return []
        answer = self.method("audio.search", q=q, count=count)['response']['items']
        newAnswer = []
        for i in answer:
            newAnswer.append(
                {'artist': i['artist'], 'title': i['title'], 'duration': i['duration'], 'url': self.to_mp3(i['url'])})
        return newAnswer

    def get(self, owner_id=None, album_id=None, access_hash=None):
        if owner_id is None:
            return
        if album_id is None:
            answer = self.method("audio.get", owner_id=owner_id)
        else:
            answer = self.method("audio.get", owner_id=owner_id, album_id=album_id, access_key=access_hash)
        answer = answer['response']['items']
        newAnswer = []
        for i in answer:
            newAnswer.append({'artist': i['artist'], 'title': i['title'], 'duration': i['duration'], 'url': self.to_mp3(i['url'])})
        return newAnswer

    def to_mp3(self, url):
        return self._pattern.sub(r'\1\2.mp3', url)


login = '-'
password = '-'
vk = VkAndroidApi(login=login, password=password)
secret, token = vk.secret, vk.token


with open('news-data.json', 'r') as file:
    news_data = json.loads(file.read())


def set_urls(params):
    # setup urls
    params['css'] = url_for('static', filename='css/')
    params['js'] = url_for('static', filename='js/')
    params['img'] = url_for('static', filename='img/')


def get_news(params, another=-1):
    if another == -1:
        params['news'] = news_data.copy()
    else:
        if another in news_data.keys():
            params['news'] = news_data[another].copy()
        else:
            params['news'] = False


def get_forum_data(params):
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    forum_data = []
    for i in ["Основной раздел", "Игровые моменты", "Обращения к администрации"]:
        result = cur.execute(
            f"""SELECT * FROM main where `parent-header` = '{i}'""").fetchall()
        data = []
        for j in result:
            answer = {'header': j[2], 'link': j[3]}
            if int(j[5]):
                answer['blocked'] = 1
            answer['creator'] = {'link': '/members/Admin', 'login': j[4]}
            themes_length = cur.execute(f"""SELECT sum(`themes-length`) FROM `{j[3]}`""").fetchone()[0]
            try:
                answer['themes_length'] = themes_length if themes_length // 1000 == 0 else str(themes_length // 1000) + ',' + str(themes_length % 1000)[0] + 'К'
            except Exception as e:
                answer['themes_length'] = 0
            messages_length = cur.execute(f"""SELECT sum(`messages-length`) FROM `{j[3]}`""").fetchone()[0]
            try:
                answer['messages_length'] = messages_length if messages_length // 1000 == 0 else str(messages_length // 1000) + ',' + str(messages_length % 1000)[0] + 'К'
            except Exception as e:
                answer['messages_length'] = 0
            try:
                last_msg = max(cur.execute(f"""SELECT `link`, `last-message-creator`, `last-message-date` FROM `{j[3]}` where `link` != '' and `last-message-creator` != '' and `last-message-date` != ''""").fetchall(), key=lambda x: datetime.strptime(x[2], "%d.%m.%Y - %H:%M:%S"))
                answer['lastMessage'] = {"link": 'forum/' + j[3] + '/' + last_msg[0], "user": {"link": '/members/' + last_msg[1], "name": last_msg[1]}, "date": last_msg[2].split(' -')[0]}
            except Exception as e:
                pass
            data.append(answer)
        forum_data.append({"header": i, "data": data})
    con.commit()
    con.close()
    params['forum'] = forum_data


def get_themes(params, theme_link, subtheme_link=False):
    if subtheme_link:
        answer = {}
        con = sqlite3.connect('./forum/forum_data.db')
        cur = con.cursor()
        header = cur.execute(
                f"""SELECT * FROM main where link = '{theme_link}'""").fetchone()
        if header is None or not len(header) or header[0] is None:
            con.commit()
            con.close()
            return False
        second = cur.execute(
            f"""SELECT * FROM `{theme_link}` where link = '{subtheme_link}'""").fetchone()
        if second is None or not len(second) or second[0] is None:
            con.commit()
            con.close()
            return False
        answer['header'] = header[1]
        answer['before_this_header'] = header[2]
        answer['theme'] = second[1]
        answer['link'] = f'{theme_link}/{subtheme_link}'
        answer['before_this'] = theme_link
        answer['blocked'] = second[9]
        answer['data'] = []
        result = cur.execute(
                f"""SELECT * FROM `{theme_link}-{subtheme_link}`""").fetchall()
        for i in result:
            answer['data'].append({'link': i[1], 'header': i[0], "creator": {'login': i[2], 'date': i[3], 'link': '/members/' + i[2]}, "messages_length": i[4], "lastMessage": {'user': {'link': '/members/' + i[5], 'name': i[5]}, 'date': i[6].split(' -')[0]}})
            if int(i[7]):
                answer['data'][-1]['blocked'] = 1
        answer['data'] = sorted(answer['data'], key=lambda x: x['link'])[::-1]
        params['forum'] = answer
        con.commit()
        con.close()
        return True
    else:
        answer = {}
        con = sqlite3.connect('./forum/forum_data.db')
        cur = con.cursor()
        header = cur.execute(
            f"""SELECT * FROM main where link = '{theme_link}'""").fetchone()
        if header is None or not len(header) or header[0] is None:
            con.commit()
            con.close()
            return False
        answer['header'] = header[1]
        answer['theme'] = header[2]
        answer['link'] = theme_link
        answer['blocked'] = header[5]
        answer['data'] = []
        result = cur.execute(
            f"""SELECT * FROM `{theme_link}`""").fetchall()
        for i in result:
            answer['data'].append(
                {'link': i[2], 'header': i[1], "creator": {'login': i[3], 'date': i[4], 'link': '/members/' + i[3]},
                 "themes_length": i[5],
                 "messages_length": i[6],
                 "lastMessage": {'user': {'link': '/members/' + i[7], 'name': i[7]}, 'date': i[8].split(' -')[0]}})
            if int(i[9]):
                answer['data'][-1]['blocked'] = 1
        params['forum'] = answer
        con.commit()
        con.close()
        return True

def push_new_theme(header, link, keywords, theme_link):
    header = header.replace('"', "'")
    date_of_theme_and_message = datetime.today().strftime('%d.%m.%Y - %H:%M:%S')
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    check = cur.execute(
        f"""SELECT * FROM main where link = '{theme_link}'""").fetchone()
    if not len(check) or check[0] is None or not int(current_user.admin):
        con.commit()
        con.close()
        return
    check = cur.execute(
        f"""SELECT * FROM `{theme_link}` where link = '{link}'""").fetchone()
    if not check is None and len(check):
        con.commit()
        con.close()
        return
    check = cur.execute(
        f"""SELECT * FROM `{theme_link}` where header = '{header}'""").fetchone()
    if not check is None and len(check):
        con.commit()
        con.close()
        return
    cur.execute(
        f"""INSERT into `{theme_link}`('header', 'link', 'creator', 'creator-theme-date', 'themes-length', 'messages-length', 'last-message-creator', 'last-message-date', 'blocked', 'keywords') values('{header}', '{link}', '{current_user.login}', '{date_of_theme_and_message.split(' -')[0]}', 0, 0, '', '', 0, '{keywords}')""")
    cur.execute(
        f"""CREATE TABLE IF NOT EXISTS `{theme_link}-{link}` ('header' varchar, 'link' varchar, 'creator' varchar, 'creator-theme-date' varchar, 'messages-length' varchar, 'last-message-creator' varchar, 'last-message-date' varchar, 'blocked' BOOLEAN, 'keywords' varchar);""")
    con.commit()
    con.close()
    return


def push_new_subtheme(header, keywords, first_message, theme_link):
    header = header.replace('"', "'")
    first_message = first_message.replace('"', "'")
    first_message = first_message.replace('`', "'")
    first_message = first_message.replace('<', '')
    first_message = first_message.replace('>', "'")
    first_message = first_message.replace('\r', '')
    first_message = first_message.replace('\\', '')
    date_of_theme_and_message = datetime.today().strftime('%d.%m.%Y - %H:%M:%S')
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    check = cur.execute(
        f"""SELECT * FROM main where link = '{theme_link.split('/')[0]}'""").fetchone()
    if not len(check) or check[0] is None:
        con.commit()
        con.close()
        return
    check = cur.execute(
        f"""SELECT * FROM `{theme_link.split('/')[0]}` where link = '{theme_link.split('/')[1]}'""").fetchone()
    if not len(check) or check[0] is None or (int(check[9]) and not int(current_user.admin)):
        con.commit()
        con.close()
        return
    max_index = 500000
    if int(current_user.admin):
        max_index = 500000*2
    max_id = cur.execute(
        f"""SELECT max(link) FROM `{theme_link.replace('/', '-')}` where cast(link as integer) < {str(max_index)}""").fetchone()
    if not len(max_id) or max_id[0] is None:
        max_id = max_index - 500000
    else:
        max_id = int(max_id[0]) + 1
    cur.execute(
        f"""INSERT into `{theme_link.replace('/', '-')}` values('{header}', '{max_id}', '{current_user.login}', '{date_of_theme_and_message.split(' -')[0]}', 1, '{current_user.login}', '{date_of_theme_and_message}', 0, '{keywords}')""")
    cur.execute(
        f"""CREATE TABLE IF NOT EXISTS `{theme_link.replace('/', '-')}-{str(max_id)}` ('login' varchar, 'date' varchar, 'text' varchar, 'answer' varchar);""")
    cur.execute(
        f"""INSERT into `{theme_link.replace('/', '-')}-{str(max_id)}` values('{current_user.login}', '{date_of_theme_and_message}', "{first_message}", '')""")
    cur.execute(
        f"""UPDATE `{theme_link.split('/')[0]}` set `messages-length` = `messages-length` + 1, `themes-length` = `themes-length` + 1, `last-message-creator` = '{current_user.login}', `last-message-date` = '{date_of_theme_and_message}' where link = '{theme_link.split('/')[1]}' """)
    con.commit()
    con.close()
    return


def get_themes_chat(params, theme_link, subtheme_link, thread_id):
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    first_check = cur.execute(f"""SELECT * FROM main where link = '{theme_link}'""").fetchone()
    if first_check is None or not len(first_check) or first_check[0] is None:
        con.commit()
        con.close()
        return False
    second_check = cur.execute(f"""SELECT * FROM `{theme_link}` where link = '{subtheme_link}'""").fetchone()
    if second_check is None or not len(second_check) or second_check[0] is None:
        con.commit()
        con.close()
        return False
    third_check = cur.execute(f"""SELECT * FROM `{theme_link}-{subtheme_link}` where link = '{thread_id}'""").fetchone()
    if third_check is None or not len(third_check) or third_check[0] is None:
        con.commit()
        con.close()
        return False
    params['forum'] = {}
    params['forum']['subtheme'] = second_check[1]
    params['forum']['subtheme_link'] = subtheme_link
    params['forum']['link'] = theme_link
    if int(third_check[7]):
        params['forum']['blocked'] = 1
    params['forum']['thread_title'] = third_check[0]
    params['forum']['theme'] = first_check[2]
    params['forum']['header'] = first_check[1]
    params['forum']['messages'] = []
    session = db_session.create_session()
    try:
        for i in cur.execute(f"""SELECT * FROM `{theme_link}-{subtheme_link}-{thread_id}`""").fetchall():
            text = i[2].replace('"', "'").split('\n')
            userData = cur.execute(f"""SELECT * FROM `users` where login='{i[0]}'""").fetchone()
            if userData is None or not len(userData) or userData[0] is None:
                image = 'user-ico.svg'
            else:
                image = userData[1]
            params['forum']['messages'].append({"author": {"name": i[0], "admin": session.query(User).filter(User.login == i[0]).first().admin, "image": image}, "time": i[1], "text": f"{''.join([f'<p>`{j}`</p>' for j in text])}", "answer": i[3]})
    except:
        pass
    session.close()
    con.commit()
    con.close()
    return True


def get_last_messages(link, need_time):
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    link = '-'.join(link.split('/'))[:-1]
    data = {"messages": []}
    session = db_session.create_session()
    try:
        for i in cur.execute(f"""SELECT * FROM `{link}`""").fetchall():
            text = i[2].replace('"', "'").split('\n')
            userData = cur.execute(f"""SELECT * FROM `users` where login='{i[0]}'""").fetchone()
            if userData is None or not len(userData) or userData[0] is None:
                image = 'user-ico.svg'
            else:
                image = userData[1]
            data['messages'].append({"author": {"name": i[0], "admin": session.query(User).filter(User.login == i[0]).first().admin, "image": image}, "time": i[1], "text": f"{''.join([f'<p>`{j}`</p>' for j in text])}", "answer": i[3]})
    except:
        pass
    session.close()
    con.commit()
    con.close()
    try:
        return [x for x in data['messages'] if datetime.strptime(x["time"], "%d.%m.%Y - %H:%M:%S") > datetime.strptime(need_time, "%d.%m.%Y - %H:%M:%S")]
    except:
        return []


def get_themes_search(params, search_text):
    search_text = search_text.lower()
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    answer = {}
    answer['header'] = 'Главная страница'
    answer['theme'] = 'Поиск'
    answer['data'] = []
    for i in cur.execute(
            f"""SELECT * FROM main""").fetchall():
        result = cur.execute(
            f"""SELECT * FROM `{i[3]}`""").fetchall()
        for j in result:
            keywords = j[10].lower().replace(' ', ',').split(',')
            if any(map(lambda v: v in search_text.split(), keywords)):
                answer['data'].append({'link': i[3] + '/' + j[2], 'header': j[1], 'blocked': int(j[9]), 'creator': {'login': j[3], 'date': j[4], 'link': '/members/' + j[3]},
                                        "themes_length": j[5],
                                        "messages_length": j[6],
                                        "lastMessage": {'user': {'link': '/members/' + j[7], 'name': j[7]}, 'date': j[8].split(' -')[0]}})
            else:
                new_result = cur.execute(
                    f"""SELECT * FROM `{i[3]}-{j[2]}`""").fetchall()
                for k in new_result:
                    keywords = k[8].lower().replace(' ', ',').split(',')
                    if any(map(lambda v: v in search_text.split(), keywords)):
                        answer['data'].append({'link': i[3] + '/' + j[2] + '/' + k[1], 'header': k[0], 'blocked': int(k[7]),
                                               'creator': {'login': k[2], 'date': k[3], 'link': '/members/' + k[2]},
                                               "messages_length": k[4],
                                               "lastMessage": {'user': {'link': '/members/' + k[5], 'name': k[5]},
                                                               'date': k[6].split(' -')[0]}})
    params['forum'] = answer
    con.commit()
    con.close()
    return True


def push_new_message(text, link, answer):
    text = text.replace('"', "'")
    text = text.replace('"', "'")
    text = text.replace('`', "'")
    text = text.replace('<', '')
    text = text.replace('>', "'")
    text = text.replace('\r', '')
    text = text.replace('\\', '')


    date_of_theme_and_message = datetime.today().strftime('%d.%m.%Y - %H:%M:%S')
    link = link.split('/')
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    check = cur.execute(f"""SELECT * FROM `{link[0]}` where link='{link[1]}'""").fetchone()
    if check is None or not len(check) or check[0] is None or (int(check[9]) and not int(current_user.admin)):
        con.commit()
        con.close()
        return
    try:
        cur.execute(
            f"""INSERT into `{link[0]}-{link[1]}-{link[2]}` values('{current_user.login}', '{date_of_theme_and_message}', "{text}", '{answer}')""")
        cur.execute(
            f"""Update `{link[0]}-{link[1]}` set `messages-length` = `messages-length` + 1, `last-message-creator` = '{current_user.login}', `last-message-date` = '{date_of_theme_and_message}' where link= '{link[2]}'""")
        cur.execute(
            f"""UPDATE `{link[0]}` set `messages-length` = `messages-length` + 1, `last-message-creator` = '{current_user.login}', `last-message-date` = '{date_of_theme_and_message}' where link = '{link[1]}' """)
    except:
        pass
    con.commit()
    con.close()


def delete_message(login, time, link):
    link = link.split('/')
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    try:
        check = cur.execute(f"""SELECT * FROM `{link[0]}-{link[1]}` where link='{link[2]}'""").fetchone()
        if check is None or not len(check) or check[0] is None:
            con.commit()
            con.close()
            return
        if current_user.login != login and not int(current_user.admin):
            con.commit()
            con.close()
            return
        cur.execute(
            f"""DELETE from `{link[0]}-{link[1]}-{link[2]}` where `login` = '{login}' and `date` = '{time}'""")
        cur.execute(
            f"""Update `{link[0]}-{link[1]}` set `messages-length` = `messages-length` - 1 where link= '{link[2]}'""")
        cur.execute(
            f"""UPDATE `{link[0]}` set `messages-length` = `messages-length` - 1 where link = '{link[1]}' """)
    except:
        pass
    con.commit()
    con.close()


def delete_subtheme(link):
    if not int(current_user.admin):
        return
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    try:
        link = link.split('/forum/')[1].split('/')
        check = cur.execute(f"""SELECT * FROM `{link[0]}-{link[1]}` where link='{link[2]}'""").fetchone()
        if check is None or not len(check) or check[0] is None:
            con.commit()
            con.close()
            return
        cur.execute(
            f"""UPDATE `{link[0]}` set `messages-length` = `messages-length` - {check[4]}, `themes-length` = `themes-length` - 1 where link = '{link[1]}' """)
        cur.execute(
            f"""DROP TABLE `{link[0]}-{link[1]}-{link[2]}`""")
        cur.execute(
            f"""DELETE FROM `{link[0]}-{link[1]}` where link='{link[2]}'""")
    except:
        pass
    con.commit()
    con.close()
    return


def close_theme(link):
    if not int(current_user.admin):
        return
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    try:
        link = link.split('/forum/')[1].split('/')
        check = cur.execute(f"""SELECT * FROM `{link[0]}` where link='{link[1]}'""").fetchone()
        if check is None or not len(check) or check[0] is None:
            con.commit()
            con.close()
            return
        cur.execute(
            f"""Update `{link[0]}` set `blocked` = not `blocked` where link= '{link[1]}'""")
    except:
        pass
    con.commit()
    con.close()
    return


def close_subtheme(link):
    if not int(current_user.admin):
        return
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    try:
        link = link.split('/forum/')[1].split('/')
        check = cur.execute(f"""SELECT * FROM `{link[0]}-{link[1]}` where link='{link[2]}'""").fetchone()
        if check is None or not len(check) or check[0] is None:
            con.commit()
            con.close()
            return
        cur.execute(
            f"""Update `{link[0]}-{link[1]}` set `blocked` = not `blocked` where link= '{link[2]}'""")
    except:
        pass
    con.commit()
    con.close()
    return


def get_usr_data(params, login):
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    params['user'] = {}
    params['user']['image'] = 'user-ico.svg'
    try:
        session = db_session.create_session()
        admin_level = session.query(User).filter(User.login == login).first().admin
        date_of_reg = session.query(User).filter(User.login == login).first().date_of_reg
        session.close()
        if not len(date_of_reg):
            con.commit()
            con.close()
            return False
    except:
        return False
    try:
        if login.lower() == 'admin':
            check = cur.execute(f"""SELECT * FROM `users` where login='{login.lower()}'""").fetchone()
        else:
            check = cur.execute(f"""SELECT * FROM `users` where login='{login}'""").fetchone()
        if check is None or not len(check) or check[0] is None:
            pass
        else:
            params['user']['image'] = check[1]
    except:
        pass
    params['user']['date_of_reg'] = date_of_reg
    params['user']['rules'] = ['Игрок', 'Модератор', 'Хелпер', 'Администратор', 'Главный Администратор', 'Создатель'][int(admin_level)]
    answer = {'data': [], 'messages': []}
    another = []
    for i in cur.execute(
            f"""SELECT * FROM main""").fetchall():
        result = cur.execute(
            f"""SELECT * FROM `{i[3]}`""").fetchall()
        for j in result:
            if j[3].lower() == login.lower():
                answer['data'].append({'link': i[3] + '/' + j[2], 'header': j[1], 'blocked': int(j[9]), 'creator': {'login': j[3], 'date': j[4], 'link': '/members/' + j[3]},
                                        "themes_length": j[5],
                                        "messages_length": j[6],
                                        "lastMessage": {'user': {'link': '/members/' + j[7], 'name': j[7]}, 'date': j[8].split(' -')[0]}})
            new_result = cur.execute(
                f"""SELECT * FROM `{i[3]}-{j[2]}`""").fetchall()
            for k in new_result:
                if k[2].lower() == login.lower():
                    another.append({'link': i[3] + '/' + j[2] + '/' + k[1], 'header': k[0], 'blocked': int(k[7]),
                                           'creator': {'login': k[2], 'date': k[3], 'link': '/members/' + k[2]},
                                           "messages_length": k[4],
                                           "lastMessage": {'user': {'link': '/members/' + k[5], 'name': k[5]},
                                                           'date': k[6].split(' -')[0]}})
                new_new_result = cur.execute(
                    f"""SELECT * FROM `{i[3]}-{j[2]}-{k[1]}`""").fetchall()
                for _ in new_new_result:
                    if _[0].lower() == login.lower():
                        answer['messages'].append({'link': i[3] + '/' + j[2] + '/' + k[1], 'text': _[2][:53].replace('\n', ' '), 'date': _[1]})
    answer['data'].extend(another)
    params['user']['forum'] = {}
    params['user']['forum']['data'] = answer['data']
    params['user']['forum']['messages'] = answer['messages']
    params['user']['forum']['messagesLength'] = str(len(answer['messages']))
    params['user']['forum']['dataLength'] = str(len(answer['data']))
    if login.lower() == 'admin':
        check = cur.execute(f"""SELECT * FROM `users_online` where login='{login.lower()}'""").fetchone()
    else:
        check = cur.execute(f"""SELECT * FROM `users_online` where login='{login}'""").fetchone()
    if check is None or not len(check) or check[0] is None:
        params['user']['last_activity'] = 'был(а) в сети давно'
        params['user']['active'] = 'offline'
    else:
        if int(check[1]):
            params['user']['active'] = 'online'
            params['user']['last_activity'] = 'в сети'
        else:
            params['user']['active'] = 'offline'
            params['user']['last_activity'] = 'был(а) в сети ' + check[2]
    con.commit()
    con.close()
    return True


def update_last_online_time(active, date):
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    check = cur.execute(f"""SELECT * FROM `users_online` where login='{current_user.login}'""").fetchone()
    if check is None or not len(check) or check[0] is None:
        cur.execute(
            f"""INSERT into `users_online` values('{current_user.login}', '{active}', '{date}')""")
    else:
        cur.execute(
            f"""UPDATE `users_online` set `usr-active` = '{active}', `usr-date` = '{date}' where login='{current_user.login}'""")
    con.commit()
    con.close()
    return


def upload_image(image):
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    check = cur.execute(f"""SELECT * FROM `users` where login='{current_user.login}'""").fetchone()
    if check is None or not len(check) or check[0] is None:
        cur.execute(
            f"""INSERT into `users` values('{current_user.login}', '{image}')""")
    else:
        os.remove('/home/todolist/static/img/' + check[1])
        cur.execute(
            f"""UPDATE `users` set `usr-image` = '{image}' where login='{current_user.login}'""")
    con.commit()
    con.close()
    return


def get_another_usr_image(params, login):
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    params['image'] = 'user-ico-white.svg'
    try:
        check = cur.execute(f"""SELECT * FROM `users` where login='{login}'""").fetchone()
        if check is None or not len(check) or check[0] is None:
            pass
        else:
            params['image'] = check[1]
    except:
        pass
    con.commit()
    con.close()
    return


def get_vk_music(params, id, call, text=None):
    global vk
    reciever_id = int(id)
    if call == 'playlist':
        params['playlist'] = []
        smth = vk.get_albums(owner_id=reciever_id)[::-1]
        for i in smth:
            try:
                check_songs = vk.get(owner_id=i['owner_id'], album_id=i['id'], access_hash=i['access_hash'])
                if not len(check_songs):
                    continue
                params['playlist'].append({'name': i['title'], 'pic': i['img'], 'genre': '', 'music': []})
                for j in check_songs:
                    duration = int(j['duration']) % 60
                    if len(str(duration)) == 1:
                        duration = '0' + str(duration)
                    minutes = int(j['duration']) // 60
                    end_duration = str(minutes) + ':' + str(duration)
                    params['playlist'][-1]['music'].append({'url': j['url'], 'name': j['title'], 'artist': j['artist'], 'duration': end_duration})
            except Exception as e:
                if len(params['playlist']) and params['playlist'][-1]['name'] == i['title']:
                    params['playlist'].pop()
            time.sleep(0.1)
    elif call == 'localMusic':
        params['localMusic'] = []
        smth = vk.get(owner_id=reciever_id)
        try:
            for i in smth:
                duration = int(i['duration']) % 60
                if len(str(duration)) == 1:
                    duration = '0' + str(duration)
                minutes = int(i['duration']) // 60
                end_duration = str(minutes) + ':' + str(duration)
                params['localMusic'].append(
                    {'url': i['url'], 'name': i['title'], 'artist': i['artist'], 'duration': end_duration})
        except:
            params['localMusic'] = []
    elif call == 'findMusic':
        params['findMusic'] = []
        smth = vk.search(text, count=15)
        try:
            for i in smth:
                duration = int(i['duration']) % 60
                if len(str(duration)) == 1:
                    duration = '0' + str(duration)
                minutes = int(i['duration']) // 60
                end_duration = str(minutes) + ':' + str(duration)
                params['findMusic'].append(
                    {'url': i['url'], 'name': i['title'], 'artist': i['artist'], 'duration': end_duration})
        except:
            params['findMusic'] = []
    return


def get_usr_image(params):
    con = sqlite3.connect('./forum/forum_data.db')
    cur = con.cursor()
    params['image'] = 'user-ico-white.svg'
    try:
        check = cur.execute(f"""SELECT * FROM `users` where login='{current_user.login}'""").fetchone()
        if check is None or not len(check) or check[0] is None:
            pass
        else:
            params['image'] = check[1]
    except:
        pass
    con.commit()
    con.close()
    return

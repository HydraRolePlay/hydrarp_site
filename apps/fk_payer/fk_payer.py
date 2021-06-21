from flask import Blueprint, request, redirect
from flask_login import current_user
from data import db_session
from data.vip import Vip
from data.players import Player
from data.users import User
from settings import FK_ID, FK_MERCHANT_ID, FK_SECRET_1, FK_SECRET_2, VIP_PRICES
from hashlib import md5


payer = Blueprint('payer', __name__, template_folder='fk_payer_temps')


@payer.route('/subscribe/success', methods=['POST'])
def success():
    return redirect('/profile')


@payer.route('/subscribe/fail', methods=['POST'])
def fail():
    return redirect('/profile')


@payer.route('/subscribe/alert', methods=['POST'])
def alert():
    alert_secret = md5(
        (
            request.form.get('MERCHANT_ID') + ':' + 
            request.form.get('AMOUNT') + ':' + FK_SECRET_2 + ':' + 
            request.form.get('MERCHANT_ORDER_ID')
        ).encode()
    ).hexdigest()
    print(alert_secret)

    if (request.form.get('SIGN') != alert_secret):
        return '', 422 # hacking attemp

    # vip
    if (request.form.get('us_nickname') and
            request.form.get('us_vip')):
        nickname = request.form.get('us_nickname')
        vip_index = request.form.get('us_vip')

        session = db_session.create_session()
        vip = session.query(Vip).filter(Vip.nickname == nickname).first()
        if vip:
            vip.add_sub(vip_index)
        else:
            vip = Vip(nickname=nickname, subscribe=vip_index)
            session.add(vip)
        session.commit()
        session.close()
        return 'YES'
    # donate
    elif (request.form.get('us_login')):
        session = db_session.create_session()
        user = session.query(User).filter(User.login == request.form.get('us_login')).first()
        user.balance = str(int(user.balance) + int(request.form.get('AMOUNT')))
        session.commit()
        session.close()
        return 'YES'
    else:
        return ''


@payer.route('/subscribe/pay_vip', methods=['POST'])
def pay_vip():
    if (current_user.is_authenticated and
            request.form.get('us_nickname') and
            request.form.get('us_vip') and
            request.form.get('pay')):
        session = db_session.create_session()
        pers = session.query(Player).filter(Player.nickname == request.form['us_nickname']).first()
        if pers.login != current_user.login:
            # fix
            return redirect('/profile')
        sub_list = ['standart', 'premium', 'VIP', 'VIP_plus']
        if not request.form['us_vip'] in sub_list:
            # fix
            return redirect('/profile')
        else:
            price = VIP_PRICES[sub_list.index(request.form['us_vip'])]
        # creating uri
        data = {}
        data['m'] = FK_MERCHANT_ID
        data['oa'] = price
        data['o'] = current_user.login + ';' + request.form['us_nickname'] + ';' + request.form['us_vip']
        data['s'] = md5((':'.join([data['m'], data['oa'], FK_SECRET_1, data['o']])).encode()).hexdigest()
        data['us_vip'] = request.form['us_vip']
        data['us_nickname'] = request.form['us_nickname']
        get = '&'.join([i + '=' + data[i] for i in data])
        session.close()
        return redirect('https://www.free-kassa.ru/merchant/cash.php?' + get)
    return redirect('/profile')


@payer.route('/subscribe/donate', methods=['POST'])
def donate():
    if (current_user.is_authenticated and
            request.form.get('donate') and
            request.form.get('pay')):
        session = db_session.create_session()
        user = session.query(User).filter(User.login == current_user.login).first()
        if not user:
            # fix
            return redirect('/profile')
        try:
            int(request.form['donate'])
        except:
            # fix
            return redirect('/profile')
        # creating uri
        if int(request.form['donate']) < 1:
            # fix
            return redirect('/profile')
        data = {}
        data['m'] = FK_MERCHANT_ID
        data['oa'] = request.form['donate']
        data['o'] = current_user.login + ';donate;' + request.form['donate']
        data['s'] = md5((':'.join([data['m'], data['oa'], FK_SECRET_1, data['o']])).encode()).hexdigest()
        data['us_login'] = current_user.login
        get = '&'.join([i + '=' + data[i] for i in data])
        session.close()
        return redirect('https://www.free-kassa.ru/merchant/cash.php?' + get)
    return redirect('/profile')


@payer.route('/subscribe/swap', methods=['POST'])
def swap():
    if (current_user.is_authenticated and
            request.form.get('us_nickname') and
            request.form.get('swap') and
            request.form.get('pay')):
        try:
            int(request.form['swap'])
        except:
            return redirect('/profile')
        session = db_session.create_session()
        user = session.query(User).filter(User.login == current_user.login).first()
        pers = session.query(Player).filter(Player.nickname == request.form['us_nickname']).first()
        if (user and pers and
        pers.login == user.login and 
        int(request.form['swap']) > 0 and
        int(user.balance) >= int(request.form['swap'])):
            user.balance = str(int(user.balance) - int(request.form['swap']))
            pers.cash = str(int(pers.cash) + int(request.form['swap']) * 1000)
            session.commit()
            session.close()
    return redirect('/profile')
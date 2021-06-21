from flask import Flask
from flask_login import LoginManager
from apps.reglog.handle import reglog
from apps.changer.changer import changer
from apps.fk_payer.fk_payer import payer
from data import db_session
from settings import SECRET_KEY, STR_CONN_TO_MYSQL


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
login_manager = LoginManager()
login_manager.init_app(app)
app.register_blueprint(reglog)
app.register_blueprint(changer)
app.register_blueprint(payer)
db_session.global_init(STR_CONN_TO_MYSQL)
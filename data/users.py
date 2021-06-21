import sqlalchemy
from sqlalchemy.dialects.mysql import VARCHAR
from flask_login import UserMixin
from datetime import datetime
#from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase
import os


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = "server_players"

    id = sqlalchemy.Column(sqlalchemy.Integer,
                            primary_key=True,
                            autoincrement=True)
    login = sqlalchemy.Column(VARCHAR(128))
    email = sqlalchemy.Column(VARCHAR(128))
    password = sqlalchemy.Column(VARCHAR(128))
    balance = sqlalchemy.Column(VARCHAR(128), default='0')
    admin = sqlalchemy.Column(VARCHAR(128), default='0')
    telegram_id = sqlalchemy.Column(VARCHAR(128), default='')
    checkmail = sqlalchemy.Column(VARCHAR(128), default='')
    date_of_reg = sqlalchemy.Column(VARCHAR(128), default=str(datetime.today().strftime('%d.%m.%Y')))

    def set_password(self, _pass):
        self.password = _pass

    def check_password(self, _pass):
        return self.password == _pass
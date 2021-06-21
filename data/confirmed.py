import sqlalchemy
from datetime import datetime
from random import randint
from sqlalchemy.dialects.mysql import VARCHAR
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class C_User(SqlAlchemyBase, UserMixin):
    __tablename__ = "site_confirmed"

    id = sqlalchemy.Column(sqlalchemy.Integer,
                            primary_key=True,
                            autoincrement=True)
    login = sqlalchemy.Column(VARCHAR(128))
    verify_code = sqlalchemy.Column(VARCHAR(8))
    changer = sqlalchemy.Column(VARCHAR(8), nullable=True)
    confirmed = sqlalchemy.Column(VARCHAR(128), nullable=True)

    
    def is_confirmed(self):
        return self.confirmed != ''

    def confirm(self):
        self.confirmed = str(datetime.now())

    def generate_verification(self):
        self.verify_code = ''.join([str(randint(0, 9)) for i in range(8)])

    def generate_changer(self):
        self.changer = ''.join([str(randint(0, 9)) for i in range(8)])
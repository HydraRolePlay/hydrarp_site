import sqlalchemy
from datetime import datetime, timedelta
from sqlalchemy.dialects.mysql import VARCHAR
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class Vip(SqlAlchemyBase, UserMixin):
    __tablename__ = "players_vip"

    id = sqlalchemy.Column(sqlalchemy.Integer,
                            primary_key=True,
                            autoincrement=True)
    nickname = sqlalchemy.Column(VARCHAR(128))
    subscribe = sqlalchemy.Column(VARCHAR(128))
    enddate = sqlalchemy.Column(VARCHAR(128))


    def __init__(self, nickname, subscribe):
        self.nickname = nickname
        self.subscribe = subscribe
        self.enddate = (datetime.now() + timedelta(days=30)).isoformat()[:10]


    def add_sub(self, subscribe):
        self.subscribe = subscribe
        self.enddate = (datetime.now() + timedelta(days=30)).isoformat()[:10]
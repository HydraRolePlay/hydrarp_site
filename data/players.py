import sqlalchemy
from sqlalchemy.dialects.mysql import VARCHAR
from flask_login import UserMixin
from .db_session import SqlAlchemyBase


class Player(SqlAlchemyBase, UserMixin):
    __tablename__ = "players"

    id = sqlalchemy.Column(sqlalchemy.Integer,
                            primary_key=True,
                            autoincrement=True)
    login = sqlalchemy.Column(VARCHAR(128))
    nickname = sqlalchemy.Column(VARCHAR(128))
    model = sqlalchemy.Column(VARCHAR(128))
    level = sqlalchemy.Column(VARCHAR(128))
    Experience = sqlalchemy.Column(VARCHAR(128))
    faction = sqlalchemy.Column(VARCHAR(128))
    ban = sqlalchemy.Column(VARCHAR(128))
    reason = sqlalchemy.Column(VARCHAR(128))
    dateofban = sqlalchemy.Column(VARCHAR(128))
    cash = sqlalchemy.Column(VARCHAR(128))
    card = sqlalchemy.Column(VARCHAR(128))

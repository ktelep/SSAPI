import os

class Config():
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Scr1mmag32w!n'

    SQLALCHEMY_DATABASE_URI = 'sqlite:////test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_LIFESPAN = {'hours': 24}
    JWT_REFRESH_LIFESPAN = {'days': 30}


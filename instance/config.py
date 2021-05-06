import os
basedir = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = 'secretkeyisverysecret'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'wafmovies.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = False
DEVELOPMENT = True
DEBUG = True

ITEM_PER_PAGE = 20



from flask import Flask, request, jsonify
from SSAPI.config import Config
from flask_restplus import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import flask_praetorian

guard = flask_praetorian.Praetorian()

app = Flask(__name__)                  #  Create a Flask WSGI application
app.config.from_object(Config)         #  Pull in our configuration
api = Api(app)                         #  Create a Flask-RESTPlus API
db = SQLAlchemy(app)                   #  Create our SQLAlchemy DB

from SSAPI.models import *
from SSAPI.usermgmt_views import *
from SSAPI.scrimmage_views import *
from SSAPI.invite_views import *

guard.init_app(app, User)

if __name__ == '__main__':
    app.run(debug=True)                #  Start a development server

from flask import Flask, request, jsonify
from SSAPI.config import Config
from flask_restplus import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from SSAPI.config import app_config
import flask_praetorian
import os
import sqlalchemy


guard = flask_praetorian.Praetorian()
config_name = os.getenv('APP_SETTINGS')

app = Flask(__name__)                  # Create a Flask WSGI application
app.config.from_object(app_config[config_name])    # Pull in our configuration
CORS(app)                              # Allow Cross-Origin
api = Api(app)                         # Create a Flask-RESTPlus API
db = SQLAlchemy(app)                   # Create our SQLAlchemy DB

from SSAPI.models import *
from SSAPI.usermgmt_views import *
from SSAPI.scrimmage_views import *
from SSAPI.invite_views import *

guard.init_app(app, User)


# Setup our error handlers
@api.errorhandler(flask_praetorian.exceptions.MissingTokenHeader)
@api.errorhandler(flask_praetorian.exceptions.AuthenticationError)
def my_handler(error):
    error_response = error.jsonify()
    return flask.json.loads(error_response.get_data()), error_response.status_code

if __name__ == '__main__':
    app.run(debug=True)                # Start a development server
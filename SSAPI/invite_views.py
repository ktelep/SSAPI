from flask import Flask, request, jsonify
from SSAPI.config import Config
from SSAPI import app, api, db, guard
from flask_restplus import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import flask_praetorian
from SSAPI.models import *

@api.route('/Invites')
class InviteList(Resource):
    def get(self):
        """ Returns a list of Scrimmages """
        pass
    def post(self):
        """ Create a new Scrimmage """
        pass

@api.route('/Invites/<int:id>')
class Invites(Resource):
    def get(self,id):
        """ Returns info about a Scrimmage """
        invite = ScrimmageInvite.query.filter_by(id=id).first()
        return jsonify(invite.as_dict())

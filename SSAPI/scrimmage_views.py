from flask import Flask, request, jsonify
from SSAPI import app, api, db, guard
from flask_restplus import Resource, reqparse, inputs
import flask_praetorian
from SSAPI.models import *

@api.route('/Scrimmages')
class ScrimmageList(Resource):
    @flask_praetorian.auth_required
    def get(self):
        """ Returns a list of Scrimmages """
        current_user_id = flask_praetorian.current_user().id
        current_user_roles = flask_praetorian.current_user().roles 

        # Filtering/sorting
        parser = reqparse.RequestParser()
        parser.add_argument('role', type=str, help='Return only Scrimmages of type Role')
        parser.add_argument('all', type=inputs.boolean, help='Returns ALL Scrimmages (admin only)')
        parser.add_argument('completed', type=inputs.boolean, help='Returns completed scrimmages if set to true')
        args = parser.parse_args()

        query = None
        if args["all"]:
            if "admin" in current_user_roles:
                query = Scrimmage.query
            else:
                query = Scrimmage.query.filter(
                     (Scrimmage.advisors.any(User.id == current_user_id))|
                     (Scrimmage.presenters.any(User.id == current_user_id)))
        else:
            query = Scrimmage.query.filter(
                 (Scrimmage.advisors.any(User.id == current_user_id))|
                 (Scrimmage.presenters.any(User.id == current_user_id)))

        if args["role"]:
            if "advisor" in args["role"]:
                query = query.filter(Scrimmage.advisors.any(User.id == current_user_id))

            if "presenter" in args["role"]:
                query = query.filter(Scrimmage.presenters.any(User.id == current_user_id))
       
        if args["completed"] is not None:
            print(args["completed"])
            query = query.filter(Scrimmage.scrimmage_complete == args["completed"])
 
        ret = []
        result = query.all()
        for i in result:
          ret.append(i.as_dict())

        resp = jsonify(ret)
        return resp

    @flask_praetorian.auth_required
    def post(self):
        """ Create a new Scrimmage """
        pass

@api.route('/Scrimmages/<int:id>')
class Scrimmages(Resource):
    @flask_praetorian.auth_required
    def get(self,id):
        """ Returns info about a Scrimmage """
        scrimmage = Scrimmage.query.filter_by(id=id).first()
        return jsonify(scrimmage.as_dict())

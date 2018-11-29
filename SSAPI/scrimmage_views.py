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
        current_id = flask_praetorian.current_user().id
        current_user_roles = flask_praetorian.current_user().roles

        # Filtering/sorting
        parser = reqparse.RequestParser()
        parser.add_argument('role', type=str)  # role (advisor or presenter)
        parser.add_argument('all', type=inputs.boolean)  # all admin only
        parser.add_argument('completed', type=inputs.boolean)  # Completed?
        args = parser.parse_args()

        query = None
        if args["all"]:
            if "admin" in current_user_roles:
                query = Scrimmage.query
            else:
                query = Scrimmage.query.filter(
                    (Scrimmage.advisors.any(User.id == current_id)) |
                    (Scrimmage.presenters.any(User.id == current_id)))
        else:
            query = Scrimmage.query.filter(
                (Scrimmage.advisors.any(User.id == current_id)) |
                (Scrimmage.presenters.any(User.id == current_id)))

        if args["role"]:
            if "advisor" in args["role"]:
                query = query.filter(
                    Scrimmage.advisors.any(User.id == current_id))

            if "presenter" in args["role"]:
                query = query.filter(Scrimmage.presenters.any(
                    User.id == current_id))

        if args["completed"] is not None:
            query = query.filter(
                Scrimmage.scrimmage_complete == args["completed"])

        ret = []
        result = query.all()
        for i in result:
            ret.append(i.as_dict())

        resp = jsonify(ret)
        return resp

    @flask_praetorian.auth_required
    def post(self):
        """ Create a new Scrimmage """
        parser = reqparse.RequestParser()
        parser.add_argument('subject', required=True, type=str)
        parser.add_argument('schedule', required=True, type=str)
        parser.add_argument('scrimmage_type', required=True, type=str)
        parser.add_argument('presenter', required=True, type=int)
        parser.add_argument('max_advisors', type=int)
        args = parser.parse_args()

        if not args["max_advisors"]:
            args["max_advisors"] = 5

        scrimmage_user = User.query.filter_by(id=args["presenter"]).first()
        new_scrimmage = Scrimmage(subject=args["subject"],
                                  schedule=args["schedule"],
                                  scrimmage_complete=False,
                                  scrimmage_type=args["scrimmage_type"],
                                  max_advisors=args["max_advisors"])
        new_scrimmage.presenters.append(scrimmage_user)

        db.session.add(new_scrimmage)
        db.session.commit()

        resp = jsonify(new_scrimmage.as_dict())
        resp.status_code = 200
        return resp


@api.route('/Scrimmages/<int:id>')
class Scrimmages(Resource):
    @flask_praetorian.auth_required
    def get(self, id):
        """ Returns info about a Scrimmage """
        scrimmage = Scrimmage.query.filter_by(id=id).first()
        return jsonify(scrimmage.as_dict())
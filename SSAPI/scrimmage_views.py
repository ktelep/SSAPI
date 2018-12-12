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
        parser.add_argument('scrimmage_complete', type=inputs.boolean)  # Completed?
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

        if args["scrimmage_complete"] is not None:
            query = query.filter(
                Scrimmage.scrimmage_complete == args["scrimmage_complete"])

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
        parser.add_argument('presenters', required=True, type=list, location="json")
        parser.add_argument('max_advisors', type=int)
        args = parser.parse_args()

        if not args["max_advisors"]:
            args["max_advisors"] = 5

        new_scrimmage = Scrimmage(subject=args["subject"],
                                  schedule=args["schedule"],
                                  scrimmage_complete=False,
                                  scrimmage_type=args["scrimmage_type"],
                                  max_advisors=args["max_advisors"])

        for i in args["presenters"]:
            scrimmage_user = User.query.filter_by(id=i).first()
            if "presenter" in scrimmage_user.roles:
                new_scrimmage.presenters.append(scrimmage_user)
            else:
                resp = jsonify({"message": "Unable to locate or invalid user for presenter"})
                resp.status_code = 400
                return resp

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

    @flask_praetorian.auth_required
    def post(self, id):
        """ Updates a scrimmage """
        scrimmage = Scrimmage.query.filter_by(id=id).first()
        parser = reqparse.RequestParser()
        parser.add_argument('subject', type=str)
        parser.add_argument('schedule', type=str)
        parser.add_argument('scrimmage_type', type=str)
        parser.add_argument('presenters', type=list, location="json")
        parser.add_argument('advisors', type=list, location="json")
        parser.add_argument('max_advisors', type=int)
        parser.add_argument('scrimmage_complete', type=inputs.boolean)
        args = parser.parse_args()

        # If I am an admin, OR one of the presenters, I can modify
        user_id = flask_praetorian.current_user().id
        user = User.query.filter_by(id=user_id).first()

        if (user in scrimmage.presenters or
                'admin' in flask_praetorian.current_user().roles):
            update_dict = {}
            for param in args.keys():
                if args[param]:
                    new_presenters = []
                    new_advisors = []
                    if "presenters" in param:
                        for i in args[param]:
                            new_presenter = User.query.filter_by(id=i).first()
                            if new_presenter and 'presenter' in new_presenter.roles:
                                new_presenters.append(new_presenter)
                            else:
                                resp = jsonify({"message": "Unable to locate or invalid user for presenter"})
                                resp.status_code = 400
                                return resp
                        scrimmage.presenters = new_presenters
                    elif "advisors" in param:
                        for i in args[param]:
                            new_advisor = User.query.filter_by(id=i).first()
                            if new_advisor and 'advisor' in new_advisor.roles:
                                new_advisors.append(new_advisor)
                            else:
                                resp = jsonify({"message": "Unable to locate or invalid user for advisor"})
                                resp.status_code = 400
                                return resp
                        scrimmage.advisors = new_advisors
                    else:
                        update_dict[param] = args[param]

            if update_dict:
                Scrimmage.query.filter_by(id=id).update(update_dict)

            db.session.commit()

        else:
            resp = jsonify({"message": "Unauthorized to update"})
            resp.status_code = 401
            return resp

        resp = jsonify(scrimmage.as_dict())
        resp.status_code = 200
        return resp

    @flask_praetorian.auth_required
    def delete(self, id):
        """ Delete a Scrimmage """
        # If I am an admin, OR one of the presenters, I can delete
        user_id = flask_praetorian.current_user().id
        user = User.query.filter_by(id=user_id).first()
        scrimmage = Scrimmage.query.filter_by(id=id).first()

        if (user in scrimmage.presenters or
                'admin' in flask_praetorian.current_user().roles):
            Scrimmage.query.filter_by(id=id).delete()
            db.session.commit()
            return 'Scrimmage Deleted', 204

        return 'UNAUTHORIZED', 401

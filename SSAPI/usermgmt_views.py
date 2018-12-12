from flask import Flask, request, jsonify
from SSAPI.config import Config
from SSAPI import app, api, db, guard
from flask_restplus import Resource, Api
from flask_sqlalchemy import SQLAlchemy
import flask_praetorian
from SSAPI.models import *


@api.route('/login')
class Login(Resource):

    def post(self):

        req = request.get_json(force=True)
        username = req.get('username', None)
        password = req.get('password', None)

        try:
            user = guard.authenticate(username, password)
            ret = {'access_token': guard.encode_jwt_token(user)}
            return jsonify(ret)
        except Exception as e:
            return e.jsonify()


@api.route('/Users')
class UsersList(Resource):
    @flask_praetorian.auth_required
    def get(self):
        """ Returns a list of users """
        # Filtering/sorting
        filt = request.args.get("role", None)

        if filt:
            all_users = User.query.filter(User.roles.like("%" + filt + "%"))
        else:
            all_users = User.query.all()

        # Generate list to return
        ret = list()
        for users in all_users:
            ret.append(users.as_dict())

        resp = jsonify(ret)
        resp.status_code = 200
        return resp

    def post(self):
        """ Create a new User """
        req = request.get_json(force=True)
        username = req.get('username', None)
        password = req.get('password', None)
        firstname = req.get('firstname', None)
        lastname = req.get('lastname', None)
        roles = req.get('roles', None)

        # Check if user already exists, if so we bail
        if User.query.filter_by(username=username).first():
            resp = jsonify(None)
            resp.status_code = 412

        # Do not allow admin users to be created, they can only be modified
        if "admin" in roles:
            resp = jsonify(None)
            resp.status_code = 412
            return resp

        # Create the actual account
        new_user = User(
            username=username,
            password=guard.encrypt_password(password),
            firstname=firstname,
            lastname=lastname,
            roles=roles)
        db.session.add(new_user)
        db.session.commit()

        resp = jsonify(new_user.as_dict())
        resp.status_code = 200
        return resp


@api.route('/Users/<int:id>')
class Users(Resource):
    @flask_praetorian.auth_required
    def get(self, id):
        """ Returns info about a user (minus password) """
        user = User.query.filter_by(id=id).first()
        return jsonify(user.as_dict())

    @flask_praetorian.auth_required
    def delete(self, id):
        """ Delete a User """
        if (flask_praetorian.current_user().id == id or
                'admin' in flask_praetorian.current_user().roles):
            User.query.filter_by(id=id).delete()
            db.session.commit()
            return 'User Deleted', 204

        return 'UNAUTHORIZED', 401

    @flask_praetorian.auth_required
    def post(self, id):
        """ Updates a User """
        if (flask_praetorian.current_user().id == id or
                'admin' in flask_praetorian.current_user().roles):
            update_dict = {}
            req = request.get_json(force=True)
            for param in list(req.keys()):
                if "username" in param:
                    # Don't allow username change to an existing username
                    name_check = User.query.filter_by(username=req.get(param)).first()
                    if name_check:
                        return 'User Already Exists', 409
                if "password" in param:
                    update_dict[param] = guard.encrypt_password(req.get(param))
                else:
                    update_dict[param] = req.get(param)

                User.query.filter_by(id=id).update(update_dict)

                db.session.commit()

            user = User.query.filter_by(id=id).first()

            resp = jsonify(user.as_dict())
            resp.status_code = 200
            return resp

        else:
            return 'UNAUTHORIZED', 401

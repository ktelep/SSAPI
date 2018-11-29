from SSAPI import app, db, guard
from SSAPI.models import User

guard.init_app(app,User)

db.drop_all()
db.create_all()
db.session.add(User(
    username='admin',
    password=guard.encrypt_password('admin'),
    firstname='administrator',
    lastname='administrator',
    roles='admin,presenter,advisor',
))

db.session.add(User(
    username='presenter',
    password=guard.encrypt_password('presenter'),
    firstname='presenter',
    lastname='presenter',
    roles='presenter',
))

db.session.add(User(
    username='advisor',
    password=guard.encrypt_password('advisor'),
    firstname='advisor',
    lastname='advisor',
    roles='advisor',
))

db.session.add(User(
    username='presentadvisor',
    password=guard.encrypt_password('presentadvisor'),
    firstname='presentadvisor',
    lastname='presentadvisor',
    roles='presenter,advisor',
))

db.session.commit()

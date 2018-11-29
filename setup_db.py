from SSAPI import app, db, guard
from SSAPI.models import User, Scrimmage, ScrimmageInvite

guard.init_app(app, User)

db.drop_all()
db.create_all()
db.session.add(User(
    username='admin',
    password=guard.encrypt_password('admin'),
    firstname='administrator',
    lastname='administrator',
    roles='admin,presenter,advisor',
))

presenter = User(
    username='presenter',
    password=guard.encrypt_password('presenter'),
    firstname='presenter',
    lastname='presenter',
    roles='presenter',
)

advisor = User(
    username='advisor',
    password=guard.encrypt_password('advisor'),
    firstname='advisor',
    lastname='advisor',
    roles='advisor',
)

present_advisor = User(
    username='presentadvisor',
    password=guard.encrypt_password('presentadvisor'),
    firstname='presentadvisor',
    lastname='presentadvisor',
    roles='presenter,advisor',
)

db.session.add(presenter)
db.session.add(advisor)
db.session.add(present_advisor)

new_scrimmage = Scrimmage(
    subject="Test Scrimmage",
    schedule="Test Schedule",
    max_advisors=20,
    scrimmage_type="Demo",
    scrimmage_complete=False)

new_scrimmage.presenters.append(presenter)
new_scrimmage.advisors.append(advisor)
new_scrimmage.advisors.append(present_advisor)

new_scrimmage2 = Scrimmage(
    subject="Test Scrimmage2",
    schedule="Test Schedule2",
    max_advisors=20,
    scrimmage_type="Demo",
    scrimmage_complete=False)

new_scrimmage2.presenters.append(advisor)
new_scrimmage2.advisors.append(presenter)

new_invite = ScrimmageInvite(
    scrimmage=new_scrimmage,
    advisor=advisor)

db.session.add(new_scrimmage)
db.session.add(new_scrimmage2)
db.session.commit()

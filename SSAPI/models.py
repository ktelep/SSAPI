from SSAPI import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    firstname = db.Column(db.Text)
    lastname = db.Column(db.Text)
    roles = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, server_default='true')
    invitations = db.relationship("ScrimmageInvite", backref='advisor')

    @property
    def rolenames(self):
        try:
            return self.roles.split(',')
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_active

    def is_admin(self):
        return "admin" in self.roles

    def as_dict(self):
        return {c.name: getattr(self,c.name) for c in self.__table__.columns if c.name not in "password"}

class ScrimmageInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accepted = db.Column(db.Boolean)
    last_sent = db.Column(db.DateTime)
    responded = db.Column(db.DateTime)
    advisor_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    scrimmage_id = db.Column(db.Integer, db.ForeignKey("scrimmage.id"))

    def as_dict(self):
        return_dict = {c.name: getattr(self,c.name) for c in self.__table__.columns}
        # Note we don't need to follow the relationships here, as the foreign
        # keys will provide with the ID of the related object

        return return_dict

# Many-to-Many reference tables for Scrimmage class
presenters = db.Table('presenters',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('scrimmage_id', db.Integer, db.ForeignKey('scrimmage.id'), primary_key=True)
    )

advisors = db.Table('advisors',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('scrimmage_id', db.Integer, db.ForeignKey('scrimmage.id'), primary_key=True)
    )

class Scrimmage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.Text)
    schedule = db.Column(db.Text)
    scrimmage_type = db.Column(db.Text)
    scrimmage_complete = db.Column(db.Boolean) 
    max_advisors = db.Column(db.Integer)
    presenters = db.relationship('User', secondary = presenters, backref=db.backref('scrimmages_presenter', lazy=True))
    advisors = db.relationship('User', secondary = advisors, backref=db.backref('scrimmages_advisor', lazy=True))
    invites = db.relationship('ScrimmageInvite', backref="scrimmage")

    def as_dict(self):
        return_dict = {c.name: getattr(self,c.name) for c in self.__table__.columns}
        # Follow the M2M relationships to return presenter and advisor IDs
        return_dict["presenters"] = []
        return_dict["advisors"] = []
        for p in self.presenters:
            return_dict["presenters"].append(p.id)
        for a in self.advisors:
            return_dict["advisors"].append(a.id)

        return return_dict



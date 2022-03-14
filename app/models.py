from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(32), index=True)
    last_name = db.Column(db.String(32), index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), index=True)
    phone = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    about_me = db.Column(db.String(500))
    last_viewed = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64))
    student_email = db.Column(db.String(64), index=True)
    parent_name = db.Column(db.String(64))
    parent_email = db.Column(db.String(64))
    secondary_email = db.Column(db.String(64))
    timezone = db.Column(db.Integer)
    location = db.Column(db.String(128))
    status = db.Column(db.String(24), default = "active", index=True)
    pronouns = db.Column(db.String(32))
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor.id'))

    def __repr__(self):
        return '<Student {}>'.format(self.student_name + " " + self.last_name)


class Tutor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), index=True)
    last_name = db.Column(db.String(64))
    email = db.Column(db.String(64), index=True)
    timezone = db.Column(db.Integer)
    status = db.Column(db.String(24), default = "active", index=True)
    students = db.relationship('Student', backref='tutor', lazy='dynamic')

    def __repr__(self):
        return '<Tutor {}>'.format(self.first_name + " " + self.last_name)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

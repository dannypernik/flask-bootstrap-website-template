from datetime import datetime
from time import time
import jwt
from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class UserTestDate(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    test_date_id = db.Column(db.Integer, db.ForeignKey('test_date.id'), primary_key=True)
    is_registered = db.Column(db.Boolean)
    users = db.relationship("User", backref=db.backref('planned_tests', lazy='dynamic'))
    test_dates = db.relationship("TestDate", backref=db.backref('users_interested', lazy='dynamic'))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(32), index=True)
    last_name = db.Column(db.String(32), index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    phone = db.Column(db.String(32), index=True)
    secondary_email = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    timezone = db.Column(db.Integer)
    location = db.Column(db.String(128))
    status = db.Column(db.String(24), default = "active", index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    students = db.relationship('User',
        backref=db.backref('tutor', remote_side=[id]), 
        primaryjoin=(id==tutor_id),
        foreign_keys=[tutor_id],
        post_update=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    children = db.relationship('User',
        primaryjoin=(id==parent_id),
        backref=db.backref('parent', remote_side=[id]),
        foreign_keys=[parent_id],
        post_update=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    last_viewed = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(24), index=True)
    is_admin = db.Column(db.Boolean)
    is_verified = db.Column(db.Boolean)
    session_reminders = db.Column(db.Boolean)
    test_dates = db.relationship('UserTestDate',
                                foreign_keys=[UserTestDate.user_id],
                                backref=db.backref('user', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __repr__(self):
        return '<User {}>'.format(self.email)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_email_verification_token(self, expires_in=3600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')
    
    def add_test_date(self, test_date):
        if not self.is_testing(test_date):
            t = UserTestDate(user_id=self.id, test_date_id=test_date.id)
            db.session.add(t)
            db.session.commit()

    def remove_test_date(self, test_date):
        f = self.test_dates.filter_by(test_date_id=test_date.id).first()
        if f:
            db.session.delete(f)
            

    def is_testing(self, test_date):
        return self.test_dates.filter(
            UserTestDate.test_date_id == test_date.id).count() > 0
    
    def get_dates(self):
        return TestDate.query.join(
                UserTestDate, (UserTestDate.test_date_id == TestDate.id)
            ).filter(UserTestDate.user_id == self.id)

    @staticmethod
    def verify_email_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


class TestDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    test = db.Column(db.String(24))
    status = db.Column(db.String(24), default = "confirmed")
    reg_date = db.Column(db.Date)
    late_date = db.Column(db.Date)
    other_date = db.Column(db.Date)
    score_date = db.Column(db.Date)
    students = db.relationship('User', secondary="user_test_date", backref=db.backref('dates_interested'), lazy='dynamic')

    def __repr__(self):
        return '<TestDate {}>'.format(self.date)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

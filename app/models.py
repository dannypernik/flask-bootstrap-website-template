from datetime import datetime
from time import time
import jwt
from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(32))
    last_name = db.Column(db.String(32))
    email = db.Column(db.String(64), unique=True, index=True)
    phone = db.Column(db.String(32))
    password_hash = db.Column(db.String(128))
    location = db.Column(db.String(128))
    status = db.Column(db.String(24))
    role = db.Column(db.String(24))
    parent_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    children = db.relationship('User',
        primaryjoin=(id==parent_id),
        backref=db.backref('parent', remote_side=[id]),
        foreign_keys=[parent_id],
        post_update=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    last_viewed = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean)
    is_verified = db.Column(db.Boolean)

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

    @staticmethod
    def verify_email_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(id)

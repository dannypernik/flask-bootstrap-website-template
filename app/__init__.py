import os
import sentry_sdk
from flask import Flask
from config import Config
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_bootstrap import Bootstrap
from flask_hcaptcha import hCaptcha
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True, compare_type=True)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)
hcaptcha = hCaptcha(app)

from app import routes, models, errors
login.login_message = u'Please sign in to access this page.'
from app import app, db
from app.models import User, Post
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    "https://7b07a0f6a2244061a029e1deaa863161@o473156.ingest.sentry.io/5507799",
    traces_sample_rate=1.0, integrations=[FlaskIntegration()])

division_by_zero = 1 / 0

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'users':User.query.all()}

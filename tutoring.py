from app import app, db
from app.models import User, Student, TestDate

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Student': Student, 'TestDate':TestDate, 'users':User.query.all()}

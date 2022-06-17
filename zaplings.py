from app import app, db
from app.models import User, Idea

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'users':User.query.all(), 'Idea': Idea, 'ideas':Idea.query.all()}

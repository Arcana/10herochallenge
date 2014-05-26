"""
Manager script :)

Takes the following commands:
- runserver
- shell
- init_db
- check_matches
"""

from app import app as application, db
from flask.ext.script import Manager

manager = Manager(application)

@manager.command
def init_db():
    db.create_all()


@manager.command
def check_challenges():
    from app.scripts.check_challenges import check_challenges as _check_challenges
    _check_challenges()


if __name__ == "__main__":
    manager.run()

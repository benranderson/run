import os
import json
import click
from datetime import datetime
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Event, Exercise

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Exercise=Exercise)


@app.cli.command()
def test():
    """Run the unit tests."""
    # import unittest
    # tests = unittest.TestLoader().discover('tests')
    # unittest.TextTestRunner(verbosity=2).run(tests)

    import pytest
    pytest.main(['tests/'])


@app.cli.command()
@click.option('--drop_first', default=False)
def createdb(drop_first):
    """Creates a database."""
    if drop_first:
        db.drop_all()
    db.create_all()


@app.cli.command()
def seeddb():
    user = User(email='ben@domain.com',
                first_name='Ben',
                last_name='Randerson')
    user.set_password('test')
    db.session.add(user)
    EVENTS = json.load(open('events.json'))
    for event in EVENTS:
        date = datetime.strptime(EVENTS[event]['date'], '%Y-%m-%d').date()
        d = EVENTS[event]['date']
        e = Event(name=event,
                  distance=EVENTS[event]['distance'],
                  date=date)
        db.session.add(e)
    db.session.commit()


@app.cli.command()
def clean():
    """Remove *.pyc and *.pyo files recursively starting at current directory.
    """
    for dirpath, dirnames, filenames in os.walk('.'):
        for filename in filenames:
            if filename.endswith('.pyc') or filename.endswith('.pyo'):
                full_pathname = os.path.join(dirpath, filename)
                print('Removing {}'.format(full_pathname))
                os.remove(full_pathname)

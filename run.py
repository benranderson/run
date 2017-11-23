import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import User, Exercise

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Exercise=Exercise)


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command()
@click.option('--drop_first', default=False)
def createdb(drop_first):
    """Creates a database."""
    if drop_first:
        db.drop_all()
    db.create_all()

from datetime import datetime
from . import db
from .exceptions import ValidationError


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))

    def __repr__(self):
        return f'< {self.__class__.__name__} {self.username}>'


class Exercise(db.Model):

    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(128))
    duration = db.Column(db.Numeric)
    workoutset_id = db.Column(db.Integer, db.ForeignKey('workoutsets.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.description} ({self.duration})>'


class WorkoutSet(db.Model):

    __tablename__ = 'workoutsets'

    id = db.Column(db.Integer, primary_key=True)
    reps = db.Column(db.Integer)
    exercises = db.relationship('Exercise', backref='workoutset')
    duration = db.Column(db.Float)
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.reps}>'


class Workout(db.Model):

    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.now)
    category = db.Column(db.String(128))
    workoutsets = db.relationship(
        'WorkoutSet', backref='workout', lazy='dynamic',
        cascade='all, delete-orphan')
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.date}>'


class Plan(db.Model):

    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(64))
    start_date = db.Column(db.DateTime, default=datetime.now)
    workouts = db.relationship(
        'Workout', backref='plan', lazy='dynamic',
        cascade='all, delete-orphan')
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.level}>'

    def create(self, days=None):
        '''
        Creates schedule based on ability level and training days
        '''
        pass


class Event(db.Model):

    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    distance = db.Column(db.Numeric)
    plans = db.relationship('Plan', backref='event', lazy='dynamic')

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name}>'

    def import_data(self, data):
        try:
            self.name = data['name']
            self.distance = data['distance']
        except KeyError as e:
            raise ValidationError('Invalid event: missing ' + e.args[0])
        return self

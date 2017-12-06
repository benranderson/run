from datetime import datetime, date, timedelta
from collections import namedtuple
from itertools import cycle
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, admin, login_manager
from .exceptions import ValidationError
from .builder import rest_week


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    plans = db.relationship(
        'Plan', backref='user', lazy='dynamic',
        cascade='all, delete-orphan')

    def __repr__(self):
        return f'< {self.__class__.__name__} {self.username}>'

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Exercise(db.Model):

    __tablename__ = 'exercises'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(128))
    duration = db.Column(db.Numeric)
    workoutset_id = db.Column(db.Integer, db.ForeignKey('workoutsets.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.description} ({self.duration})>'

    def __str__(self):
        """ Format duration in seconds if less than 1 minute. """
        if self.duration < 1:
            duration = f'{self.duration*60:.0f}s'
        else:
            duration = f'{self.duration:.0f}mins'
        return f'{self.description} ({duration})'


class WorkoutSet(db.Model):

    __tablename__ = 'workoutsets'

    id = db.Column(db.Integer, primary_key=True)
    reps = db.Column(db.Integer)
    exercises = db.relationship('Exercise', backref='workoutset')
    workout_id = db.Column(db.Integer, db.ForeignKey('workouts.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.reps}>'

    def __str__(self):
        exs = ''
        for exercise in self.exercises:
            exs += f'{exercise}\n'
        return f'{self.reps}x {exs}'

    @property
    def duration(self):
        pass


class Workout(db.Model):

    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.now())
    category = db.Column(db.String(128))
    workoutsets = db.relationship(
        'WorkoutSet', backref='workout', lazy='dynamic',
        cascade='all, delete-orphan')
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.date}>'


RepsSetting = namedtuple('RepsSetting', [
    'start',
    'step',
    'step_interval',
    'max',
])

ExerciseSetting = namedtuple('ExerciseSetting', [
    'description',
    'start',
    'step',
    'step_interval',
    'max',
])


class Plan(db.Model):

    __tablename__ = 'plans'

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(64))
    start_date = db.Column(db.Date, default=datetime.now())
    workouts = db.relationship(
        'Workout', backref='plan', lazy='dynamic',
        cascade='all, delete-orphan')
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    fivek_plans = {
        'Beginner': [
            [
                {'category': 'easy',
                 'warmup': 0,
                 'warmdown': 0,
                 'reps': RepsSetting(1, 0, 0, 1),
                 'exercises': [ExerciseSetting('easy', 25, 5, 3, 35)]}
            ],
            [
                {'category': 'intervals',
                 'warmup': 10,
                 'warmdown': 10,
                 'reps': RepsSetting(6, 1, 2, 8),
                 'exercises': [ExerciseSetting('intervals', 1, 0.25, 2, 2)]},
                {'category': 'hillsprint',
                 'warmup': 0,
                 'warmdown': 0,
                 'reps': RepsSetting(5, 0, 0, 1),
                 'exercises': [ExerciseSetting('hillsprint', 25, 5, 3, 100)]}
            ],
            [
                {'category': 'easy',
                 'warmup': 10,
                 'warmdown': 10,
                 'reps': RepsSetting(5, 0, 0, 1),
                 'exercises': [ExerciseSetting('fast', 0.5, 0.25, 2, 2),
                               ExerciseSetting('easy', 1, 0, 0, 1)]}
            ]
        ],
        'Intermediate': [
            [
                {'category': 'easy',
                 'warmup': 0,
                 'warmdown': 0,
                 'reps': RepsSetting(1, 0, 0, 1),
                 'exercises': [ExerciseSetting('easy', 25, 5, 3, 100)]}
            ],
            [
                {'category': 'hillsprint',
                 'warmup': 12,
                 'warmdown': 12,
                 'reps': RepsSetting(6, 1, 2, 8),
                 'exercises': [ExerciseSetting('hill', 1, 0.25, 2, 2)]},
                {'category': 'easy',
                 'warmup': 0,
                 'warmdown': 0,
                 'reps': RepsSetting(1, 0, 0, 1),
                 'exercises': [ExerciseSetting('easy', 25, 5, 3, 100)]}
            ],
            [
                {'category': 'easy',
                 'warmup': 10,
                 'warmdown': 10,
                 'reps': RepsSetting(5, 0, 0, 1),
                 'exercises': [ExerciseSetting('fast', 0.5, 0.25, 2, 2),
                               ExerciseSetting('easy', 1, 0, 0, 1)]}
            ]
        ],
        'Advanced': [
            [
                {'category': 'easy',
                 'warmup': 0,
                 'warmdown': 0,
                 'reps': RepsSetting(1, 0, 0, 1),
                 'exercises': [ExerciseSetting('easy', 25, 5, 3, 100)]}
            ],
            [
                {'category': 'hillsprint',
                 'warmup': 12,
                 'warmdown': 12,
                 'reps': RepsSetting(6, 1, 2, 8),
                 'exercises': [ExerciseSetting('hill', 1, 0.25, 2, 2)]},
                {'category': 'easy',
                 'warmup': 0,
                 'warmdown': 0,
                 'reps': RepsSetting(1, 0, 0, 1),
                 'exercises': [ExerciseSetting('easy', 25, 5, 3, 100)]}
            ],
            [
                {'category': 'easy',
                 'warmup': 10,
                 'warmdown': 10,
                 'reps': RepsSetting(5, 0, 0, 1),
                 'exercises': [ExerciseSetting('fast', 0.5, 0.25, 2, 2),
                               ExerciseSetting('easy', 1, 0, 0, 1)]}
            ]
        ]
    }

    plan_settings = {
        '5k': fivek_plans,
        '10k': fivek_plans,
        'half': fivek_plans,
        'full': fivek_plans
    }

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.level}>'

    @staticmethod
    def weeks_between_dates(start_date, end_date):
        '''
        Return the number of weeks between two dates
        '''
        monday1 = (start_date - timedelta(days=start_date.weekday()))
        monday2 = (end_date - timedelta(days=end_date.weekday()))
        return int((monday2 - monday1).days / 7)

    @property
    def length(self):
        '''
        Length of the training plan in weeks
        '''
        return self.weeks_between_dates(self.start_date, self.event.date)

    def create(self, days=None):
        '''
        Creates schedule based on ability level and training days.
        '''

        plan = Plan.plan_settings[self.event.distance]
        settings = plan[self.level]

        if days is not None:
            for day, plan in zip(days, settings):
                for wk, progression in zip(range(self.length), cycle(plan)):

                    # determine date of workout
                    dt = self.start_date - \
                        timedelta(days=self.start_date.weekday()) + \
                        timedelta(days=day) + timedelta(weeks=wk)

                    w = Workout(plan=self, date=dt,
                                category=progression['category'])

                    # warmup set
                    if progression['warmup'] > 0:
                        e = Exercise(description='easy',
                                     duration=progression['warmup'])
                        warmup = WorkoutSet(workout=w, reps=1, exercises=[e])

                    # work set, first determine if rest week
                    if rest_week(wk, self.length):
                        multiple = wk - 1
                    else:
                        multiple = wk

                    reps = min(progression['reps'].start +
                               progression['reps'].step * multiple,
                               progression['reps'].max)

                    exercises = []
                    for es in progression['exercises']:
                        description = es.description
                        duration = min(es.start + es.step * multiple, es.max)
                        e = Exercise(description=description,
                                     duration=duration)
                        exercises.append(e)

                    ws = WorkoutSet(workout=w, reps=reps, exercises=exercises)

                    # warmdown set
                    if progression['warmdown'] > 0:
                        e = Exercise(description='easy',
                                     duration=progression['warmdown'])
                        warmdown = WorkoutSet(workout=w, reps=1, exercises=[e])

        else:
            print('Define workout days')


class Event(db.Model):

    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    distance = db.Column(db.String(64))
    date = db.Column(db.Date, nullable=False)
    plans = db.relationship('Plan', backref='event', lazy='dynamic')

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name} ({self.distance})>'

    def import_data(self, data):
        try:
            self.name = data['name']
            self.distance = data['distance']
        except KeyError as e:
            raise ValidationError('Invalid event: missing ' + e.args[0])
        return self


class MyView(BaseView):
    @expose('/')
    def index(self):
        return 'Hello World!'


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Event, db.session))
admin.add_view(ModelView(Plan, db.session))
admin.add_view(ModelView(Workout, db.session))

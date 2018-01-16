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

from pprint import pprint


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

    def __str__(self):
        description = f'{self.category.title()} Workout\n'
        for workoutset in self.workoutsets:
            description += f'{str(workoutset.reps)}x [ '
            for exercise in workoutset.exercises:
                description += f'{exercise.description} ({exercise.duration:.1f}mins) '
            description += ']\n'
        return description


class PlanSetting(db.Model):

    __tablename__ = 'plan_settings'

    id = db.Column(db.Integer, primary_key=True)
    distance = db.Column(db.String(64))
    level = db.Column(db.String(64))
    plan_days = db.relationship('PlanDay', backref='plan_setting',
                                lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.distance} - {self.level}>'


class PlanDay(db.Model):

    __tablename__ = 'plan_days'

    id = db.Column(db.Integer, primary_key=True)
    progressions = db.relationship('Progression', backref='plan_day',
                                   lazy='dynamic', cascade='all, delete-orphan')
    plan_setting_id = db.Column(db.Integer, db.ForeignKey('plan_settings.id'))


class Progression(db.Model):

    __tablename__ = 'progressions'

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Integer)
    category = db.Column(db.String(64))
    warmup = db.Column(db.Numeric)
    warmdown = db.Column(db.Numeric)
    workoutset_settings = db.relationship('WorkoutSetSetting', backref='progression',
                                          lazy='dynamic', cascade='all, delete-orphan')
    plan_day_id = db.Column(db.Integer, db.ForeignKey('plan_days.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.category}>'

    def number_of_workouts(self):
        return len(self.workoutset_settings)


class WorkoutSetSetting(db.Model):

    __tablename__ = 'workoutset_settings'

    id = db.Column(db.Integer, primary_key=True)
    reps_start = db.Column(db.Integer)
    reps_step = db.Column(db.Integer)
    reps_step_interval = db.Column(db.Integer)
    reps_max = db.Column(db.Integer)
    exercise_settings = db.relationship('ExerciseSetting', backref='workoutset_setting',
                                        lazy='dynamic', cascade='all, delete-orphan')
    progression_id = db.Column(db.Integer, db.ForeignKey('progressions.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'


class ExerciseSetting(db.Model):

    __tablename__ = 'exercise_settings'

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(64))
    duration_start = db.Column(db.Numeric)
    duration_step = db.Column(db.Numeric)
    duration_step_interval = db.Column(db.Numeric)
    duration_max = db.Column(db.Numeric)
    workoutset_setting_id = db.Column(
        db.Integer, db.ForeignKey('workoutset_settings.id'))

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.description}>'


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
        plan_setting = PlanSetting.query.filter_by(level=self.level).first()

        if days is not None:
            for day, plan_day in zip(days, plan_setting.plan_days):

                progress_tally = {}
                for progression in plan_day.progressions:
                    progress_tally[progression] = {}
                    for workoutset_setting in progression.workoutset_settings:
                        progress_tally[progression][workoutset_setting] = {}
                        progress_tally[progression][workoutset_setting]['reps'] = 0
                        for es in workoutset_setting.exercise_settings:
                            progress_tally[progression][workoutset_setting][es] = 0

                for wk, progression in zip(range(self.length), cycle(plan_day.progressions)):

                    # determine date of workout
                    dt = self.start_date - \
                        timedelta(days=self.start_date.weekday()) + \
                        timedelta(days=day) + timedelta(weeks=wk)

                    w = Workout(plan=self, date=dt,
                                category=progression.category)

                    # warmup set
                    if progression.warmup > 0:
                        e = Exercise(description='easy',
                                     duration=progression.warmup)
                        warmup = WorkoutSet(workout=w, reps=1, exercises=[e])

                    # work set, first determine if rest week
                    if rest_week(wk, self.length):
                        multiple = wk - 1
                    else:
                        multiple = wk

                    for workoutset_setting in progression.workoutset_settings:

                        # check if reps progress week
                        if workoutset_setting.reps_step_interval > 0 and (wk + 1) % workoutset_setting.reps_step_interval == 0:
                            progress_tally[progression][workoutset_setting]['reps'] += workoutset_setting.reps_step

                        reps = min(workoutset_setting.reps_start +
                                   progress_tally[progression][workoutset_setting]['reps'],
                                   workoutset_setting.reps_max)

                        ws = WorkoutSet(workout=w, reps=reps)

                        for es in workoutset_setting.exercise_settings:
                            description = es.description
                            # check if duration progress week
                            if es.duration_step_interval > 0 and (wk + 1) % es.duration_step_interval == 0:
                                progress_tally[progression][workoutset_setting][es] += es.duration_step
                            duration = min(es.duration_start +
                                           progress_tally[progression][workoutset_setting][es],
                                           es.duration_max)
                            e = Exercise(workoutset=ws, description=description,
                                         duration=duration)

                    # warmdown set
                    if progression.warmdown > 0:
                        e = Exercise(description='easy',
                                     duration=progression.warmdown)
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
admin.add_view(ModelView(PlanSetting, db.session))
admin.add_view(ModelView(PlanDay, db.session))
admin.add_view(ModelView(Progression, db.session))
admin.add_view(ModelView(WorkoutSetSetting, db.session))
admin.add_view(ModelView(ExerciseSetting, db.session))

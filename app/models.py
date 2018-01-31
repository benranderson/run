from datetime import datetime, date, timedelta
from dateutil import parser as datetime_parser
from dateutil.tz import tzutc
from collections import namedtuple
from itertools import cycle
from flask import url_for
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, admin, login_manager
from .exceptions import ValidationError
from .builder import weeks_between_dates, progression_start_date, \
    reps_or_duration, rest_week

from pprint import pprint


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_next else None
            }
        }
        return data


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, PaginatedAPIMixin, db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    first_name = db.Column(db.String(64), unique=True, index=True)
    last_name = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    plans = db.relationship(
        'Plan', backref='user', lazy='dynamic',
        cascade='all, delete-orphan')

    def __repr__(self):
        return f'< {self.__class__.__name__} {self.first_name} {self.last_name}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            '_links': {
                'self': url_for('api.get_user', id=self.id),
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['first_name', 'last_name', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])


class Event(PaginatedAPIMixin, db.Model):

    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    distance = db.Column(db.String(64))
    date = db.Column(db.Date, nullable=False)
    plans = db.relationship('Plan', backref='event', lazy='dynamic')

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.name} ({self.distance})>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'distance': self.distance,
            'date': self.date.isoformat() + 'Z',
            '_links': {
                'self': url_for('api.get_event', id=self.id),
            }
        }

    def from_dict(self, data):
        for field in ['name', 'distance']:
            if field in data:
                setattr(self, field, data[field])
        if 'date' in data:
            self.date = datetime_parser.parse(data['date']).astimezone(
                tzutc()).replace(tzinfo=None)


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
        durations = [exercise.duration for exercise in self.exercises]
        return self.reps * sum(durations)


class Workout(PaginatedAPIMixin, db.Model):

    __tablename__ = 'workouts'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.now())
    category = db.Column(db.String(128))
    rest = db.Column(db.Boolean)
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

    @property
    def duration(self):
        durations = [workoutset.duration for workoutset in self.workoutsets]
        return sum(durations)

    def to_dict(self):
        data = {
            'id': self.id,
            'date': self.date.iso_format() + 'Z',
            'category': self.category,
            'rest': self.rest,
            '_links': {
                'self': url_for('api.get_workout', id=self.id),
            }
        }
        return data

    def from_dict(self, data, new_user=False):
        for field in ['usermame', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.password(data['password'])


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

    @property
    def length(self):
        '''
        Length of the training plan in weeks
        '''
        return weeks_between_dates(self.start_date, self.event.date)

    def create(self, days):

        plans = {
            '5k': {
                'Beginner': self.create_5k_beginner_plan,
                'Intermediate': self.create_5k_beginner_plan,
                'Advanced': self.create_5k_beginner_plan,
            },
            '10k': {
                'Beginner': self.create_5k_beginner_plan,
                'Intermediate': self.create_5k_beginner_plan,
                'Advanced': self.create_5k_beginner_plan,
            },
            'half': {
                'Beginner': self.create_5k_beginner_plan,
                'Intermediate': self.create_5k_beginner_plan,
                'Advanced': self.create_5k_beginner_plan,
            },
            'full': {
                'Beginner': self.create_5k_beginner_plan,
                'Intermediate': self.create_5k_beginner_plan,
                'Advanced': self.create_5k_beginner_plan,
            }
        }

        plans[self.event.distance][self.level](days)

    def create_5k_beginner_plan(self, days):
        '''
        Creates beginner training plan
        - start date
        - weeks
        - rest weeks
        - ramp up 4 weeks
        - workout priority
            - day 1: runeasy
            - day 2: intervals/hillsprint rotation
            - day 3: runeasy
        '''

        start_dates = [progression_start_date(
            self.start_date, day) for day in days]

        progressions = [self.runeasy_progression,
                        self.intervals_hillsprint_progression,
                        self.runeasy_progression]

        params = [
            {
                'start': 25,
                'step': 5,
                'interval': 3,
                'maximum': 35
            },
            {
                'intervals_warmupdown': 10,
                'intervals_reps_start': 5,
                'intervals_reps_step': 1,
                'intervals_reps_interval': 1,
                'intervals_reps_max': 8,
                'intervals_duration_start': 0.25,
                'intervals_duration_step': 0.25,
                'intervals_duration_interval': 1,
                'intervals_duration_maximum': 1,
                'hillsprint_warmupdown': 12,
                'hillsprint_reps_start': 6,
                'hillsprint_reps_step': 2,
                'hillsprint_reps_interval': 3,
                'hillsprint_reps_max': 10,
                'hillsprint_duration_start': 0.25,
                'hillsprint_duration_step': 0,
                'hillsprint_duration_interval': 0,
                'hillsprint_duration_maximum': 0.25
            },
            {
                'start': 30,
                'step': 5,
                'interval': 3,
                'maximum': 35
            }
        ]

        for progression, param, start_date in zip(progressions, params, start_dates):
            progression(start_date, self.length, **param)

    def runeasy_progression(self, start_date, plan_length, start, step,
                            interval, maximum):

        for week in range(plan_length):
            date = start_date + timedelta(weeks=week)
            workout = Workout(plan=self, date=date,
                              category='easy', rest=rest_week(week, plan_length))
            workout_set = WorkoutSet(workout=workout, reps=1)
            duration = reps_or_duration(plan_length=plan_length,
                                        plan_week=week,
                                        workout_week=week,
                                        start=start,
                                        step=step,
                                        maximum=maximum,
                                        interval=interval)
            exercise = Exercise(workoutset=workout_set,
                                description='easy', duration=duration)

    def intervals_hillsprint_progression(self,
                                         start_date,
                                         plan_length,
                                         intervals_warmupdown,
                                         intervals_reps_start,
                                         intervals_reps_step,
                                         intervals_reps_interval,
                                         intervals_reps_max,
                                         intervals_duration_start,
                                         intervals_duration_step,
                                         intervals_duration_interval,
                                         intervals_duration_maximum,
                                         hillsprint_warmupdown,
                                         hillsprint_reps_start,
                                         hillsprint_reps_step,
                                         hillsprint_reps_interval,
                                         hillsprint_reps_max,
                                         hillsprint_duration_start,
                                         hillsprint_duration_step,
                                         hillsprint_duration_interval,
                                         hillsprint_duration_maximum):

        for week in range(plan_length):
            date = start_date + timedelta(weeks=week)
            if week % 2 == 0:
                workout = Workout(plan=self, date=date, category='intervals')
                workout_set = WorkoutSet(workout=workout,
                                         reps=1,
                                         exercises=[Exercise(description='easy',
                                                             duration=intervals_warmupdown)])
                reps = reps_or_duration(plan_length=plan_length,
                                        plan_week=week,
                                        workout_week=int(week / 2),
                                        start=intervals_reps_start,
                                        step=intervals_reps_step,
                                        maximum=intervals_reps_max,
                                        interval=intervals_reps_interval)
                workout_set = WorkoutSet(workout=workout,
                                         reps=reps)
                duration = reps_or_duration(plan_length=plan_length,
                                            plan_week=week,
                                            workout_week=int(week / 2),
                                            start=intervals_duration_start,
                                            step=intervals_duration_step,
                                            maximum=intervals_duration_maximum,
                                            interval=intervals_duration_interval)
                exercise = Exercise(workoutset=workout_set,
                                    description='fast', duration=duration)
                exercise = Exercise(workoutset=workout_set,
                                    description='easy', duration=1)
                workout_set = WorkoutSet(workout=workout,
                                         reps=1,
                                         exercises=[Exercise(description='easy',
                                                             duration=intervals_warmupdown)])
            else:
                workout = Workout(plan=self, date=date, category='hillsprint')
                workout_set = WorkoutSet(workout=workout,
                                         reps=1,
                                         exercises=[Exercise(description='easy',
                                                             duration=hillsprint_warmupdown)])
                reps = reps_or_duration(plan_length=plan_length,
                                        plan_week=week,
                                        workout_week=int(week / 2),
                                        start=hillsprint_reps_start,
                                        step=hillsprint_reps_step,
                                        maximum=hillsprint_reps_max,
                                        interval=hillsprint_reps_interval)
                workout_set = WorkoutSet(workout=workout,
                                         reps=reps)
                duration = reps_or_duration(plan_length=plan_length,
                                            plan_week=week,
                                            workout_week=int(week / 2),
                                            start=hillsprint_duration_start,
                                            step=hillsprint_duration_step,
                                            maximum=hillsprint_duration_maximum,
                                            interval=hillsprint_duration_interval)
                exercise = Exercise(workoutset=workout_set,
                                    description='hillsprint', duration=duration)
                workout_set = WorkoutSet(workout=workout,
                                         reps=1,
                                         exercises=[Exercise(description='easy',
                                                             duration=hillsprint_warmupdown)])


class MyView(BaseView):
    @expose('/')
    def index(self):
        return 'Hello World!'


admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Event, db.session))
admin.add_view(ModelView(Plan, db.session))
admin.add_view(ModelView(Workout, db.session))

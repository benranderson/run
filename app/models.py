from datetime import datetime, date, timedelta
from collections import namedtuple
from itertools import cycle
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, admin, login_manager
from .exceptions import ValidationError
from .builder import weeks_between_dates, progression_start_date, \
    reps_or_duration, rest_week

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


class Workout(db.Model):

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

        if days:
            start_date = progression_start_date(self.start_date, days[0])
            self.runeasy_progression(start_date,
                                     self.length,
                                     start=25,
                                     step=5,
                                     interval=3,
                                     maximum=35)
        if len(days) > 1:
            start_date = progression_start_date(self.start_date, days[1])
            self.intervals_hillsprint_progression(start_date,
                                                  self.length,
                                                  intervals_warmupdown=10,
                                                  intervals_reps_start=5,
                                                  intervals_reps_step=1,
                                                  intervals_reps_interval=1,
                                                  intervals_reps_max=8,
                                                  intervals_duration_start=0.25,
                                                  intervals_duration_step=0.25,
                                                  intervals_duration_interval=1,
                                                  intervals_duration_maximum=1,
                                                  hillsprint_warmupdown=12,
                                                  hillsprint_reps_start=6,
                                                  hillsprint_reps_step=2,
                                                  hillsprint_reps_interval=3,
                                                  hillsprint_reps_max=10,
                                                  hillsprint_duration_start=0.25,
                                                  hillsprint_duration_step=0,
                                                  hillsprint_duration_interval=0,
                                                  hillsprint_duration_maximum=0.25)
        if len(days) > 2:
            start_date = progression_start_date(self.start_date, days[2])
            self.runeasy_progression(start_date,
                                     self.length,
                                     start=30,
                                     step=5,
                                     interval=3,
                                     maximum=35)

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

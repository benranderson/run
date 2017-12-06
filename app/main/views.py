from flask import render_template, session, redirect, url_for, current_app, \
    flash
from flask_login import current_user
from datetime import date, timedelta
from .. import db
from ..models import Event, Plan, Workout
from ..email import send_email
from . import main
from .forms import PlanForm
from .calendar import WorkoutCalendar


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/create', methods=['GET', 'POST'])
def create():
    form = PlanForm()
    form.event_id.choices = [(e.id, e.name)
                             for e in Event.query.order_by('name') if date.today() < e.date < (date.today() + timedelta(weeks=4 * 12))]
    if form.validate_on_submit():
        plan = Plan.query.filter_by(
            user=current_user._get_current_object()).first()
        if plan is not None:
            db.session.delete(plan)
        event = Event.query.filter_by(id=form.event_id.data).first()
        plan = Plan(start_date=date.today(), event=event, level=form.level.data,
                    user=current_user._get_current_object())
        db.session.add(plan)
        days = [day for day in form.days.data]
        plan.create(days)
        db.session.commit()
        flash('Plan created.')
        return redirect(url_for('.plan', id=plan.id))
    return render_template('create.html', form=form)


@main.route('/plan/<int:id>', methods=['GET', 'POST'])
def plan(id):
    '''
    Show a calendar with the training plan schedule
    '''
    plan = Plan.query.filter(
        Plan.user == current_user._get_current_object()).first()

    workouts = {workout.date: workout for workout in plan.workouts}

    calendars = []

    for i, workout_date in enumerate(workouts):
        if i == 0:
            calendar_workout_date = workout_date
        if i == 0 or is_next_month(calendar_workout_date, workout_date):
            calendars.append(WorkoutCalendar(
                workouts).formatmonth(workout_date.year, workout_date.month))
            calendar_workout_date = workout_date

    return render_template('plan.html', plan=plan, calendars=calendars)


def is_next_month(first_date, second_date):
    """ Return True if second_date is in following month to first_date """
    return (second_date.month - first_date.month) + \
        (second_date.year - first_date.year) * first_date.month == 1

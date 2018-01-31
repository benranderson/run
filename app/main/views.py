from datetime import date, timedelta
from ics import Calendar
from ics import Event as icsEvent
from flask import render_template, session, redirect, url_for, current_app, \
    flash, send_file
from flask_login import current_user, login_required
from .. import db
from ..models import User, Event, Plan, Workout
from ..email import send_email
from . import main
from .forms import PlanForm, WorkoutForm
from .calendar import WorkoutCalendar


@main.route('/', methods=['GET', 'POST'])
def index():
    events = [event for event in Event.query.order_by(
        'date').all() if event.date >= date.today()]
    return render_template('index.html', events=events)


@main.route('/user/<int:id>', methods=['GET', 'POST'])
@login_required
def user(id):
    user = User.query.filter_by(id=id).first_or_404()
    plan = Plan.query.filter_by(user=user).first()
    calendars = False

    if plan:
        workouts = {workout.date: workout for workout in plan.workouts}

        calendars = []

        for i, workout_date in enumerate(workouts):
            if i == 0:
                calendar_workout_date = workout_date
            if i == 0 or is_next_month(calendar_workout_date, workout_date):
                calendars.append(WorkoutCalendar(
                    workouts).formatmonth(workout_date.year, workout_date.month))
                calendar_workout_date = workout_date

    return render_template('user.html', user=user, plan=plan,
                           calendars=calendars)


@main.route('/create', methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('.user', id=current_user.id))
    return render_template('create.html', form=form)


@main.route('/workout/<int:id>', methods=['GET', 'POST'])
@login_required
def workout(id):
    workout = Workout.query.get_or_404(id)
    return render_template('workout.html', workout=workout)


@main.route('/plan/<int:id>/ical', methods=['GET', 'POST'])
def ical(id):
    plan = Plan.query.get_or_404(id)
    c = Calendar()
    for workout in plan.workouts:
        e = icsEvent()
        e.name = workout.category
        e.begin = str(workout.date)
        e.description = str(workout)
        print(e.description)
        c.events.append(e)

    print(c.events)

    with open('app/workout-cal.ics', 'w') as f:
        f.writelines(c)

    try:
        return send_file('workout-cal.ics', attachment_filename='workout-cal.ics')
    except Exception as e:
        return str(e)

    return redirect(url_for('.plan', id=id))


def is_next_month(first_date, second_date):
    """ Return True if second_date is in following month to first_date """
    return (second_date.month - first_date.month) + \
        (second_date.year - first_date.year) * first_date.month == 1

from flask import render_template, session, redirect, url_for, current_app, \
    flash
from datetime import date
from .. import db
from ..models import Event, Plan
from ..email import send_email
from . import main
from .forms import EventForm


@main.route('/', methods=['GET', 'POST'])
def index():
    form = EventForm()
    form.event_id.choices = [(e.id, e.name)
                             for e in Event.query.order_by('name')]
    if form.validate_on_submit():
        event = Event(name=form.name.data)
        db.session.add(event)
        db.session.commit()
        flash('Event added.')
        return redirect(url_for('.index'))
    return render_template('index.html', form=form)


# @main.route('/', methods=['GET', 'POST'])
# def index():
#     form = PlanForm(date.today())

#     if form.validate_on_submit():
#         event = Event.query.filter_by(name=form.event_name.data).first()

#         plan = Plan(level=form.level.data,
#                     start_date=form.start_date.data,
#                     level=form.level.data,)
#         db.session.add(facility)
#         db.session.commit()
#         flash('Facility added.')
#         return redirect(url_for('.index'))
#     facilities = Facility.query.all()
#     return render_template('index.html', form=form, facilities=facilities)

#     if form.validate_on_submit():
#         event = form.event.data
#         level = dict(LEVELS).get(form.level.data)
#         days = [day for day in form.days.data]

#         plan = get_plan(event, level)
#         plan.create(days)

#         Workout.query.delete()

#         for workout in plan.schedule:
#             wo = Workout(workout.date, workout.category, workout.duration,
#                          str(workout))
#             db.session.add(wo)
#             db.session.commit()

#         return redirect(url_for('main.calendar'))
#         # return render_template('calendar.html')
#     return render_template('index.html', form=form)

#     if form.validate_on_submit():
#         user = User.query.filter_by(username=form.name.data).first()
#         if user is None:
#             user = User(username=form.name.data)
#             db.session.add(user)
#             db.session.commit()
#             session['known'] = False
#             if current_app.config['RUN_ADMIN']:
#                 send_email(current_app.config['RUN_ADMIN'], 'New User',
#                            'mail/new_user', user=user)
#         else:
#             session['known'] = True
#         session['name'] = form.name.data
#         return redirect(url_for('.index'))
#     return render_template('index.html',
#                            form=form, name=session.get('name'),
#                            known=session.get('known', False))

from flask import render_template, session, redirect, url_for, current_app, \
    flash
from flask_login import current_user
from datetime import date, timedelta
from .. import db
from ..models import Event, Plan
from ..email import send_email
from . import main
from .forms import PlanForm


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/create', methods=['GET', 'POST'])
def create():
    form = PlanForm()
    form.event_id.choices = [(e.id, e.name)
                             for e in Event.query.order_by('name') if date.today() < e.date < (date.today() + timedelta(weeks=4 * 12))]
    if form.validate_on_submit():
        event = Event.query.filter_by(id=form.event_id.data).first()
        plan = Plan(event=event, level=form.level.data,
                    user=current_user._get_current_object())
        db.session.add(plan)
        db.session.commit()
        flash('Plan created.')
        return redirect(url_for('.schedule'))
    return render_template('create.html', form=form)


@main.route('/schedule', methods=['GET', 'POST'])
def schedule():
    return render_template('schedule.html')

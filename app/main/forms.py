from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class UserForm(FlaskForm):
    username = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EventForm(FlaskForm):
    event_id = SelectField('Which event are you training for?')
    submit = SubmitField('Submit')


# class PlanForm(FlaskForm):
#     event = SelectField('Which event are you training for?',
#                         default="Edinburgh Marathon Festival 5k")

#     level = SelectField('What is your current ability level?',
#                         choices=LEVELS,
#                         default='Beginner')

#     days = SelectMultipleField('On which days would you like to train?',
#                                choices=DAYS,
#                                default=[1, 3, 5],
#                                coerce=int)

#     submit = SubmitField('Submit')

#     def __init__(self, date):
#         super(PlanForm, self).__init__()
#         # Show future events within 12 months
#         resource_path = os.path.join(basedir, 'events.json')
#         events = open_json(resource_path)

#         self.event.choices = [
#             (event, "{0} ({1})".format(event,
#                                        datetime.strptime(info["date"],
#                                                          '%Y-%m-%d').date().strftime('%d %b %Y')))
#             for (event, info) in events.items()
#             if date < datetime.strptime(info["date"], '%Y-%m-%d').date() < (date + timedelta(weeks=4 * 12))]

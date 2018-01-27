from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, SelectMultipleField, \
    DateField, BooleanField, IntegerField, DecimalField, FieldList, FormField
from wtforms.validators import DataRequired


class PlanForm(FlaskForm):
    event_id = SelectField('Which event are you training for?', coerce=int)
    level = SelectField('What is your current ability level?',
                        choices=[('Beginner', 'Beginner'),
                                 ('Intermediate', 'Intermediate'),
                                 ('Advanced', 'Advanced')
                                 ],
                        default='Beginner')
    days = SelectMultipleField('On which days would you like to train?',
                               choices=[(0, 'Monday'),
                                        (1, 'Tuesday'),
                                        (2, 'Wednesday'),
                                        (3, 'Thursday'),
                                        (4, 'Friday'),
                                        (5, 'Saturday'),
                                        (6, 'Sunday')],
                               default=[1, 3, 5],
                               coerce=int)
    submit = SubmitField('Submit')


class EventForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    distance = SelectField('Distance',
                           choices=[('5k', '5k'),
                                    ('10k', '10k'),
                                    ('Half Marathon', 'Half Marathon'),
                                    ('Marathon', 'Marathon'),
                                    ])
    date = DateField('Date', validators=[DataRequired()])
    submit = SubmitField('Submit')


class ExcerciseForm(FlaskForm):
    description = StringField('Exercise description',
                              validators=[DataRequired()])
    duration = DecimalField('Duration', validators=[DataRequired()])


class WorkoutsetForm(FlaskForm):
    reps = IntegerField('Reps', validators=[DataRequired()])
    exercises = FieldList(FormField(ExcerciseForm), min_entries=2)


class WorkoutForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    category = SelectField('Category',
                           choices=[('easy', 'Run Easy'),
                                    ('intervals', 'Intervals'),
                                    ('hillsprints', 'Hillsprints'),
                                    ('crosstrain', 'Cross Train'),
                                    ],
                           validators=[DataRequired()])
    rest = BooleanField('Rest')
    workoutsets = FieldList(FormField(WorkoutsetForm), min_entries=2)
    submit = SubmitField('Submit')

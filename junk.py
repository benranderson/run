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

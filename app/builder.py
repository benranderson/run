from datetime import datetime, date, timedelta


def rest_week(week, plan_length):
    '''
    int -> boolean

    Determine if current week is a rest week.

    Plans work on a 4 week block, with every 4th week being an easier week.
    Runner has at least 2 weeks, and a maximum of 5 weeks before they get an
    easier week.  So if they were on a 6 week plan they would only have an
    easier week on race week.

    Returns True if rest week and False if progression week.
    '''
    build_up = plan_length % 4
    if week <= build_up < 3:
        return False
    elif (week - build_up) % 4 == 0:
        return True
    else:
        return False


def reps_or_duration(plan_length, plan_week, workout_week, start, step, maximum,
                     interval):
    # convert boolean returned from function to 1 or 0
    rest = int(rest_week(plan_week, plan_length))
    result = start + (int(workout_week / interval) - rest) * step
    return min(result, maximum - rest * step)


def progression_start_date(plan_start_date, day):
    '''
    Return date of workout progression.
    '''
    return plan_start_date + timedelta(weeks=1) - \
        timedelta(days=plan_start_date.weekday()) + timedelta(days=day)


def weeks_between_dates(start_date, end_date):
    '''
    Return the number of weeks between two dates
    '''
    monday1 = (start_date - timedelta(days=start_date.weekday()))
    monday2 = (end_date - timedelta(days=end_date.weekday()))
    return int((monday2 - monday1).days / 7)

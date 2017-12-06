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

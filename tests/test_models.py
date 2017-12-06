import pytest
from datetime import date
from app.models import Event, Plan, FiveK


def test_event():
    e = Event(name='EMF', distance='5k', date=date(2018, 1, 1))
    assert '5k' in repr(e)


def test_plan():
    p = Plan(level='Beginner')
    assert 'Beginner' in repr(p)


def test_plan_weeks_between_dates():
    p = Plan()
    assert p.weeks_between_dates(date(2018, 1, 1), date(2018, 2, 1)) == 4


@pytest.fixture()
def event():
    return Event(name='EMF', distance='5k', date=date(2018, 1, 1))


def test_plan_length(event):
    p = Plan(level='Beginner', event=event, start_date=date(2017, 12, 1))
    assert p.length == 5


def test_plan_create(event):
    p = Plan(level='Beginner', event=event, start_date=date(2017, 12, 1))
    p.create(days=[0, 1, 2])

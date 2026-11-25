from datetime import date, timedelta
from fitness.validation import validate, warnings_for
from fitness.models import Session


def test_valid_session_and_calorie_estimate():
    values, error = validate(date.today().isoformat(), "Walking", 30, 2, "", "test")
    assert error is None
    assert values["duration_min"] == 30
    assert values["calories"] > 0


def test_future_date_rejected():
    future = (date.today() + timedelta(days=1)).isoformat()
    values, error = validate(future, "Walking", 30, 2, 100)
    assert values is None
    assert "future" in error.lower()


def test_invalid_activity_rejected():
    values, error = validate(date.today().isoformat(), "Dancing", 30, 2, 100)
    assert values is None
    assert "Activity" in error


def test_zero_duration_rejected():
    values, error = validate(date.today().isoformat(), "Walking", 0, 0, 0)
    assert values is None
    assert "Duration" in error


def test_unrealistic_speed_warning():
    session = Session(1, date.today().isoformat(), "Walking", 30, 10, 100)
    assert any("unrealistic" in warning for warning in warnings_for(session))

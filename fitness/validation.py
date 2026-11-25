from datetime import date, datetime
from .config import ACTIVITIES, LIMITS, WEIGHT_KG
from .models import Session


def _num(v, name, lo, hi, blank_ok=False):
    if v is None or str(v).strip() == "":
        if blank_ok:
            return None
        raise ValueError(f"{name} is required.")
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number.")
    if x != x or not lo <= x <= hi:
        raise ValueError(f"{name} must be between {lo} and {hi}.")
    return round(x, 2)


def validate(d, activity, duration, distance, calories, notes=""):
    """Return (clean_values_dict, error_message). Never raises."""
    try:
        day = datetime.strptime(str(d).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None, "Date must be in YYYY-MM-DD format."
    if day > date.today():
        return None, "Date cannot be in the future."
    if activity not in ACTIVITIES:
        return None, f"Activity must be one of: {', '.join(ACTIVITIES)}."
    try:
        dur = _num(duration, "Duration (min)", *LIMITS["duration"])
        dist = _num(distance, "Distance (km)", *LIMITS["distance"], blank_ok=True) or 0.0
        cal = _num(calories, "Calories", *LIMITS["calories"], blank_ok=True)
    except ValueError as e:
        return None, str(e)
    if cal is None:
        cal = round(ACTIVITIES[activity] * WEIGHT_KG * dur / 60, 1)
    return dict(date=day.isoformat(), activity=activity, duration_min=dur,
                distance_km=dist, calories=cal, notes=str(notes or "").strip()[:200]), None


def warnings_for(s: Session):
    """Threshold / anomaly warnings for one session."""
    w = []
    if s.duration_min > 240:
        w.append("very long session (>4 h)")
    if s.distance_km and s.duration_min:
        speed = s.distance_km / (s.duration_min / 60)
        if s.activity == "Walking" and speed > 9:
            w.append(f"walking speed {speed:.1f} km/h looks unrealistic")
        if s.activity == "Running" and speed > 25:
            w.append(f"running speed {speed:.1f} km/h looks unrealistic")
    if s.calories > 2500:
        w.append("very high calorie burn")
    return w

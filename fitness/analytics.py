from datetime import date, timedelta


def summary(sessions):
    """Aggregate totals, averages, streak, weekly trend. None if no data."""
    if not sessions:
        return None
    n = len(sessions)
    tot_min = sum(s.duration_min for s in sessions)
    km = sum(s.distance_km for s in sessions)
    days = {date.fromisoformat(s.date) for s in sessions}
    today = date.today()
    age = lambda s: (today - date.fromisoformat(s.date)).days
    wk = sum(s.duration_min for s in sessions if age(s) < 7)
    prev = sum(s.duration_min for s in sessions if 7 <= age(s) < 14)
    by_act = {}
    for s in sessions:
        a = by_act.setdefault(s.activity, dict(n=0, min=0, km=0, cal=0))
        a["n"] += 1; a["min"] += s.duration_min; a["km"] += s.distance_km; a["cal"] += s.calories
    cur = today if today in days else today - timedelta(days=1)
    streak = 0
    while cur in days:
        streak += 1
        cur -= timedelta(days=1)
    return dict(n=n, minutes=tot_min, km=km, cal=sum(s.calories for s in sessions),
                avg_min=tot_min / n, avg_km=km / n, active_days=len(days),
                week_min=wk, prev_week_min=prev,
                trend="up" if wk > prev else "down" if wk < prev else "flat",
                streak=streak, by_act=by_act,
                best=max(sessions, key=lambda s: s.duration_min),
                top=max(by_act, key=lambda k: by_act[k]["min"]))


def daily_minutes(sessions, days=30):
    """{date: minutes} for the last `days` days (zeros included)."""
    today = date.today()
    out = {today - timedelta(days=i): 0 for i in range(days - 1, -1, -1)}
    for s in sessions:
        d = date.fromisoformat(s.date)
        if d in out:
            out[d] += s.duration_min
    return out

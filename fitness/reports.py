import csv
from datetime import datetime
from .analytics import summary
from .config import EXPORT_DIR, FIELDS, WEEKLY_GOAL_MIN
from .validation import warnings_for


def export_report(sessions, kind):
    """kind: 'md' | 'txt' | 'csv'. Returns file Path or None if no data."""
    S = summary(sessions)
    if not S:
        return None
    EXPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ss = sorted(sessions, key=lambda s: s.date)
    if kind == "csv":
        p = EXPORT_DIR / f"report_{stamp}.csv"
        with p.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(FIELDS)
            w.writerows([[getattr(s, k) for k in FIELDS] for s in ss])
        return p
    md = kind == "md"
    lines = [("# " if md else "") + "Fitness Activity Summary",
             f"Generated: {datetime.now():%Y-%m-%d %H:%M}", "",
             f"Sessions: {S['n']} | Total: {S['minutes']:.0f} min | Distance: {S['km']:.1f} km "
             f"| Calories: {S['cal']:.0f}",
             f"Average session: {S['avg_min']:.1f} min | Last 7 days: {S['week_min']:.0f} min "
             f"(goal {WEEKLY_GOAL_MIN}) | Trend vs previous week: {S['trend']}", ""]
    if md:
        lines += ["## By activity", "", "| Activity | Sessions | Minutes | Km | Calories |",
                  "|---|---|---|---|---|"]
        lines += [f"| {a} | {v['n']} | {v['min']:.0f} | {v['km']:.1f} | {v['cal']:.0f} |"
                  for a, v in S["by_act"].items()]
    else:
        lines += ["BY ACTIVITY"] + [f"  {a:<10} n={v['n']:<3} {v['min']:.0f} min "
                                    f"{v['km']:.1f} km {v['cal']:.0f} kcal"
                                    for a, v in S["by_act"].items()]
        lines += ["", "AUDIT LOG"]
        for s in ss:
            w = warnings_for(s)
            lines.append(f"  #{s.id} {s.date} {s.activity} {s.duration_min}min "
                         f"{s.distance_km}km {s.calories}kcal" + (f"  WARN: {'; '.join(w)}" if w else ""))
    p = EXPORT_DIR / f"report_{stamp}.{'md' if md else 'txt'}"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p

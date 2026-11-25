"""Matplotlib charts. Each function draws onto a given Figure (GUI-independent)."""
from .config import WEEKLY_GOAL_MIN


def daily_minutes_chart(fig, dm):
    ax = fig.subplots()
    labels = [d.strftime("%d %b") for d in dm]
    ax.bar(labels, list(dm.values()), color="#0d9488")
    ax.axhline(WEEKLY_GOAL_MIN / 7, color="orange", ls="--", label="daily goal avg")
    ax.set_xticks(range(0, len(labels), 5))
    ax.set_xticklabels(labels[::5])
    ax.set_title("Daily active minutes (last 30 days)")
    ax.legend()
    fig.tight_layout()


def activity_pie_chart(fig, by_act):
    ax = fig.subplots()
    ax.pie([v["min"] for v in by_act.values()], labels=list(by_act), autopct="%1.0f%%")
    ax.set_title("Time distribution by activity")
    fig.tight_layout()


def cumulative_distance_chart(fig, sessions):
    ax = fig.subplots()
    ordered = sorted(sessions, key=lambda s: s.date)
    total, cum = 0, []
    for s in ordered:
        total += s.distance_km
        cum.append(total)
    ax.plot(range(len(ordered)), cum, color="#0f766e", marker="o", ms=3)
    step = max(1, len(ordered) // 8)
    idx = list(range(0, len(ordered), step))
    ax.set_xticks(idx)
    ax.set_xticklabels([ordered[i].date for i in idx], rotation=30)
    ax.set_title("Cumulative distance (km)")
    fig.tight_layout()

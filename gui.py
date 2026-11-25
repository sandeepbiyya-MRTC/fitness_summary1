"""NiceGUI interface layer - the only module that imports nicegui."""
from dataclasses import asdict
from datetime import date

from nicegui import ui

from fitness import charts as ch
from fitness.analytics import daily_minutes, summary
from fitness.config import ACTIVITIES, FIELDS, WEEKLY_GOAL_MIN
from fitness.reports import export_report
from fitness.storage import Store
from fitness.validation import validate, warnings_for

store = Store()
tables = {}


def refresh_all():
    dashboard.refresh()
    charts_panel.refresh()
    if "records" in tables:
        tables["records"].refresh()


def stat_card(label, value, icon, sub=""):
    with ui.card().classes("min-w-[170px] flex-1"):
        with ui.row().classes("items-center gap-2"):
            ui.icon(icon, size="md").classes("text-teal-600")
            ui.label(label).classes("text-sm text-gray-500")
        ui.label(value).classes("text-2xl font-bold")
        if sub:
            ui.label(sub).classes("text-xs text-gray-400")


@ui.refreshable
def dashboard():
    S = summary(store.sessions)
    if not S:
        ui.label("No sessions yet - add one or import a CSV.").classes("text-gray-500")
        return
    with ui.row().classes("w-full gap-4"):
        stat_card("Sessions", str(S["n"]), "fitness_center", f"{S['active_days']} active days")
        stat_card("Total time", f"{S['minutes'] / 60:.1f} h", "timer", f"avg {S['avg_min']:.0f} min")
        stat_card("Distance", f"{S['km']:.1f} km", "directions_walk", f"avg {S['avg_km']:.1f} km")
        stat_card("Calories", f"{S['cal']:,.0f}", "local_fire_department")
        stat_card("Streak", f"{S['streak']} d", "bolt", f"top: {S['top']}")
    with ui.card().classes("w-full"):
        ui.label(f"Weekly goal: {S['week_min']:.0f} / {WEEKLY_GOAL_MIN} min "
                 f"(trend {S['trend']} vs previous week: {S['prev_week_min']:.0f} min)").classes("font-medium")
        ui.linear_progress(value=min(S["week_min"] / WEEKLY_GOAL_MIN, 1),
                           show_value=False).props("size=14px color=teal")
        if S["week_min"] < WEEKLY_GOAL_MIN:
            ui.label(f"Warning: {WEEKLY_GOAL_MIN - S['week_min']:.0f} min short of the weekly goal."
                     ).classes("text-orange-600")
        else:
            ui.label("Goal reached - nice work!").classes("text-green-600")
    flagged = [(s, warnings_for(s)) for s in store.sessions if warnings_for(s)]
    if flagged:
        with ui.card().classes("w-full bg-orange-50"):
            ui.label(f"Anomaly warnings ({len(flagged)})").classes("font-bold text-orange-700")
            for s, w in flagged[-5:]:
                ui.label(f"#{s.id} {s.date} {s.activity}: {'; '.join(w)}").classes("text-sm")
    with ui.card().classes("w-full"):
        ui.label("By activity").classes("font-bold")
        ui.table(columns=[{"name": k, "label": k.title(), "field": k, "align": "left"}
                          for k in ("activity", "sessions", "minutes", "km", "calories")],
                 rows=[dict(activity=a, sessions=v["n"], minutes=round(v["min"]),
                            km=round(v["km"], 1), calories=round(v["cal"]))
                       for a, v in sorted(S["by_act"].items(), key=lambda kv: -kv[1]["min"])]
                 ).classes("w-full").props("flat dense")


@ui.refreshable
def charts_panel():
    if not store.sessions:
        ui.label("Nothing to plot yet.").classes("text-gray-500")
        return
    S = summary(store.sessions)
    with ui.row().classes("w-full gap-4"):
        with ui.card().classes("flex-1 min-w-[420px]"):
            with ui.matplotlib(figsize=(6, 3.4)).figure as fig:
                ch.daily_minutes_chart(fig, daily_minutes(store.sessions))
        with ui.card().classes("flex-1 min-w-[420px]"):
            with ui.matplotlib(figsize=(6, 3.4)).figure as fig:
                ch.activity_pie_chart(fig, S["by_act"])
    with ui.card().classes("w-full"):
        with ui.matplotlib(figsize=(12, 3.2)).figure as fig:
            ch.cumulative_distance_chart(fig, store.sessions)


def build_add_tab():
    with ui.card().classes("w-[460px]"):
        ui.label("Record a session").classes("text-lg font-bold")
        d = ui.input("Date (YYYY-MM-DD)", value=date.today().isoformat()).props("outlined dense").classes("w-full")
        a = ui.select(list(ACTIVITIES), value="Walking", label="Activity").props("outlined dense").classes("w-full")
        dur = ui.input("Duration (minutes)").props("outlined dense").classes("w-full")
        dist = ui.input("Distance (km, optional)").props("outlined dense").classes("w-full")
        cal = ui.input("Calories (optional - estimated if blank)").props("outlined dense").classes("w-full")
        notes = ui.input("Notes").props("outlined dense").classes("w-full")

        def submit():
            v, err = validate(d.value, a.value, dur.value, dist.value, cal.value, notes.value)
            if err:
                ui.notify(err, type="negative")
                return
            s = store.add(**v)
            for w in warnings_for(s):
                ui.notify(f"Warning: {w}", type="warning")
            ui.notify(f"Saved session #{s.id} ({s.calories:.0f} kcal)", type="positive")
            dur.value = dist.value = cal.value = notes.value = ""
            refresh_all()
        ui.button("Save session", icon="save", on_click=submit)


def build_records_tab():
    state = {"q": "", "cat": "All"}

    @ui.refreshable
    def table():
        q = state["q"].lower()
        rows = [asdict(s) for s in sorted(store.sessions, key=lambda s: (s.date, s.id), reverse=True)
                if (state["cat"] == "All" or s.activity == state["cat"])
                and (not q or q in f"{s.date} {s.activity} {s.notes}".lower())]
        cols = [{"name": k, "label": k.replace("_", " ").title(), "field": k,
                 "sortable": True, "align": "left"} for k in FIELDS]
        t = ui.table(columns=cols, rows=rows, row_key="id", selection="multiple",
                     pagination=10).classes("w-full")

        def delete():
            ids = {r["id"] for r in t.selected}
            if not ids:
                ui.notify("Select rows first.", type="warning")
                return
            store.delete(ids)
            refresh_all()
            ui.notify(f"Deleted {len(ids)} record(s).")
        ui.button("Delete selected", icon="delete", color="red", on_click=delete)
        ui.label(f"{len(rows)} record(s) shown").classes("text-xs text-gray-500")

    def set_q(e):
        state["q"] = e.value or ""
        table.refresh()

    def set_cat(e):
        state["cat"] = e.value
        table.refresh()
    with ui.row().classes("items-center gap-4"):
        ui.input("Search keyword (date, activity, notes)", on_change=set_q
                 ).props("clearable outlined dense").classes("w-80")
        ui.select(["All", *ACTIVITIES], value="All", label="Category", on_change=set_cat
                  ).props("outlined dense").classes("w-40")
    table()
    return table


def build_io_tab():
    with ui.row().classes("gap-6 items-start"):
        with ui.card().classes("w-[420px]"):
            ui.label("Bulk import (CSV)").classes("text-lg font-bold")
            ui.label("Header needs: date, activity, duration_min "
                     "(+ optional distance_km, calories, notes)").classes("text-xs text-gray-500")
            log = ui.log(max_lines=200).classes("w-full h-40")

            async def on_upload(e):
                f = getattr(e, "file", None)          # NiceGUI 3.x
                raw = await f.read() if f is not None else e.content.read()   # 1.x / 2.x
                ok, errs = store.import_csv(raw.decode("utf-8-sig", errors="replace"))
                log.clear()
                log.push(f"Imported {ok} row(s), {len(errs)} rejected.")
                for er in errs:
                    log.push(er)
                ui.notify(f"Imported {ok} rows", type="positive" if ok else "warning")
                refresh_all()
            ui.upload(on_upload=on_upload, auto_upload=True, label="Drop CSV here"
                      ).props("accept=.csv flat").classes("w-full")
        with ui.card().classes("w-[320px]"):
            ui.label("Export report").classes("text-lg font-bold")
            for kind, label in (("md", "Markdown"), ("txt", "Plain-text audit log"), ("csv", "CSV")):
                def go(k=kind):
                    p = export_report(store.sessions, k)
                    if p:
                        ui.download(str(p))
                    else:
                        ui.notify("No data to export.", type="warning")
                ui.button(label, icon="download", on_click=go).props("outline").classes("w-full")


@ui.page("/")
def index():
    ui.colors(primary="#0d9488")
    with ui.header().classes("items-center gap-3"):
        ui.icon("directions_run", size="lg")
        ui.label("Fitness Activity Summary").classes("text-xl font-bold")
        ui.label("record sessions - track totals - see trends").classes("text-sm opacity-80")
    with ui.tabs().classes("w-full") as tabs:
        t = [ui.tab(n, icon=i) for n, i in (("Dashboard", "dashboard"), ("Add session", "add_circle"),
                                             ("Records", "search"), ("Charts", "insert_chart"),
                                             ("Import / Export", "import_export"))]
    with ui.tab_panels(tabs, value=t[0]).classes("w-full"):
        with ui.tab_panel(t[0]):
            dashboard()
        with ui.tab_panel(t[1]):
            build_add_tab()
        with ui.tab_panel(t[2]):
            tables["records"] = build_records_tab()
        with ui.tab_panel(t[3]):
            charts_panel()
        with ui.tab_panel(t[4]):
            build_io_tab()
\n\nif __name__ in {'__main__', '__mp_main__'}:\n    ui.run(title='Fitness Activity Summary', reload=False, show=True)\n
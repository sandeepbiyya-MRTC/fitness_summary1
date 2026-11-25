"""Command-line entry point: python main.py"""
import argparse
import csv
import logging
from datetime import date

from fitness.analytics import summary
from fitness.config import ACTIVITIES, EXPORT_DIR, FIELDS
from fitness.logging_config import configure_logging
from fitness.reports import export_report
from fitness.storage import Store
from fitness.validation import validate, warnings_for

logger = logging.getLogger(__name__)


def print_sessions(sessions):
    if not sessions:
        print("No fitness sessions recorded yet.")
        return
    print(f"{'ID':>4}  {'DATE':10}  {'ACTIVITY':10} {'MIN':>6} {'KM':>8} {'KCAL':>7}")
    print("-" * 57)
    for s in sorted(sessions, key=lambda item: (item.date, item.id), reverse=True):
        print(f"{s.id:>4}  {s.date:10}  {s.activity:10} {s.duration_min:6.1f} "
              f"{s.distance_km:8.2f} {s.calories:7.1f}")
        for warning in warnings_for(s):
            print(f"      ! {warning}")


def run_cli():
    configure_logging()
    store = Store()
    parser = argparse.ArgumentParser(description="Fitness Activity Summary CLI")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("summary", help="show totals and weekly progress")
    sub.add_parser("list", help="list saved sessions")
    add = sub.add_parser("add", help="record a fitness session")
    add.add_argument("--date", default=date.today().isoformat())
    add.add_argument("--activity", required=True, choices=sorted(ACTIVITIES))
    add.add_argument("--duration", required=True, type=float, help="minutes")
    add.add_argument("--distance", type=float, default=0, help="kilometres")
    add.add_argument("--calories", type=float, default=None)
    add.add_argument("--notes", default="")
    delete = sub.add_parser("delete", help="delete a session by ID")
    delete.add_argument("id", type=int)
    imp = sub.add_parser("import", help="import a CSV file")
    imp.add_argument("file")
    exp = sub.add_parser("export", help="export md, txt or csv report")
    exp.add_argument("--format", choices=("md", "txt", "csv"), default="md")
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
    elif args.command == "list":
        print_sessions(store.sessions)
    elif args.command == "summary":
        result = summary(store.sessions)
        if not result:
            print("No data available. Add a session or import a CSV file.")
        else:
            print("FITNESS ACTIVITY SUMMARY")
            print(f"Sessions: {result['n']} | Active days: {result['active_days']}")
            print(f"Total time: {result['minutes']:.0f} min | Distance: {result['km']:.1f} km")
            print(f"Calories: {result['cal']:.0f} | Average session: {result['avg_min']:.1f} min")
            print(f"This week: {result['week_min']:.0f}/150 min | Trend: {result['trend']}")
            print(f"Current streak: {result['streak']} day(s) | Top activity: {result['top']}")
    elif args.command == "add":
        values, error = validate(args.date, args.activity, args.duration, args.distance,
                                 args.calories, args.notes)
        if error:
            parser.error(error)
        session = store.add(**values)
        print(f"Saved session #{session.id}.")
        for warning in warnings_for(session):
            print(f"Warning: {warning}")
    elif args.command == "delete":
        if not any(s.id == args.id for s in store.sessions):
            parser.error(f"No session with ID {args.id}")
        store.delete({args.id})
        print(f"Deleted session #{args.id}.")
    elif args.command == "import":
        try:
            with open(args.file, encoding="utf-8-sig") as source:
                imported, errors = store.import_csv(source.read())
        except OSError as exc:
            parser.error(str(exc))
        print(f"Imported {imported}; rejected {len(errors)}.")
        for error in errors:
            print(error)
    elif args.command == "export":
        path = export_report(store.sessions, args.format)
        print(f"Report saved: {path}" if path else "No data to export.")


if __name__ == "__main__":
    run_cli()

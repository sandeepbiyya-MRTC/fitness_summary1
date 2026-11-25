# Fitness Activity Summary

A Python fitness-session tracker with a **CLI-first workflow**, optional NiceGUI
dashboard, analytics, anomaly warnings, CSV import, and Markdown/text/CSV reports.

## Setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## Command-line interface (default)

Run commands from this folder:

```bash
python main.py
python main.py add --activity Walking --duration 30 --distance 2
python main.py list
python main.py summary
python main.py import sample_data/sample_sessions.csv
python main.py export --format md
python main.py delete 1
```

Dates use `YYYY-MM-DD`. Supported activities: Walking, Running, Cycling,
Swimming, Hiking, Yoga, and Gym. Calories are estimated when omitted.
Validation rejects future dates, unsupported activities, and out-of-range values.

## Optional Web GUI

Install the same requirements, then run:

```bash
python gui.py
```

The GUI retains the dashboard, charts, records, CSV import, and report export.

## Storage, logging, and recovery

Session records are stored in `data/sessions.db` using SQLite transactions,
constraints, and a date index. If the database is new and `data/sessions.json`
exists, the application imports the legacy JSON records without deleting the
original file. Logs are written to `logs/fitness_app.log` with rotation.

## Tests

```bash
pytest -q
```

Tests cover validation boundaries, anomaly detection, SQLite persistence,
deletion, and CSV import error handling.

## Project structure

- `main.py` — CLI entry point
- `gui.py` — optional NiceGUI interface
- `fitness/` — models, validation, SQLite storage, analytics, charts, reports
- `tests/` — automated pytest suite
- `data/` — SQLite database and legacy JSON/sample data
- `sample_data/` — CSV import examples
- `exports/` — generated reports
- `logs/` — rotating application logs

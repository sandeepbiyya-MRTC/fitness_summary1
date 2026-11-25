from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA_FILE = BASE / "data" / "sessions.json"  # legacy import source
DATABASE_FILE = BASE / "data" / "sessions.db"
EXPORT_DIR = BASE / "exports"
LOG_DIR = BASE / "logs"

ACTIVITIES = {"Walking": 3.5, "Running": 9.0, "Cycling": 7.5, "Swimming": 8.0,
              "Hiking": 6.0, "Yoga": 2.5, "Gym": 5.0}
WEIGHT_KG = 70
WEEKLY_GOAL_MIN = 150
LIMITS = {"duration": (1, 600), "distance": (0, 200), "calories": (0, 5000)}
FIELDS = ["id", "date", "activity", "duration_min", "distance_km", "calories", "notes"]

from dataclasses import dataclass


@dataclass
class Session:
    id: int
    date: str            # YYYY-MM-DD
    activity: str
    duration_min: float
    distance_km: float
    calories: float
    notes: str = ""

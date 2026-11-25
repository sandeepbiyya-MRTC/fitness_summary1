from datetime import date
from fitness.storage import Store


def test_add_load_delete_round_trip(tmp_path):
    db = tmp_path / "test.db"
    store = Store(db)
    session = store.add(date=date.today().isoformat(), activity="Walking",
                        duration_min=30, distance_km=2, calories=100, notes="unit test")
    assert session.id == 1
    reloaded = Store(db)
    assert len(reloaded.sessions) == 1
    assert reloaded.sessions[0].notes == "unit test"
    reloaded.delete({1})
    assert Store(db).sessions == []


def test_csv_import_accepts_valid_and_rejects_bad_row(tmp_path):
    store = Store(tmp_path / "import.db")
    data = ("date,activity,duration_min,distance_km,calories,notes\n"
            f"{date.today().isoformat()},Walking,30,2,100,valid\n"
            "2099-01-01,Walking,30,2,100,future\n")
    count, errors = store.import_csv(data)
    assert count == 1
    assert len(errors) == 1
    assert len(Store(tmp_path / "import.db").sessions) == 1

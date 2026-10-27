"""Low-intake alert rule: last 3 recorded meals under 50% -> alert. Missing is skipped, not 0%."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.alerts import low_streak, meal_records, resident_alerts  # noqa: E402


def test_three_low_alerts():
    assert low_streak([30, 40, 45])


def test_two_low_one_ok_no_alert():
    assert not low_streak([30, 40, 80])
    assert not low_streak([80, 30, 40])  # only the last 3 count, and the ok one is among them


def test_missing_is_skipped_not_zero():
    assert low_streak([30, None, 40, 45])  # low, missing, low, low -> alert on the 3 recorded
    assert not low_streak([30, None, 40])  # only 2 recorded


def test_empty_no_alert():
    assert not low_streak([])
    assert not low_streak([None, None, None])


def _scan(rid, t, meal, phase, pct, status="ok"):
    return {"resident_id": rid, "time": t, "meal": meal, "phase": phase, "status": status,
            "total_pct_eaten": pct, "kcal": 1, "protein_g": 1}


def test_records_from_scans():
    scans = [
        _scan("R02", "2026-10-26T12:00:00", "lunch", "after", 30),
        _scan("R02", "2026-10-26T17:00:00", "dinner", "after", 40),
        _scan("R02", "2026-10-27T12:00:00", "lunch", "before", None),  # never scanned after = missing
        _scan("R02", "2026-10-27T17:00:00", "dinner", "after", 20),
        _scan(None, "2026-10-27T17:05:00", None, "before", None, status="no_qr"),
    ]
    recs = meal_records(scans)
    assert [r["pct"] for r in recs] == [30, 40, None, 20]
    out = resident_alerts(recs, [{"id": "R02", "name": "John D.", "room": "110"}])
    assert len(out) == 1 and [m["pct"] for m in out[0]["meals"]] == [30, 40, 20]

"""Dashboard insights: protein vs served, items a resident keeps leaving, food that comes back."""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.insights import day_nutrition, kitchen_waste, left_items, protein_on_track  # noqa: E402

MENU = {"chicken": {"protein_g": 35, "cost_usd": 1.0}, "rice": {"protein_g": 2, "cost_usd": 0.1}}


def _after(rid, t, meal, items, phase="after", status="ok"):
    return {"resident_id": rid, "time": t, "meal": meal, "phase": phase, "status": status,
            "items": [{"name": n, "pct_eaten": p, "kcal": k, "protein_g": g} for n, p, k, g in items]}


def test_day_nutrition_uses_latest_after_per_meal():
    scans = [_after("R01", "2026-10-28T08:00:00", "breakfast", [("chicken", 50, 95, 17.5)]),
             _after("R01", "2026-10-28T08:30:00", "breakfast", [("chicken", 100, 190, 35)]),  # redo wins
             _after("R01", "2026-10-28T12:00:00", "lunch", [("rice", 50, 50, 1)]),
             _after("R01", "2026-10-28T12:00:00", "lunch", [("rice", 0, 0, 0)], phase="before"),
             _after("R02", "2026-10-28T12:00:00", "lunch", [("rice", 100, 100, 2)])]
    d = day_nutrition(scans, MENU, "R01", "2026-10-28")
    assert d == {"kcal": 240, "protein_g": 36, "protein_served_g": 37, "meals": 2}
    assert protein_on_track(d) is True
    assert protein_on_track(day_nutrition(scans, MENU, "R01", "2026-10-27")) is None


def test_protein_off_track():
    assert protein_on_track({"protein_g": 10, "protein_served_g": 35, "meals": 1}) is False


def test_left_items_threshold():
    def meals(pcts):
        return [_after("R02", f"2026-10-{20 + i}T12:00:00", "lunch", [("chicken", p, 0, 0), ("rice", 90, 0, 0)])
                for i, p in enumerate(pcts)]
    assert left_items(meals([10, 20, 80, 30, 90, 40]), "R02") == [{"name": "chicken", "left": 4, "served": 6}]
    assert left_items(meals([10, 20, 80, 90, 90, 40]), "R02") == []  # only 3 of 6
    assert left_items(meals([10, 10, 10, 10, 90, 90, 90, 90]), "R02") == []  # only the last 6 count


def test_kitchen_waste_dollars():
    scans = [_after("R01", "2026-10-28T12:00:00", "lunch", [("chicken", 50, 0, 0), ("rice", 100, 0, 0)]),
             _after("R02", "2026-10-27T12:00:00", "lunch", [("chicken", 0, 0, 0)]),
             _after("R03", "2026-10-01T12:00:00", "lunch", [("chicken", 0, 0, 0)])]  # outside 7 days
    w = kitchen_waste(scans, MENU, date(2026, 10, 28))
    assert w[0] == {"name": "chicken", "served": 2, "pct_left": 75.0, "usd": 1.5}
    assert w[1] == {"name": "rice", "served": 1, "pct_left": 0.0, "usd": 0.0}

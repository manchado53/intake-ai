"""Seed SYNTHETIC meal history for the 2 days before profiles.json `date` (lunch + dinner).

R02 John D. eats under 50% at his last 3 meals so the RD alert shows before any live scan;
everyone else eats 60-100%. Idempotent: fixed scan_ids ("seed-..."), INSERT OR IGNORE.
Rows are stored with synthetic=1 and station_id "synthetic-seed".

Run (repo root): .venv-app/Scripts/python -m app.seed
"""
import random
from datetime import date, timedelta

from app import store

MEAL_HOUR = {"breakfast": "08:00", "lunch": "12:15", "dinner": "17:30"}
CHART_BINS = (0, 25, 50, 75, 100)


def chart_bin(pct: float) -> int:
    return min(CHART_BINS, key=lambda b: abs(b - pct))


def build_scans(profiles: dict) -> list[dict]:
    rng = random.Random(42)
    today = date.fromisoformat(profiles["date"])
    menu = profiles["menu_items"]
    scans = []
    for r in profiles["residents"]:
        slots = [(today - timedelta(days=d), meal)
                 for d in (2, 1) for meal in ("breakfast", "lunch", "dinner") if meal in r["meals"]]
        for i, (day, meal) in enumerate(slots):
            low = r["id"] == "R02" and i >= len(slots) - 3
            items, before_sum, after_sum = [], 0.0, 0.0
            for name in r["meals"][meal]:
                pct = rng.uniform(15, 45) if low else rng.uniform(60, 100)
                before = round(rng.uniform(0.06, 0.18), 3)
                after = round(before * (1 - pct / 100), 3)
                pct = round(100 * (1 - after / before), 1)
                before_sum += before
                after_sum += after
                items.append({"name": name, "before_frac": before, "after_frac": after, "pct_eaten": pct,
                              "kcal": round(pct / 100 * menu[name]["kcal"], 1),
                              "protein_g": round(pct / 100 * menu[name]["protein_g"], 1)})
            total = round(100 * (1 - after_sum / before_sum), 1)
            t = f"{day.isoformat()}T{MEAL_HOUR[meal]}:00"
            scans.append({
                "scan_id": f"seed-{day.isoformat()}-{r['id']}-{meal}-after",
                "station_id": "synthetic-seed", "time": t, "resident_id": r["id"], "meal": meal,
                "phase": "after", "status": "ok", "needs_review": False, "review_reasons": [],
                "items": items, "total_pct_eaten": total, "chart_bin": chart_bin(total),
                "kcal": round(sum(x["kcal"] for x in items), 1),
                "protein_g": round(sum(x["protein_g"] for x in items), 1),
                "annotated_jpg_b64": None, "synthetic": True,
            })
    return scans


def seed(db: str | None = None) -> int:
    """Insert the synthetic history; returns how many rows were new."""
    con = store.connect(db)
    try:
        return sum(store.insert_scan(con, s, synthetic=True) for s in build_scans(store.load_profiles()))
    finally:
        con.close()


if __name__ == "__main__":
    n = seed()
    print(f"seeded {n} new synthetic scans into {store.db_path()}")

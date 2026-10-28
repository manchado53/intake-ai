"""Seed SYNTHETIC meal history: the 7 days before profiles.json `date` plus that day's breakfast.

Planted patterns (so every dashboard insight has something to show before any live scan):
- R02 John D. leaves the meat (pork chop, chicken, eggs) and eats the starch; his last 3 meals
  are under 50%, so the RD alert shows.
- R03 Rosa M. eats less and less of her protein items over the week.
- Kitchen: pork chop and green beans come back the most.
Everyone else eats 60-100%.

Three of today's lunches (before the demo, so they top the kitchen feed) use REAL recorded meals
(photos + hosted Workflow output in data/raw/demo_photos/, made with workflow/run_hosted.py;
skipped if the folder is missing). Mary R. is left alone for the live scan.
- R05 Helen B.: meal_03 (fish, pasta, carrots), all foods named right.
- R03 Rosa M.: meal_05 (chicken, mashed potatoes, mixed vegetables). CLIP named the chicken
  "mashed potatoes" in the BEFORE photo -> review ("missing_item: chicken").
- R06 Frank P.: meal_02 (pork chop, rice, green beans). Rice named "green beans" -> review.
The missing_item rule lives here only; the station does not flag a missing menu item yet.
The % comes from station/intake.py, the same math the station runs.

Idempotent: fixed scan_ids ("seed-..."), INSERT OR IGNORE.
Rows are stored with synthetic=1 and station_id "synthetic-seed".

Run (repo root): .venv-app/Scripts/python -m app.seed
"""
import base64
import json
import random
from datetime import date, timedelta
from pathlib import Path

from app import store
from station.intake import before_items, compare, group_items

MEAL_HOUR = {"breakfast": "08:00", "lunch": "12:15", "dinner": "17:30"}
CHART_BINS = (0, 25, 50, 75, 100)
DAYS = 7
MEAT = {"pork chop", "chicken", "white fish", "scrambled eggs"}
PROTEIN = MEAT | {"yogurt"}
KITCHEN_LEFT = {"pork chop": (40, 85), "green beans": (30, 80)}  # % eaten range for everyone else
PHOTOS = Path(__file__).resolve().parent.parent / "data" / "raw" / "demo_photos"
REAL = {"R05": "meal_03", "R03": "meal_05", "R06": "meal_02"}  # today's lunch
REAL_TIMES = ("11:15:00", "11:45:00")  # before, after


def chart_bin(pct: float) -> int:
    return min(CHART_BINS, key=lambda b: abs(b - pct))


def item_pct(rng, rid, name, i, n, low):
    """% eaten of one item at slot i of n (oldest first) for this resident."""
    if rid == "R02":
        if low:
            return rng.uniform(5, 25) if name in MEAT else rng.uniform(30, 50)
        return rng.uniform(10, 35) if name in MEAT else rng.uniform(65, 95)
    if rid == "R03" and name in PROTEIN:
        mid = 95 - 50 * i / max(n - 1, 1)  # slides from ~95% to ~45%
        return min(100.0, max(0.0, rng.uniform(mid - 8, mid + 5)))
    return rng.uniform(*KITCHEN_LEFT.get(name, (60, 100)))


def real_meal(r, day, meal, menu_items):
    """Before + after scans from a recorded meal (s0 -> s5), or None if not planted / no photos."""
    src = PHOTOS / REAL.get(r["id"], "-")
    if not (src / "s0_1_color.json").exists():
        return None
    plan = r["meals"][meal]
    shots = {}
    for phase, shot in (("before", "s0_1_color"), ("after", "s5_1_color")):
        est = json.loads((src / f"{shot}.json").read_text(encoding="utf-8"))["estimate"]
        fracs, reasons = group_items(est["items"], plan)
        img = base64.b64encode((src / f"{shot}_annotated.jpg").read_bytes()).decode()
        shots[phase] = (fracs, reasons, img)
    missing = [n for n, f in shots["before"][0].items() if f == 0]
    reasons = shots["before"][1] + shots["after"][1] + [f"missing_item: {n}" for n in missing]
    base = {"station_id": "synthetic-seed", "resident_id": r["id"], "meal": meal, "status": "ok",
            "needs_review": bool(reasons), "review_reasons": reasons, "synthetic": True}
    before = {**base, "scan_id": f"seed-{day.isoformat()}-{r['id']}-{meal}-before", "phase": "before",
              "time": f"{day.isoformat()}T{REAL_TIMES[0]}", "items": before_items(shots["before"][0]),
              "total_pct_eaten": None, "chart_bin": None, "kcal": None, "protein_g": None,
              "annotated_jpg_b64": shots["before"][2], "needs_review": False, "review_reasons": []}  # one card
    after = {**base, "scan_id": f"seed-{day.isoformat()}-{r['id']}-{meal}-after", "phase": "after",
             "time": f"{day.isoformat()}T{REAL_TIMES[1]}", "annotated_jpg_b64": shots["after"][2],
             **compare(shots["before"][0], shots["after"][0], menu_items)}
    return [before, after]


def build_scans(profiles: dict) -> list[dict]:
    rng = random.Random(42)
    today = date.fromisoformat(profiles["date"])
    menu = profiles["menu_items"]
    scans = []
    for r in profiles["residents"]:
        slots = [(today - timedelta(days=d), meal)
                 for d in range(DAYS, 0, -1) for meal in ("breakfast", "lunch", "dinner") if meal in r["meals"]]
        if "breakfast" in r["meals"]:
            slots.append((today, "breakfast"))
        for i, (day, meal) in enumerate(slots):
            low = r["id"] == "R02" and i >= len(slots) - 3
            items, before_sum, after_sum = [], 0.0, 0.0
            for name in r["meals"][meal]:
                pct = item_pct(rng, r["id"], name, i, len(slots), low)
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
        scans += real_meal(r, today, "lunch", menu) or []
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

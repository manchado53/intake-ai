"""Fake kitchen station: POSTs ~10 contract-2 scans (docs/contracts.md §2) to the dashboard API.

Before/after pairs for R01, R03, R04 at lunch, one no_qr, one unknown resident, one duplicate
scan_id (station retry). Each scan carries a small generated JPEG so the photo path is exercised.

Run (repo root): .venv-app/Scripts/python tests/fake_station.py [--url http://localhost:8000] [--delay 1.5]
"""
import argparse
import base64
import io
import json
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PROFILES = json.loads((ROOT / "config" / "profiles.json").read_text(encoding="utf-8"))
MENU = PROFILES["menu_items"]
DAY = PROFILES["date"]
COLORS = {"white fish": "#f2efe6", "pasta": "#f0d27a", "carrots": "#f08a24", "chicken": "#d9b07a",
          "mashed potatoes": "#f5ecd0", "mixed vegetables": "#5aa83c", "pork chop": "#b87a4b",
          "rice": "#fbfbf5", "green beans": "#3f8f3a"}


def jpeg(label: str, fracs: dict) -> str:
    img = Image.new("RGB", (320, 240), "#555b63")
    d = ImageDraw.Draw(img)
    d.ellipse([60, 20, 260, 220], fill="#ffffff", outline="#2a7de1", width=3)
    for i, (name, f) in enumerate(fracs.items()):
        r = max(3, int(140 * f ** 0.5))
        cx, cy = 115 + 50 * (i % 2) + 30 * (i // 2), 90 + 45 * (i // 2)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=COLORS.get(name, "#aa5555"), outline="#e0245e", width=2)
    d.rectangle([0, 0, 320, 18], fill="#000000")
    d.text((6, 3), label, fill="#ffffff")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()


def chart_bin(p):
    return min((0, 25, 50, 75, 100), key=lambda b: abs(b - p))


def pair(rid, hhmm_before, hhmm_after, before, after, review=None):
    """Before + after scans following the contract math."""
    meal = "lunch"
    t0, t1 = f"{DAY}T{hhmm_before}:00", f"{DAY}T{hhmm_after}:00"
    b = {"scan_id": f"{t0}-{rid}-{meal}-before", "station_id": "fake-station", "time": t0,
         "resident_id": rid, "meal": meal, "phase": "before", "status": "ok",
         "needs_review": False, "review_reasons": [],
         "items": [{"name": n, "before_frac": f, "after_frac": None, "pct_eaten": None, "kcal": None,
                    "protein_g": None} for n, f in before.items()],
         "total_pct_eaten": None, "chart_bin": None, "kcal": None, "protein_g": None,
         "annotated_jpg_b64": jpeg(f"BEFORE {rid} {meal}", before)}
    items = []
    for n, f in before.items():
        af = after.get(n, 0.0)
        p = round(min(max(100 * (1 - af / f), 0), 100), 1)
        items.append({"name": n, "before_frac": f, "after_frac": af, "pct_eaten": p,
                      "kcal": round(p / 100 * MENU[n]["kcal"], 1),
                      "protein_g": round(p / 100 * MENU[n]["protein_g"], 1)})
    total = round(min(max(100 * (1 - sum(after.values()) / sum(before.values())), 0), 100), 1)
    a = {**b, "scan_id": f"{t1}-{rid}-{meal}-after", "time": t1, "phase": "after", "items": items,
         "needs_review": bool(review), "review_reasons": review or [],
         "total_pct_eaten": total, "chart_bin": chart_bin(total),
         "kcal": round(sum(i["kcal"] for i in items), 1),
         "protein_g": round(sum(i["protein_g"] for i in items), 1),
         "annotated_jpg_b64": jpeg(f"AFTER {rid} {meal}", after)}
    return b, a


def bad(status, t, rid=None):
    return {"scan_id": f"{DAY}T{t}:00-{status}", "station_id": "fake-station", "time": f"{DAY}T{t}:00",
            "resident_id": rid, "meal": "lunch", "phase": "before", "status": status,
            "needs_review": False, "review_reasons": [], "items": [], "total_pct_eaten": None,
            "chart_bin": None, "kcal": None, "protein_g": None, "annotated_jpg_b64": None}


def scans():
    r01b, r01a = pair("R01", "11:50", "12:40", {"white fish": 0.178, "pasta": 0.164, "carrots": 0.070},
                      {"white fish": 0.036, "pasta": 0.041, "carrots": 0.035})
    r03b, r03a = pair("R03", "11:52", "12:45", {"chicken": 0.190, "mashed potatoes": 0.120, "mixed vegetables": 0.080},
                      {"chicken": 0.110, "mashed potatoes": 0.080, "mixed vegetables": 0.060}, review=["low_clip"])
    r04b, r04a = pair("R04", "11:55", "12:50", {"pork chop": 0.200, "rice": 0.110, "green beans": 0.070},
                      {"green beans": 0.010})
    return [r01b, r03b, bad("no_qr", "11:56"), r04b, r01a, r01a,  # second r01a = duplicate scan_id
            bad("unknown_resident", "12:42", "R99"), r03a, r04a]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between posts (for a live demo)")
    args = ap.parse_args()
    for s in scans():
        r = requests.post(f"{args.url}/api/scan", json=s, timeout=10)
        print(r.status_code, r.json(), s["scan_id"])
        if r.status_code != 200:
            sys.exit(1)
        time.sleep(args.delay)


if __name__ == "__main__":
    main()

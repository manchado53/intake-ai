"""Scanner flow with a stub Workflow (no camera, no network).  Run: pytest tests/test_station_scan.py"""
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
from station.station import Scanner, Screen  # noqa: E402
from station.store import Store  # noqa: E402

CFG = {"STATION_ID": "test"}


class Stub:
    def __init__(self):
        self.items = []

    def run(self, frame, menu, hint=None):
        return {"qr": "R01", "annotated_image": None,
                "estimate": {"plate_found": True, "needs_review": False, "review_reasons": [], "items": self.items}}


def make(tmp_path):
    profiles = json.load(open(os.path.join(ROOT, "config", "profiles.json"), encoding="utf-8"))
    client, screen = Stub(), Screen()
    sc = Scanner(CFG, profiles, client, Store(str(tmp_path / "s.db")), screen, meal_override="lunch",
                 send_photo=False)
    return sc, client, screen, profiles["residents"][0]["meals"]["lunch"]


def test_empty_before_does_not_open_meal(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    b = sc.scan(frame, local_qr="R01")
    assert b["status"] == "error" and "no_food" in b["review_reasons"]
    assert screen.get()["text"].startswith("No food seen")
    client.items = [{"name": m, "area_frac": 0.1} for m in menu]
    assert sc.scan(frame, local_qr="R01")["phase"] == "before"  # the empty one didn't count


def test_after_with_empty_before_does_not_crash(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    sc.store.save_scan({"scan_id": "old", "time": "2026-10-28T11:00:00", "resident_id": "R01", "meal": "lunch",
                        "phase": "before", "status": "ok"}, sc_date(), {})  # left by the old code
    b = sc.scan(frame, local_qr="R01")
    assert b["phase"] == "after" and b["kcal"] is None
    assert "no change" in screen.get()["text"]


def sc_date():
    from datetime import date
    return date.today().isoformat()

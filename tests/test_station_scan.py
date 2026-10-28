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


def test_before_and_after_pictures_side_by_side(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    client.items = [{"name": m, "area_frac": 0.1} for m in menu]
    words, sub, nxt = sc.ready("R01")
    assert words.startswith("Welcome") and nxt == "before" and screen.get()["panels"] == []
    sc.scan(frame, local_qr="R01")
    assert screen.before_jpg and screen.after_jpg is None and screen.get()["panels"] == ["before"]
    before_pic = screen.before_jpg
    screen.owner = None  # card left, someone else came by
    assert sc.ready("R01")[2] == "after"
    assert screen.before_jpg == before_pic  # card back in view: its BEFORE is on screen again
    client.items = [{"name": m, "area_frac": 0.05} for m in menu]
    b = sc.scan(frame + 1, local_qr="R01")
    assert b["phase"] == "after" and screen.before_jpg == before_pic and screen.after_jpg


def test_failed_scan_keeps_pictures(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    sc.scan(frame, local_qr="R01")  # no food -> error
    assert screen.before_jpg is None and sc.store.picture("R01", "lunch", sc_date(), "before") is None


def fill(client, menu, frac):
    client.items = [{"name": m, "area_frac": frac} for m in menu]


def test_phases_cycle_before_after_before(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    phases = []
    for frac in (0.1, 0.05, 0.12, 0.03):  # plate 1 before/after, plate 2 before/after
        fill(client, menu, frac)
        phases.append(sc.scan(frame, local_qr="R01")["phase"])
    assert phases == ["before", "after", "before", "after"]
    assert screen.get()["panels"] == ["before", "after"]
    assert sc.ready("R01")[2] == "before"  # meal closed: next press starts a new plate
    assert screen.get()["panels"] == ["before", "after"]  # same card: result stays up


def test_new_card_clears_old_pictures(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    fill(client, menu, 0.1)
    sc.scan(frame, local_qr="R01")
    sc.ready("R02")
    assert screen.owner == "R02" and screen.get()["panels"] == [] and not screen.can_redo


def test_redo_before_replaces_it(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    fill(client, menu, 0.1)
    first = sc.scan(frame, local_qr="R01")
    fill(client, menu, 0.2)
    again = sc.scan(frame, local_qr="R01", redo=True)
    assert again["phase"] == "before" and again["replaces"] == first["scan_id"]
    assert again["scan_id"] != first["scan_id"]
    assert sc.store.open_before("R01", "lunch", sc_date()) == {m: 0.2 for m in menu}


def test_redo_after_compares_to_same_before(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    fill(client, menu, 0.2)
    sc.scan(frame, local_qr="R01")
    fill(client, menu, 0.2)
    bad = sc.scan(frame, local_qr="R01")  # hand in the way: looks untouched
    fill(client, menu, 0.1)
    good = sc.scan(frame, local_qr="R01", redo=True)
    assert good["phase"] == "after" and good["replaces"] == bad["scan_id"]
    assert good["total_pct_eaten"] == 50


def test_failed_redo_keeps_old_scan(tmp_path):
    sc, client, screen, menu = make(tmp_path)
    frame = np.zeros((48, 64, 3), np.uint8)
    fill(client, menu, 0.1)
    first = sc.scan(frame, local_qr="R01")
    client.items = []
    b = sc.scan(frame, local_qr="R01", redo=True)
    assert b["status"] == "error" and "replaces" not in b
    assert sc.store.last_scan("R01", "lunch", sc_date())["scan_id"] == first["scan_id"]

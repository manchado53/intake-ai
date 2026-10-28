"""Depth on the station: plate-shape math + the area/depth average through a scan (no camera).
Run: pytest tests/test_station_depth.py"""
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
from station import depth as dep  # noqa: E402
from station.intake import compare  # noqa: E402
from station.station import Scanner, Screen  # noqa: E402
from station.store import Store  # noqa: E402

H, W = 480, 640
CX, CY, R = 320, 240, 200
YY, XX = np.mgrid[:H, :W]
PLATE = np.hypot(XX - CX, YY - CY) < R
PILE = (250, 220, 60)  # x, y, radius of a dome of food


def dish(shift=0.0):
    """Table at 380 mm; plate rim 368 mm, centre 15 mm deeper (a shallow dish, like ours)."""
    z = np.full((H, W), 380.0, np.float32)
    d = np.hypot(XX - CX, YY - CY) / R
    z[PLATE] = (368 + 15 * (1 - d ** 2))[PLATE]
    return z + shift


def with_pile(z, height):
    x, y, r = PILE
    d = np.hypot(XX - x, YY - y)
    return np.where(d < r, z - height * (1 - (d / r) ** 2), z).astype(np.float32)


def pile_mask():
    x, y, r = PILE
    return np.hypot(XX - x, YY - y) < r


def poly(mask, name):
    import cv2
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return {"class": name, "points": [{"x": int(p[0][0]), "y": int(p[0][1])} for p in max(cs, key=len)]}


def test_profile_follows_the_dish():
    prof = dep.plate_profile(dish(), PLATE)
    assert prof[0][1] > prof[-1][1] + 10  # centre deeper than the rim


def test_volume_measured_from_dish_not_rim():
    prof = dep.plate_profile(dish(), PLATE)
    v_full = dep.volumes(with_pile(dish(), 30), PLATE, {"rice": pile_mask()}, prof)["rice"]
    v_half = dep.volumes(with_pile(dish(), 15), PLATE, {"rice": pile_mask()}, prof)["rice"]
    assert abs(v_half / v_full - 0.5) < 0.05  # rim floor would read ~0 for food below the rim


def test_volume_ignores_camera_distance_shift():
    prof = dep.plate_profile(dish(), PLATE)
    a = dep.volumes(with_pile(dish(), 30), PLATE, {"rice": pile_mask()}, prof)["rice"]
    b = dep.volumes(with_pile(dish(4.0), 30), PLATE, {"rice": pile_mask()}, prof)["rice"]
    assert abs(a - b) / a < 0.02


def test_masks_from_workflow_polygons():
    out = {"plate": {"predictions": [poly(PLATE, "plate")]}, "foods": {"predictions": [poly(pile_mask(), "rice")]}}
    plate, foods = dep.masks(out, (H, W))
    assert abs(int(plate.sum()) - int(PLATE.sum())) / PLATE.sum() < 0.02
    assert set(foods) == {"rice"}


def test_compare_averages_area_and_depth():
    r = compare({"rice": 0.2}, {"rice": 0.2}, {}, {"rice": 100.0}, {"rice": 50.0})
    it = r["items"][0]
    assert it["pct_area"] == 0 and it["pct_depth"] == 50 and it["pct_eaten"] == 25
    assert r["total_pct_eaten"] == 25 and r["chart_bin"] == 25


def test_compare_without_depth_is_area():
    r = compare({"rice": 0.2}, {"rice": 0.1}, {})
    assert r["items"][0]["pct_eaten"] == 50 and r["items"][0]["pct_depth"] is None


# --- through the scanner --------------------------------------------------------
class FakeDepth:
    def __init__(self):
        self.z = dish()

    def grab(self):
        return self.z


class MaskStub:
    """Workflow stub that also returns the mask outputs the real one sends."""

    def __init__(self, menu):
        self.menu, self.food = menu, True

    def run(self, frame, menu, hint=None):
        foods = [poly(pile_mask(), self.menu[0])] if self.food else []
        area = 0.1 if self.food else 0.0
        return {"annotated_image": None,
                "estimate": {"plate_found": True, "needs_review": False, "review_reasons": [],
                             "items": [{"name": self.menu[0], "area_frac": area}] if self.food else []},
                "foods": {"predictions": foods}, "plate": {"predictions": [poly(PLATE, "plate")]}}


def make(tmp_path, depth=True):
    profiles = json.load(open(os.path.join(ROOT, "config", "profiles.json"), encoding="utf-8"))
    menu = profiles["residents"][0]["meals"]["lunch"]
    cam, client, screen = FakeDepth(), MaskStub(menu), Screen()
    sc = Scanner({"STATION_ID": "t"}, profiles, client, Store(str(tmp_path / "s.db")), screen,
                 meal_override="lunch", send_photo=False, depth=cam if depth else None,
                 profile_path=str(tmp_path / "plate.json"))
    return sc, cam, client, screen, menu


def test_scan_uses_depth_after_empty_plate(tmp_path):
    sc, cam, client, screen, menu = make(tmp_path)
    frame = np.zeros((H, W, 3), np.uint8)
    assert screen.get()["depth"] == "no plate shape"
    client.food = False
    assert sc.empty_plate(frame) and screen.get()["depth"] == "on"
    assert os.path.exists(tmp_path / "plate.json")
    client.food = True
    cam.z = with_pile(dish(), 30)
    b = sc.scan(frame, local_qr="R01")
    assert b["phase"] == "before" and b["method"] == "area+depth"
    cam.z = with_pile(dish(), 15)  # top half eaten; the area stays the same
    a = sc.scan(frame, local_qr="R01")
    it = a["items"][0]
    assert a["method"] == "area+depth" and it["pct_area"] == 0 and 45 < it["pct_depth"] < 55
    assert abs(it["pct_eaten"] - it["pct_depth"] / 2) < 0.2


def test_scan_without_depth_camera_is_area(tmp_path):
    sc, cam, client, screen, menu = make(tmp_path, depth=False)
    frame = np.zeros((H, W, 3), np.uint8)
    assert screen.get()["depth"] == "off" and not sc.empty_plate(frame)
    sc.scan(frame, local_qr="R01")
    a = sc.scan(frame, local_qr="R01")
    assert a["method"] == "area" and a["items"][0]["pct_depth"] is None

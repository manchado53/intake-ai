"""Does depth (volume) track the scale better than top-down area? Offline, from the staged meals.

Same food masks for both methods (the SAM 3 labels exported from Roboflow), so the only difference
is the measurement: area = food pixels; volume = sum over food pixels of (plate surface - depth).
Depth is warped onto the color image with calib/depth_to_color.json. Pixels with no depth reading
get the mean height of the readable food pixels. Shots 1-3 of each state are averaged.

Run: .venv-app/Scripts/python eval/depth_vs_area.py <labels_dir>
     labels_dir holds lab03/, lab04/, lab05/ (+ lab02/), each with _annotations.coco.json
"""
import csv
import json
import sys
from collections import OrderedDict
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
H = np.array(json.load(open(ROOT / "calib/depth_to_color.json"))["homography_depth_to_color"])
MEALS = {"meal_03": "test", "meal_04": "valid", "meal_05": "train", "meal_02": "train"}
# log.csv food_changed -> label attribute
FOOD = {"potatoes": "potato", "pork": None, "rice": "rice", "beans": "beans", "bacon": "bacon",
        "fish": "fish", "pasta": "pasta", "carrots": "carrots", "chicken": "chicken", "veg": "veg"}
BINS = (0, 25, 50, 75, 100)


def chart_bin(p):
    return min(BINS, key=lambda b: (abs(b - p), -b))


def states(meal):
    out = OrderedDict()
    for r in csv.DictReader(open(ROOT / "data/raw/log.csv")):
        if r["meal"] == meal and r["state"] != "empty" and r["state"] not in out:
            out[r["state"]] = (int(r["grams"]), r["food_changed"])
    return out


def measure(coco, meal, state, shot):
    """{food name or 'all': (area_px, volume)} for one shot, or None if missing."""
    name = f"{meal}_{state}_{shot}_color.png"
    ims = [i for i in coco["images"] if i["file_name"] == name]
    zpath = ROOT / f"data/raw/{meal}/{state}_{shot}_depth.png"
    if not ims or not zpath.exists():
        return None
    z = cv2.imread(str(zpath), cv2.IMREAD_UNCHANGED).astype(np.float32)
    z = cv2.warpPerspective(z, H, (640, 480), flags=cv2.INTER_NEAREST)
    plate = np.zeros((480, 640), np.uint8)
    foods = {}
    for a in coco["annotations"]:
        if a["image_id"] != ims[0]["id"]:
            continue
        m = np.zeros((480, 640), np.uint8)
        for s in a["segmentation"]:
            cv2.fillPoly(m, [np.array(s).reshape(-1, 1, 2).astype(np.int32)], 1)
        if a["category_id"] == 2:
            plate |= m
        else:
            key = a.get("attributes", {}).get("food", "all")
            foods[key] = foods.get(key, np.zeros_like(m)) | m
    allfood = np.zeros((480, 640), np.uint8)
    for m in foods.values():
        allfood |= m
    ring = plate.astype(bool) & ~cv2.dilate(allfood, np.ones((15, 15), np.uint8)).astype(bool) & (z > 0)
    if ring.sum() < 200:
        return None
    floor = np.median(z[ring])
    h = np.clip(floor - z, 0, 120)
    out = {}
    for key, m in list(foods.items()) + [("all", allfood)]:
        m = m.astype(bool)
        valid = m & (z > 0)
        mean_h = h[valid].mean() if valid.any() else 0.0
        out[key] = (int(m.sum()), float(h[valid].sum() + mean_h * (m & ~valid).sum()))
    return out


def main():
    labels = Path(sys.argv[1])
    rows = []
    for meal, split in MEALS.items():
        lab = labels / f"lab{meal[-2:]}" / "_annotations.coco.json"
        if not lab.exists():
            continue
        coco = json.load(open(lab))
        st = states(meal)
        names = list(st)
        g = [st[s][0] for s in names]
        meas = {}
        for s in names:
            shots = [m for m in (measure(coco, meal, s, k) for k in (1, 2, 3)) if m]
            if shots:
                keys = set.intersection(*(set(m) for m in shots))
                meas[s] = {k: tuple(np.mean([m[k] for m in shots], axis=0)) for k in keys}
        if names[0] not in meas:
            continue
        a0, v0 = meas[names[0]]["all"]
        print(f"\n{meal} ({split})   state  scale%  area%  volume%")
        for i, s in enumerate(names[1:], 1):
            if s not in meas:
                continue
            a, v = meas[s].get("all", (0, 0))
            true = 100 * (g[0] - g[i]) / (g[0] - g[-1])
            pa = max(0, min(100, 100 * (1 - a / a0)))
            pv = max(0, min(100, 100 * (1 - v / v0)))
            rows.append((meal, split, true, pa, pv))
            print(f"{'':20s}{s:5s}  {true:5.1f}  {pa:5.1f}  {pv:6.1f}   food changed: {st[s][1]}")

    print()
    for split in ("test", "valid", "train", "all"):
        r = [x for x in rows if split == "all" or x[1] == split]
        if not r:
            continue
        for label, idx in (("area  ", 3), ("volume", 4)):
            err = [x[idx] - x[2] for x in r]
            mae = sum(abs(e) for e in err) / len(err)
            bins = 100 * sum(chart_bin(x[idx]) == chart_bin(x[2]) for x in r) / len(r)
            print(f"{split:5s} {label} n={len(r):2d}  MAE {mae:5.1f} pts  bias {sum(err) / len(err):+5.1f}  "
                  f"same 25% bin {bins:3.0f}%")


if __name__ == "__main__":
    main()

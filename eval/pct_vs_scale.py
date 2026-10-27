"""% eaten by the camera (real Workflow + station meal math) vs the kitchen scale.

For each staged meal: state s0 = the "before" scan, every later state = an "after" scan.
Scale truth comes from data/raw/log.csv: one food changes per step, so each item's grams
eaten so far = the sum of the drops logged against it.

Run: .venv-app/Scripts/python eval/pct_vs_scale.py [--url https://serverless.roboflow.com]
Workflow results are cached in data/raw/eval_cache/ (delete it to re-run the Workflow).
"""
import argparse
import csv
import json
import sys
from collections import OrderedDict
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from station.intake import chart_bin, group_items, pct_eaten  # noqa: E402
from station.workflow_client import load_config  # noqa: E402

# split by meal (docs/decisions.md): train meals are optimistic, valid/test are the honest ones
MEALS = {
    "meal_02": ("train", ["pork chop", "rice", "green beans"]),
    "meal_03": ("test", ["white fish", "pasta", "carrots"]),
    "meal_04": ("valid", ["bacon", "rice", "green beans"]),
    "meal_05": ("train", ["chicken", "mashed potatoes", "mixed vegetables"]),
}
# log.csv food_changed -> menu word
FOOD = {"rice": "rice", "pork": "pork chop", "beans": "green beans", "pasta": "pasta",
        "fish": "white fish", "carrots": "carrots", "bacon": "bacon", "potatoes": "mashed potatoes",
        "chicken": "chicken", "veg": "mixed vegetables"}


def states(meal):
    """Ordered {state: (grams, food_changed, color_file)} using shot 1 of each state."""
    out = OrderedDict()
    for r in csv.DictReader(open(ROOT / "data/raw/log.csv")):
        if r["meal"] == meal and r["state"] != "empty" and r["state"] not in out:
            out[r["state"]] = (int(r["grams"]), r["food_changed"], r["color_file"])
    return out


def truth(st, menu):
    """Per state: total % eaten and per-item % eaten from the scale."""
    names = list(st)
    g = [st[s][0] for s in names]
    item_total = {m: 0 for m in menu}
    for i in range(1, len(names)):
        food = FOOD.get(st[names[i]][1])
        if food in item_total:
            item_total[food] += g[i - 1] - g[i]
    out, eaten = {}, {m: 0 for m in menu}
    for i, s in enumerate(names):
        if i:
            food = FOOD.get(st[s][1])
            if food in eaten:
                eaten[food] += g[i - 1] - g[i]
        total = 100 * (g[0] - g[i]) / (g[0] - g[-1])
        out[s] = (total, {m: 100 * eaten[m] / item_total[m] if item_total[m] else None for m in menu})
    return out


def run_workflow(client, spec, path, menu, cache):
    if cache.exists():
        return json.loads(cache.read_text())
    out = client.run_workflow(workspace_name="manchado53", specification=spec,
                              images={"image": cv2.imread(str(path))}, parameters={"menu": menu})
    est = {"qr": out[0].get("qr"), "estimate": out[0]["estimate"]}
    cache.write_text(json.dumps(est))
    return est


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="Inference URL (default: INFERENCE_URL from .env / hosted)")
    args = ap.parse_args()
    from inference_sdk import InferenceHTTPClient
    cfg = load_config()
    client = InferenceHTTPClient(api_url=args.url or cfg["INFERENCE_URL"], api_key=cfg["ROBOFLOW_API_KEY"])
    spec = json.loads((ROOT / "workflow/intake-plate.json").read_text(encoding="utf-8"))
    cache_dir = ROOT / "data/raw/eval_cache"
    cache_dir.mkdir(exist_ok=True)

    rows = []
    for meal, (split, menu) in MEALS.items():
        st = states(meal)
        tr = truth(st, menu)
        before = None
        for s, (grams, food, color) in st.items():
            est = run_workflow(client, spec, ROOT / "data/raw" / color, menu, cache_dir / f"{meal}_{s}.json")
            fracs, reasons = group_items(est["estimate"]["items"], menu)
            if before is None:
                before = fracs
                continue
            cam_total = pct_eaten(sum(before.values()), sum(fracs.values()))
            true_total, true_items = tr[s]
            item_err = [abs(pct_eaten(before[m], fracs[m]) - true_items[m])
                        for m in menu if before[m] and true_items[m] is not None]
            rows.append({"meal": meal, "split": split, "state": s, "true": true_total, "cam": cam_total,
                         "item_mae": sum(item_err) / len(item_err) if item_err else None,
                         "bin_ok": chart_bin(cam_total) == chart_bin(true_total), "reasons": reasons})
            print(f"{meal} {split:5s} {s}: scale {true_total:5.1f}%  camera {cam_total:5.1f}%  "
                  f"err {cam_total - true_total:+6.1f}  item MAE {rows[-1]['item_mae'] or 0:5.1f}  "
                  f"bin {'ok' if rows[-1]['bin_ok'] else 'MISS'} {reasons or ''}", flush=True)

    print()
    for split in ("test", "valid", "train", "all"):
        r = [x for x in rows if split == "all" or x["split"] == split]
        if not r:
            continue
        err = [x["cam"] - x["true"] for x in r]
        mae = sum(abs(e) for e in err) / len(err)
        bias = sum(err) / len(err)
        imae = [x["item_mae"] for x in r if x["item_mae"] is not None]
        bins = 100 * sum(x["bin_ok"] for x in r) / len(r)
        print(f"{split:5s} n={len(r):2d}  total MAE {mae:5.1f} pts  bias {bias:+5.1f}  "
              f"per-item MAE {sum(imae) / len(imae):5.1f}  same 25% bin {bins:3.0f}%")


if __name__ == "__main__":
    main()

"""% eaten by the camera (real Workflow) vs weighed grams, on FLIC's holdout days (never trained on).

Each FLIC dish was weighed before and after eating. Our FLIC conversion cut every tray into one
640x480 crop per plate and logged which course (first / second / side) each crop holds, from FLIC's
own masks. Pairing: the "pre" crop holding course c with the "post" crop holding c; a dish eaten
clean leaves an empty post crop, so leftover empty post crops fill in for courses with no post crop.
Bread is skipped (often off-plate).

Two numbers per dish, both vs grams % eaten = 1 - left_g / full_g:
  camera     = 1 - post food_frac_total / pre food_frac_total   (our Workflow, our model)
  FLIC masks = 1 - left_pixels / full_pixels                    (FLIC's hand masks: the area method
                                                                   with perfect masks)

Run: .venv-app/Scripts/python eval/flic_pct_vs_scale.py <crops_dir> <log.json> <FLIC_grams.csv>
         <holdout_flic.txt> [--url http://localhost:9001]
Workflow results are cached in data/raw/eval_cache_flic/ (delete it to re-run the Workflow).
"""
import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from station.intake import chart_bin, pct_eaten  # noqa: E402
from station.workflow_client import load_config  # noqa: E402

COURSES = {"first": ("First_full_grams", "First_left_grams", "First_full_pixels", "First_left_pixels"),
           "second": ("Second_gull_grams", "Second_left_grams", "Second_gull_pixels", "Second_left_pixels"),
           "side": ("Side_full_grams", "Side_left_grams", "Side_full_pixels", "Side_left_pixels")}


def pairs(log, holdout):
    """{(tray, course): (pre_file, post_file)} for holdout crops, by the course each crop holds."""
    trays = defaultdict(lambda: {"pre": [], "post": []})
    for r in log:
        if "file" in r and r["file"] in holdout and not r.get("drop"):
            trays[r["src"].rsplit("_", 1)[0]][r["tag"]].append(r)
    out = {}
    for tray, t in trays.items():
        empties = [r["file"] for r in t["post"] if not r["courses"]]
        for c in COURSES:
            pre = [r["file"] for r in t["pre"] if r["courses"] == [c]]
            post = [r["file"] for r in t["post"] if r["courses"] == [c]]
            if len(pre) != 1 or len(post) > 1:
                continue
            if not post:
                if not empties:
                    continue
                post = [empties.pop(0)]  # eaten clean: its plate is one of the empty post crops
            out[(tray, c)] = (pre[0], post[0])
    return out


def food_frac(client, spec, crops, name, cache_dir):
    cache = cache_dir / (name[:-4] + ".json")
    if cache.exists():
        return json.loads(cache.read_text())["food_frac_total"]
    out = client.run_workflow(workspace_name="manchado53", specification=spec,
                              images={"image": cv2.imread(str(crops / name))}, parameters={"menu": ["food"]})
    est = out[0]["estimate"]
    cache.write_text(json.dumps({"food_frac_total": est["food_frac_total"], "plate_found": est["plate_found"]}))
    return est["food_frac_total"]


def report(label, rows, key):
    r = [x for x in rows if x[key] is not None]
    if not r:
        return
    err = [x[key] - x["true"] for x in r]
    mae = sum(abs(e) for e in err) / len(err)
    bias = sum(err) / len(err)
    bins = 100 * sum(chart_bin(x[key]) == chart_bin(x["true"]) for x in r) / len(r)
    print(f"  {label:7s} n={len(r):3d}  MAE {mae:5.1f} pts  bias {bias:+5.1f}  same 25% bin {bins:3.0f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("crops")
    ap.add_argument("log")
    ap.add_argument("grams")
    ap.add_argument("holdout")
    ap.add_argument("--url", help="Inference URL (default: INFERENCE_URL from .env)")
    args = ap.parse_args()
    from inference_sdk import InferenceHTTPClient
    cfg = load_config()
    client = InferenceHTTPClient(api_url=args.url or cfg["INFERENCE_URL"], api_key=cfg["ROBOFLOW_API_KEY"])
    spec = json.loads((ROOT / "workflow/intake-plate.json").read_text(encoding="utf-8"))
    cache_dir = ROOT / "data/raw/eval_cache_flic"
    cache_dir.mkdir(parents=True, exist_ok=True)
    crops = Path(args.crops)

    holdout = {ln.strip() for ln in open(args.holdout) if ln.strip() and not ln.startswith("#")}
    grams = {r["Filename_full"][:-8]: r for r in csv.DictReader(open(args.grams))}  # key: date_tray
    rows, skipped = [], 0
    for (tray, c), (pre, post) in sorted(pairs(json.load(open(args.log)), holdout).items()):
        g = grams.get(tray)
        fg, lg, fp, lp = (float(g[k]) for k in COURSES[c]) if g else (0, 0, 0, 0)
        if fg <= 0:
            skipped += 1
            continue
        true = max(0.0, min(100.0, 100 * (1 - lg / fg)))
        cam = pct_eaten(food_frac(client, spec, crops, pre, cache_dir),
                        food_frac(client, spec, crops, post, cache_dir))
        masks = pct_eaten(fp, lp) if fp > 0 else None
        rows.append({"tray": tray, "course": c, "true": true, "cam": cam, "masks": masks})
    print(f"FLIC holdout: {len(rows)} dishes paired ({skipped} with no weight skipped); "
          f"{sum(r['cam'] is None for r in rows)} where the model found no food before eating\n")
    for c in ("all", *COURSES):
        r = [x for x in rows if c == "all" or x["course"] == c]
        print(f"{c}:")
        report("camera", r, "cam")
        report("masks", r, "masks")


if __name__ == "__main__":
    main()

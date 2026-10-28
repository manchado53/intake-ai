# % eaten vs the scale: our meals + FLIC (2026-10-28)

**Question:** how far is the camera's % eaten from the weighed truth? (D9 headline metric)

**Answer:** about **13-16 points on average**, and the camera almost always reads **low** (says
less was eaten than really was). Flat food is close (5-9 points); mounded food and main dishes are
not (18-22 points). On FLIC our model's error is the **same as FLIC's own hand masks**, so the gap
comes from measuring area, not from the segmentation model. That points at depth, not a bigger model.

## Results

Error = camera % eaten - scale % eaten, in percentage points. MAE = average error without the sign.

| Set | Dishes | MAE (pts) | Bias | Same 25% bin |
|---|---|---|---|---|
| **FLIC holdout, our model** (4 canteen days, never trained on) | 126 | **13.5** | -9.6 | 67% |
| FLIC holdout, FLIC hand masks (area method, perfect masks) | 126 | 14.0 | -10.0 | 63% |
| **Our 4 staged meals, our model** | 36 | **16.2** | -16.2 | 39% |
| ↳ meal_03 (fish, pasta, carrots: flat) | 9 | 5.3 | -5.3 | 67% |
| ↳ meal_02 / 04 / 05 (rice, mashed potatoes: mounds) | 27 | 18.6-22.3 | -18.6 to -22.3 | 22-33% |
| Target (D9) | | <= 10 | within +/-5 | >= 80% |

FLIC by course (our model / hand masks): first course (pasta, rice, soup) 9.0 / 10.2,
second (meat, fish) 17.7 / 17.9, side (vegetables, potatoes) 17.8 / 17.1.

## What the numbers say

- **The model is not the bottleneck.** On the same 126 dishes, our masks score as well as FLIC's
  hand-drawn ones (13.5 vs 14.0). A bigger model or more augmentation won't close the gap.
- **Area misses food eaten from the top.** Our worst states are right after rice or mashed potatoes
  were eaten: the camera says 0% while the scale says 10-16% (the pile gets lower, its outline
  doesn't shrink). Meat on FLIC behaves the same (cut, eaten, same footprint).
- **It errs low, which is the safe side.** It under-reports eating, so it can flag a resident too
  often but does not hide a low eater. Staff eyeballing errs high (D9 research).
- **Fully cleared plates are exact** (100% = 100% on all 4 of our meals).

## Next

1. Depth (D7): our first volume try over-corrected (bias +12.9) because depth and color were not
   aligned by the plate. Fix: align by the plate circle + subtract an empty-plate baseline, then
   re-run on these same meals.
2. Score low-eater recall (scale < 50% eaten) on FLIC, the D9 safety metric.

## Limits

- Our meals: 4 meals, 1 plate each, staged by us; "train"/"valid"/"test" refer to the seg model's
  splits (the % math is not trained), so all 4 are fair for this metric.
- FLIC pairing uses the course each crop holds (from FLIC's masks); 126 of ~170 holdout dishes
  could be paired. Two clean-eaten plates on one tray are interchangeable (both empty).
- FLIC grams include sauce and bones the camera can't separate.

## Reproduce

- Our meals: `.venv-app/Scripts/python eval/pct_vs_scale.py --url http://localhost:9001`
  (Workflow results cached in `data/raw/eval_cache/`).
- FLIC: `.venv-app/Scripts/python eval/flic_pct_vs_scale.py <crops_dir> <log.json> <FLIC_grams.csv>
  <holdout_flic.txt> --url http://localhost:9001`. Inputs: the FLIC conversion output
  (`convert_full.py`: crops + `log.json`), `FLIC_grams.csv` from the FLIC release, and
  `intake-train/lists/holdout_flic.txt` on Rosie (days 2024-06-28, 07-08, 07-17, 07-25).
- Both ran the `intake-plate` Workflow (RF-DETR Seg Small v1b) on the Orin's Roboflow Inference 1.3.1.

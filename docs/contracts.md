# Contracts between the pieces

Three JSON shapes connect the Workflow, the station and the dashboard. Each piece is built and
tested against these shapes, with fakes for the others (`plans/workflow-and-app.md`). Change a
shape only by editing this file first.

```
Workflow (Roboflow Inference)  --(1) estimate-->  station  --(2) POST /api/scan-->  dashboard
                                                     ^                                  ^
                                                     +------ (3) config/profiles.json --+
```

Units: `area_frac` = food mask pixels / plate mask pixels (0..~1.5; food can overhang the rim).
Percentages are 0-100 floats. Times are ISO 8601 local time. Meals: `breakfast | lunch | dinner`.

## 1. Workflow output (`intake-plate`)

`run_workflow(...)` returns a list with one dict per image:

```json
{
  "qr": "R01",
  "estimate": {
    "plate_found": true,
    "plate_area_px": 106703,
    "food_frac_total": 0.412,
    "needs_review": false,
    "review_reasons": [],
    "items": [
      {"name": "white fish", "clip_score": 0.81, "det_conf": 0.93, "area_frac": 0.178, "centroid": [0.42, 0.31]},
      {"name": "pasta",      "clip_score": 0.77, "det_conf": 0.95, "area_frac": 0.164, "centroid": [0.63, 0.55]},
      {"name": "carrots",    "clip_score": 0.69, "det_conf": 0.88, "area_frac": 0.070, "centroid": [0.35, 0.66]}
    ]
  },
  "annotated_image": {"type": "base64", "value": "<jpeg base64>"}
}
```
- `qr`: decoded text of the QR card, or `null` if none was found. The card holds only the resident id.
- `items`: one entry per **food blob**. Several blobs can share a name (two fish pieces); the station
  sums them per name. `name` is the best menu word from CLIP among `menu`. `centroid` is
  normalized to the image (x, y in 0..1).
- `needs_review` is true if any of: no plate, a blob with `det_conf < 0.5`, a blob with
  `clip_score < 0.5`. `review_reasons` lists short codes: `no_plate`, `low_det_conf`, `low_clip`.
- Inputs: `image`, `menu` (list of strings: every menu word served today), `confidence` (default 0.5).
- The exact `annotated_image` key layout depends on the visualization block; the station must accept
  both `{"type":"base64","value":...}` and a bare base64 string.

## 2. Station -> dashboard: `POST /api/scan`

Sent once per scan (before **and** after). JSON body:

```json
{
  "scan_id": "2026-10-28T12:05:31-R01-lunch-after",
  "station_id": "orin-kitchen-1",
  "time": "2026-10-28T12:05:31",
  "resident_id": "R01",
  "meal": "lunch",
  "phase": "after",
  "status": "ok",
  "needs_review": false,
  "review_reasons": [],
  "items": [
    {"name": "white fish", "before_frac": 0.178, "after_frac": 0.036, "pct_eaten": 79.8, "kcal": 95.8, "protein_g": 20.7},
    {"name": "pasta",      "before_frac": 0.164, "after_frac": 0.123, "pct_eaten": 25.0, "kcal": 55.0,  "protein_g": 2.0},
    {"name": "carrots",    "before_frac": 0.070, "after_frac": 0.070, "pct_eaten": 0.0,  "kcal": 0.0,   "protein_g": 0.0}
  ],
  "total_pct_eaten": 46.6,
  "chart_bin": 50,
  "kcal": 150.8,
  "protein_g": 22.7,
  "annotated_jpg_b64": "<jpeg base64 or null>"
}
```
- `phase`: `before | after`. On `before`, `after_frac`, `pct_eaten`, `total_pct_eaten`, `chart_bin`,
  `kcal`, `protein_g` are `null`.
- `status`: `ok | no_qr | unknown_resident | no_plate | error`. Non-ok scans are still posted (the
  dashboard shows them in the feed), with `items: []`.
- `pct_eaten = clip(100 * (1 - after_frac / before_frac), 0, 100)`; an item missing after = 100;
  an item with `before_frac == 0` is skipped. `total_pct_eaten` uses the sums over items.
- `chart_bin` = `total_pct_eaten` rounded to the nearest of 0/25/50/75/100.
- `kcal` / `protein_g` per item = `pct_eaten / 100 * portion value` from profiles.
- `scan_id` is unique; the dashboard ignores a repeated `scan_id` (the station retries).
- Response: `200 {"ok": true}`.

## 3. `config/profiles.json` (shared by station and dashboard)

```json
{
  "date": "2026-10-28",
  "meal_times": {"breakfast": ["06:00", "10:00"], "lunch": ["10:00", "15:00"], "dinner": ["15:00", "21:00"]},
  "residents": [
    {"id": "R01", "name": "Mary R.", "room": "104", "diet": "regular",
     "meals": {"lunch": ["white fish", "pasta", "carrots"]}}
  ],
  "menu_items": {
    "white fish": {"portion": "4 oz", "kcal": 120, "protein_g": 26}
  }
}
```
- `meals` maps meal -> the menu words this resident is served today (must exist in `menu_items`).
- The Workflow's `menu` input = every key of `menu_items`.
- Nutrition numbers are our own approximations for the demo; residents are fake.

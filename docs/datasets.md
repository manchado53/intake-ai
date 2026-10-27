# Datasets

What each data source contains, where it is in Roboflow, and its limits.
Label rules and why each set is used: `docs/decisions.md` (D5, D8).
Roboflow project: `manchado53/intake-ai-food-seg` (filter by tag `source:*`).

## Our meals (`source:own`)
Shot with `tools/capture.py`: color + 16-bit depth per shot, 3 shots per step.
Weights in `data/raw/weights.md`; one food changes per step, so each step's weight
difference is that food's grams.

| Meal | Foods | Plate | Photos | Use |
|---|---|---|---|---|
| meal_01 | pasta, chicken (bone-in), roasted peppers | white | 22 | train / valid / test split by meal moment (temporary) |
| meal_02 | rice (dome, eaten from top at s1), pork, green beans | black | 33 | train |

## FLIC (`source:flic`, tags `flic:pre` / `flic:post`)
Food Leftovers In Canteens. Piccoli et al., Applied Sciences 2026, doi 10.3390/app16115465. CC BY 4.0.
- 401 canteen trays, photographed straight down at 65 cm (640x480), before and after eating,
  paired by tray QR code.
- One dish per plate. **Each course was weighed separately, before and after**
  (first course, second course, side, bread) in `FLIC_grams.csv`, with each course's pixel count.
- `FLIC_menu.csv` names the first and second course per day (English + Italian), 21 days.
  **The side dish is not named anywhere**: there is no side column, only its grams. It can only
  be read off the photos.
- Everyone on a given day ate the same dishes, so any test on FLIC must split by **day**.
- In Roboflow: 1,845 single-plate crops (978 before, 867 after), all train. Converted per D8.

## MyFoodRepo (`source:myfoodrepo`)
Food Recognition Benchmark 2022 (v2.0, via Dataset Ninja). License stated as CC BY 4.0 in the
paper; not verified on AIcrowd (login needed).
- Home meal photos, mostly phone, many angled. No before/after, no grams. **Training only.**
- Filtered from ~44k to 987: item-level labels, 2-6 foods, no overlaps, plate found by SAM 3,
  no unlabeled food. Outlines tightened with SAM 3 (median area -2%).
- Original class names kept as hints only; some are wrong.

# Depth with the real plate shape (2026-10-28)

**Question:** can depth fix area's blind spot (food eaten off the top of a pile)? (D7 follow-up)

**Answer:** yes, once height is measured from the plate's real shape. % eaten error on our 4
weighed meals drops from **15.5 points (area) to 7.1 (depth)**, and to **5.8 when area and depth are
averaged**. The average meets all three D9 targets on these meals, but that rule was picked after
seeing the numbers, so it needs new meals to confirm. Not deployed: the demo still uses area.

## What was wrong

The first depth try (2026-10-27) measured food height from the plate **rim** (median depth of the
visible plate around the food). A plate is a shallow dish: on meal_05's cleared plate the rim reads
~345-352 mm from the camera and the centre ~361-365 mm, so the bottom is ~15 mm below the rim. Food
lying below rim level got height 0, so as food was eaten its volume "vanished" early: right after
rice was eaten, depth said 38-50% eaten when the scale said 13-16%.

## Fix

- Build the plate's depth profile (depth vs distance from centre / plate radius) from the meal's
  **last state** (plate cleared, 100% eaten), skipping leftover crumbs.
- In every shot, line the profile up by the **plate circle** (centre + radius from the plate mask)
  and shift it to that shot's visible plate (camera-to-plate distance can differ by a few mm).
- Food height = plate surface at that spot − food surface, clipped to 0-120 mm. Holes (no depth
  reading) get the mean height of the readable food pixels, as before.

No parameter was tuned on the results (one run; same masks as area: the SAM 3 label masks).

## Results (our 4 meals, 36 eaten states, error vs the 1 g scale)

| Method | MAE (pts) | Bias | Same 25% bin |
|---|---|---|---|
| Area (what the demo uses) | 15.5 | -15.5 | 36% |
| Depth, rim floor (first try) | 13.9 | +12.9 | 42% |
| **Depth, plate shape** | **7.1** | +6.9 | 69% |
| **Average of area and depth** | **5.8** | -4.3 | **81%** |
| D9 target | <= 10 | within +/-5 | >= 80% |

By meal: depth is best on piles (rice / mashed potatoes / meat meals: 5.8 pts vs area 18.5), area
is best on the flat meal (meal_03 fish, pasta, carrots: area 6.3, depth 11.1, average 3.6).
Area errs low, depth errs high, so their average cancels most of both.

## Limits

- 4 meals, 36 states, staged by us, one camera, one plate type per meal. The averaging rule was
  chosen after seeing these results; test it on new meals before trusting 5.8.
- The plate profile comes from the meal's own cleared plate. In a home this would be one empty-plate
  scan per plate type (homes use a few standard plates).
- Uses label masks, not the model's; FLIC has no depth, so the 126-dish FLIC check stays area-only.
- Depth noise: dark, shiny or steep food reads as holes (filled with the mean height).

## Next

1. Shoot 2-3 new weighed meals and score area / depth / average without changing the code.
2. If it holds: add depth to the station (Orbbec depth is already on the robot), with one
   empty-plate scan per plate type.

## Reproduce

`.venv-app/Scripts/python eval/depth_vs_area.py <labels_dir>` (labels_dir holds lab02..lab05 COCO
exports of the SAM 3 masks). Prints area, depth (rim floor) and depth (plate shape) per state.

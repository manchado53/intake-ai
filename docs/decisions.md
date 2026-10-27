# Decisions

The big calls, why we made them, and what would make us change them.
One entry per decision, newest last. Hardware choices (camera, height, scale) live in
`docs/setup.md`. When a decision changes, add a new entry that replaces the old one;
don't edit history.

---

## D1 — Model classes: `food-item` + `plate` (2026-10-26)
**Decision:** The segmentation model finds only two things: any food blob (`food-item`) and
the plate. It does not name foods. CLIP names each food blob from the meal's menu.

**Why:**
- Menus change every day; a model with one class per food would need retraining for every
  new dish. Food-vs-not-food doesn't.
- Two classes need far less labeled data, and every food photo online counts as data.
- The plate is the ruler: food area / plate area cancels camera height and zoom.

**Evidence:** `docs/clip-menu-test.md` (CLIP picks the right dish from a short menu).

**Revisit if:** CLIP naming fails on look-alike menu items (e.g. two pale starches).

---

## D2 — Labels: SAM 3 on Rosie + fixed rules (2026-10-26)
**Decision:** SAM 3 runs on MSOE's Rosie GPU cluster (free) with the menu words as prompts.
A person checks every batch on a contact sheet and fixes or drops bad images.

Rules, the same for every data source:
- Touching pieces of the same food = one blob; lone pieces = separate blobs.
- Sauce smears, crumbs, stains = not food.
- Bones = not food.
- Plate = the full circle, even where food covers it.

**Why:** Roboflow's AI labeling tools cost credits (Research plan: 50/month). SAM 3 on Rosie
costs nothing. Menu-word prompts beat a generic "food" prompt, which grabs crumbs.

**Evidence:** meal_01: 22 images, 106 labels (82 food, 22 plate) after fixing 4 bad frames
(half plate, bones labeled as chicken, missed pasta) and merging pasta pieces into piles.

**Revisit if:** SAM 3 misses keep showing up on new meals (then add a recall check per menu word).

---

## D3 — v1 scope: one main plate, restaurant style; trays are v2 (2026-10-26)
**Decision:** Train and demo on one round main plate per scan, no tray. Frame the camera wide
enough for a full tray, so side bowls and cups can be added later with no new hardware.

**Why:**
- CMS's own surveyor dining form lists "meals served on trays in a dining room" as an
  institutional practice to look for. Homes have been moving to plated, restaurant-style dining.
- 70% of operators offer restaurant-style dining (FoodService Director 2016, 244 operators).
  Note: that is "offer", not "share of meals"; 45% also deliver to rooms.
- Staff chart one 25% step per meal, mostly from the entrée, which is on the main plate.
- Other long-term-care intake cameras (AFINI-T, Meal Vision) photograph one plate.

**Evidence:** `context/senior-dining-service.md` (sources; CMS-20053 and the FSD survey were
checked by hand).

**Revisit if:** a pilot home serves most meals on trays (e.g. mostly in-room dining).

---

## D4 — Generalization: measure it, then close the gap with Active Learning (2026-10-26)
**Decision:** We don't claim the plate model works on trays or other settings. We measure the
drop and show how the Roboflow loop closes it.

```
plates (our unseen test meal)  -> score A
trays  (FLIC, never trained on) -> score B
gap = how much new data that setting needs
```

The Workflow includes an Active Learning step (Roboflow Dataset Upload block): low-confidence
images go back to Roboflow, get labeled, and the model is retrained and redeployed.

```
deploy -> catch unsure images -> label (SAM 3 + fix) -> retrain (~20-40 min) -> redeploy
```

**Why:** This is how Roboflow expects production vision to work: deploying is the start, and
production data drives improvement. Food blobs should carry over because the model is
class-agnostic (D1); containers and clutter on trays are new and need data.

**Evidence:**
- Roboflow Active Learning docs: https://docs.roboflow.com/deployment/monitoring-and-analytics/active-learning
- "How to Monitor & Improve AI Models in Production": https://blog.roboflow.com/how-to-improve-ai-models/
- RF-DETR's "transfers to new domains" is a vendor claim; we measure instead of repeating it.

**Revisit if:** the tray gap is small (then trays can move into v1).

---

## D5 — Data mix: our meals are train + test; public sets are train only (2026-10-26)
**Decision:**

| Source | Use | Why |
|---|---|---|
| Our meals | train + **test** | the exact station; the only honest test |
| FLIC (canteen trays, CC BY 4.0) | train, ~500 cropped plates | real leftovers, top-down, 640x480, grams |
| LeFood-Set (hospital, CC BY 4.0) | train, ~250 | white china plate, real eating, smears |
| "comida" on Universe (CC BY 4.0) | train, ~300 | china plates, top-down, full portions |

The test set is always a whole meal the model never saw. Near-identical shots of one meal
moment never sit on both sides of a split.

**Why:** No public dataset has one regular plate + top-down + before/after + masks + grams.
The only close one (AFINI-T, Waterloo) is available on request only. Each public set covers
part of what we need; our own meals cover the rest.

**Evidence:** dataset survey (FLIC paper https://doi.org/10.3390/app16115465;
LeFood https://data.mendeley.com/datasets/cchsk79jkt/1;
comida https://universe.roboflow.com/foodsegmentation-y4ncl/food-segmentation-aiqle).

**Revisit if:** public data hurts the score on our test meal (compare v0 = ours only vs
v1 = ours + public).

---

## D6 — Train RF-DETR Seg on Rosie; deploy through Roboflow (2026-10-26)
**Decision:** Train `RFDETRSegSmall` on Rosie's H100 (T4 as backup), export with
`export_for_roboflow`, upload the weights to the Roboflow project, and run them in the
Workflow on Roboflow Inference.

**Why:** Free GPU time and no credit limit on experiments; the weights still deploy through
Roboflow, which the brief requires.

**Evidence (measured 2026-10-26, H100):**
- meal_01 (14 train images), 10 epochs: 115 s total.
- ~1000 images, 2 epochs: 65 s total, so 50-100 epochs ≈ 20-40 min (estimate).
- Rosie's V100 nodes fail with this setup (old driver); use H100 or T4.

**Revisit if:** custom seg weights can't be uploaded to Roboflow (then the Orin loads the
weights directly and Roboflow Inference runs the rest).

---

## D7 — Area first; depth only if it beats area (2026-10-26)
**Decision:** % eaten = 1 − (after food area / before food area), with each area divided by
plate area. Depth (volume) is added only if it measurably lowers the error.

**Why:** Two independent checks put area-only error at roughly 6-12 points, inside the
≤10-15 point target, and below the ~15-20 point error of staff eyeballing.

**Evidence:**
- meal_01 (SAM 3 masks vs scale): 7.7 points average error.
- FLIC (hand masks vs weighed grams, ~1000 dishes): pasta 6.5, main 12.0, side 10.8 points.

**Revisit if:** food eaten from the top of a pile (mashed potatoes, rice) shows large error;
that is where area is weakest and depth should help.

---

## D8 — Public data follows our label rules, or it's dropped (2026-10-26)
**Decision:** Every public set is converted to our two classes and our rules before training.
Images that can't be made to follow the rules are dropped, not "mostly" kept.

| Rule | FLIC (canteen trays) | MyFoodRepo (home meals) |
|---|---|---|
| One blob per **menu item** | one course color on a plate = one blob (mixed veg, mixed salad = one item) | keep only images with item-level, non-overlapping labels |
| Different foods = different blobs | drop "cod with potatoes" plates (2 foods in one color) | — |
| No unlabeled food in frame | gray out everything outside this plate's circle, but keep this plate's own food (e.g. pizza overhang); label lone pieces (pea, carrot slice) as their own blobs | drop images where SAM 3 finds food that has no label |
| Plate = full disk | SAM 3 plate rim → fitted circle; bowls count as `plate` | SAM 3 plate → fitted ellipse; drop images with no plate |
| Leftovers | keep after-meal plates; empty plates = negatives; drop plastic-covered plates | — |

**Why:** One mislabeled pattern repeated hundreds of times teaches the model the wrong rule.
Unlabeled food is the worst case: it teaches "food = background".

**Evidence:** FLIC pilot (20 trays, 102 crops, 85% ok); MyFoodRepo filter 44k → 2,015 candidates
before the SAM 3 check.

**Revisit if:** v1 (ours + public) scores worse than v0 (ours only) on our unseen test meal.

---

## D9 — Success metrics: model, task, ops; % eaten error is the headline (2026-10-27)
**Decision:** Every model and Workflow version is judged on three layers. The task layer decides.

| Layer | Metric | Target | Now |
|---|---|---|---|
| Model | Mask mAP50:95 on an unseen meal (meal_03) | >= 0.80 | 0.88 (v1b) |
| Model | Plate found on every test image | 100% | not checked |
| Model | Food P/R/F1 at the F1-best confidence | report | — |
| **Task** | **Average error, % eaten vs scale (points)** | **<= 10** | not measured |
| Task | Bias (signed average error) | within +/-5 | not measured |
| Task | Same 25% bin as the scale | >= 80% | not measured |
| Task | Low eaters caught (scale < 50% eaten) | >= 90% | not measured |
| Ops | Photo to % on the Orin | < 1 s | not measured |
| Ops | Plates sent to review (Active Learning) | <= 10% | — |

Blob-count exact % stays a diagnostic, not a target.

**Why:**
- Roboflow gives no "good mAP" number; it compares models on a fixed test set and ranks
  Workflow Eval candidates by average error, then bias, then exact matches, then latency.
- Its own tutorial shows a high mask score (0.91 mIoU) with a wrong task answer (0/5 counts).
- The bar to beat is staff eyeballing: right ~44% of the time, ~20 points high, misses low eaters.
  <10 points is the "acceptable" margin used in long-term-care plate research.

**Evidence:** `docs/research/success-metrics.md` (sources). Targets for bias, bin agreement,
low-eater recall, latency and review rate are our own calls, not from a source.

**Revisit if:** area-based % eaten can't reach <= 10 points (then depth/volume, D7).

---

## Parked ideas (not doing yet; revisit only if the score says so)
- **Blur augmentation.** FLIC plate crops are upscaled ~1.8x and softer than our photos
  (sharpness ~50-180 vs ~470). Only add a light blur augmentation (~25% of images) if the model
  does worse on soft or out-of-focus images. Not added now, to avoid over-engineering.

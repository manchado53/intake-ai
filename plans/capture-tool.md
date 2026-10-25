# Capture tool

**Goal:** turn one staged meal into clean, labeled-later data in a few minutes, with nothing
mixed up. One window, keyboard only.

**Why:** everything downstream waits on photos. The same shots serve three jobs:
color images to train the `food-item` + `plate` model, depth + scale grams to prove
accuracy (camera % eaten vs scale % eaten), and the camera code is reused by the live station.

**How a meal goes:** full plate (s0) → remove some of one food → s1 → … → s4 nearly empty,
plus an empty-plate shot. At each state: weigh the plate, type the grams, say which food
changed, take 3 shots (nudge/rotate the plate between shots).

**What it saves (raw, never warped, so calibration can be redone later):**
`data/raw/meal_01/s0_1_color.png` (native color), `s0_1_depth.png` (16-bit mm, average of
10 frames, holes = 0), and one row per shot in `data/raw/log.csv`
(meal, state, shot, grams, food changed, time, holes %, calibration date).

**Safety:** stop with a clear message if the camera is busy or missing; try to lock exposure
and white balance and log whether it worked; never overwrite an existing shot.

**Defaults (agreed):** meals auto-named `meal_01`, `meal_02`, …; grams typed in the window;
3 shots per state. A `--fake` mode with synthetic frames lets the logic be tested without
the camera.

**Not in scope:** uploading to Roboflow, labeling, applying the calibration (separate steps).

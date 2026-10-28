# Setup & validation log

What the capture station is, why it is built this way, and how we checked it.
Newest entries at the bottom of each section.

## Hardware

| Part | Model | Role |
|---|---|---|
| Camera | Orbbec DaBai DCW (borrowed from the Robot-DS JetRover) | Color for the model, depth for volume |
| Ground truth scale | Taylor 11 lb Glass Platform, 1 g steps | Weighs plates before/after |
| Edge compute | Jetson Orin Nano Super 8GB (on the JetRover, 19 V bench cable) | Runs Roboflow Inference offline |
| Dev / capture | Windows laptop | Photos, labeling, training |
| Spare camera | Logitech C270 (USB, color only) | Backup if the Orbbec fails |

## Decisions

**One camera, color + depth.** The model only sees the color image. It answers *what* food
and *where* (masks). Depth is used after the model: food height inside each mask, summed
over pixels = volume. % eaten = 1 − after volume / before volume. This is the same split used by
the long-term-care RGB-D study (Pfisterer et al., Sci. Reports 2021, mean intake error −4.2%)
and the MDPI 2024 cafeteria study.

**Why depth at all.** Area alone is only reliable near 0% or 100% eaten. Food eaten from the
top of a pile keeps the same area. The alert threshold (50%) sits where area-only is weakest.

**Camera height ~37–45 cm, pointing straight down.** Lowest height where the plate (+ QR ticket)
still fits in the depth view (68° × 45°). Depth error grows with distance squared, so lower is
more accurate. Must stay above the ~30 cm minimum range.

**Ground truth = whole-plate weighing on a 1 g scale.** 1 g is ~0.2% of a 500 g meal, the
research gold standard is ±1 g, and camera error is ~10× larger. Weights are typed in by hand.

## Software setup (Windows laptop)

The DaBai DCW depth sensor uses Orbbec's legacy OpenNI protocol:
- Orbbec SDK v2 (`pyorbbecsdk2`) does **not** support it (0 devices found).
- Needed: Orbbec sensor driver `SensorDriver_V4.3.0.22` + Orbbec OpenNI SDK 2.3.0.86
  + Microsoft Visual C++ 2013 runtime (x64) + `openni` Python bindings.
- `openni` 2.3.0 breaks on Python 3.13 → project venv uses **Python 3.11**.
- Color comes through Windows as a normal webcam ("Orbbec DaBai DCW RGB Camera").
- Live check: `.venv/Scripts/python tools/preview.py` (color left, depth right).

## Validation

### 2026-10-24 — distance check
| What | Value |
|---|---|
| Tape measure, lens → plate | 14.75 in = 374.7 mm |
| Camera center reading | 375 mm |
| Error | ~0.3 mm (target ±5 mm) ✅ |
| Depth frame | 640 × 480, ~83% of pixels with a reading |

### 2026-10-25 — color/depth alignment check
Overlay of depth edges (height jumps) on the color image, box + tape measure on the plate.
| Finding | Detail |
|---|---|
| Depth was **mirrored** | OpenNI mirrors depth by default; the color webcam doesn't. Fixed: `set_mirroring_enabled(False)` in `tools/preview.py` (confirmed in the live preview). |
| OpenNI registration does nothing | OpenNI has no color sensor here (color comes through Windows as a webcam), so `IMAGE_REGISTRATION_DEPTH_TO_COLOR` has no effect. |
| Depth view is **wider** than color | Plate rim ~130→560 px wide in color vs ~190→490 px in depth: depth needs scale + shift to line up with color. To do: one-time calibration. |
| Black glossy box | Top reads partly as holes, so its depth edges are unreliable. Use a light, matte target for calibration. |

### 2026-10-25 — depth → color calibration
`tools/calibrate.py`: click the same 4 box corners in color and depth, fit a homography
(depth pixels → color pixels), saved to `calib/depth_to_color.json`. Result: scale ~1.33–1.35×,
shift ~(−112, −86) px. Redo it if the camera moves. How it works: `docs/calibration.md`.

Check on a **new scene** (box moved, not used in the fit): distance from each depth edge to the
nearest color edge.
| | Median gap | Edges within 3 px |
|---|---|---|
| No calibration (plain resize) | 25.0 px | 6% |
| Calibrated | 6.6 px | 35% |

Box edges and plate rim line up to ~2–3 px (~1.5 mm at 37 cm) by eye; the median is pulled up by
depth edges with no color edge (table, shadows, hole borders). Only 4 point pairs were used, so
the fit's own error (0 px) proves nothing; the new-scene check is the real test.
Images: `docs/img/calibration-clicks.png`, `calibration-overlay.png`,
`calib-check-no-calibration.png`, `calib-check-calibrated.png`, `calib-before-after.png`.

### 2026-10-25 — recalibration with 16 points
Box (no plate) moved to spots across the whole view, 16 corner pairs, homography with RANSAC.
Honest error = **leave-one-out** (fit on 15 pairs, test on the one left out, repeat for all 16):
| Fit | Median error | Max |
|---|---|---|
| Old 4-point homography (tested on the 16 new pairs) | 7.1 px | 13.1 px |
| New 16-point homography (saved) | 4.9 px | 10.1 px |
| New 16-point affine | 5.5 px | 8.4 px |

~5 px ≈ 2.7 mm at 37 cm, mostly hand-click noise; the box's IR shadow blurs its left edge in depth.
Affine and homography are about equal, so the camera is close to straight down.

### 2026-10-25 — plate-only check (16-point calibration)
White glossy plate alone. Plate rim fit as a circle in color edges vs warped depth edges:
| | Center | Radius |
|---|---|---|
| Color rim | (334, 243) | 210.5 px |
| Depth rim | (332, 245) | 216.1 px |

Center off 2.9 px (~1.6 mm): position is right. Depth rim ~5.6 px (~3 mm) wider all around:
the depth edge fires at the outer foot of the sloped rim, and the fit plane (box top) sits
higher than the rim. Food sits in the middle and masks get shrunk a few px, so this is fine.
Rim gap median 6.4 px. Image: `docs/img/calib-plate-rim.png` (green = color edges,
red = depth edges).

Small red loops inside the plate are **holes**: 2.6% of the plate in one frame, 2.3% after a
15-frame average; half the stray edges sit right next to a hole, the rest are holes that
flicker between frames. Image: `docs/img/plate-holes.png` (magenta = holes). See Known issues.

### Known issues
- **Glossy plate = holes (depth 0).** The camera's own infrared dots bounce straight back off
  the glaze like a mirror, so those spots read 0. Not the room light: the color image shows no
  shine there, so moving the lamp won't help. ~2.5% of the white plate (see the 2026-10-25
  plate check). Fixes: matte/paper plate (best), tilt the camera a few degrees (needs
  recalibration), or fill small holes from neighbors in code. Food itself is mostly matte, and
  `measure.py` skips 0 pixels.

### Depth on the Orin (2026-10-28)
- Camera must sit on the Orin's own USB hub: behind the extra WCH hub (1a86:8091) the depth
  sensor browns out and drops off USB the moment it streams.
- Driver: Orbbec OpenNI SDK 2.3.0.86 arm64 (github.com/orbbec/OpenNI_SDK releases) in
  `~/intake/openni/sdk/libs`. Called straight through ctypes (`station/depth.py`): the `openni`
  pip wrapper corrupts memory there (malloc crash within ~300 frames); ctypes ran 3000 frames clean.
- Never use the Orbbec ROS driver next to the station: it takes the color camera too (/dev/video* vanish).
- Depth 640x480 @ 30 fps, 10 frames averaged per scan = 0.42 s. Depth edges land on the color
  image within a few px with the laptop calibration.
- Live check, Mary's lunch: same plate scanned twice -> 0-2% apart (area and depth). Chicken piece
  removed -> area 43%, depth 48%. Pasta / edamame taken off the top -> area 1-5%, depth 21-35%.

### To do
- Height test: object of known thickness (deck of cards ~18 mm) on the plate.
- Volume test: measured box vs camera volume (target within ~10%).
- Noise test: empty table reading stability over 10 s (target ±2 mm).

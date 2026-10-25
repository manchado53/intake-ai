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

### Known issues
- **Glossy plate + overhead light = holes.** Shiny spots mirror the infrared pattern away, so
  those pixels read 0. Fix: side lighting, matte plate. Food itself is mostly matte.

### To do
- Height test: object of known thickness (deck of cards ~18 mm) on the plate.
- Volume test: measured box vs camera volume (target within ~10%).
- Noise test: empty table reading stability over 10 s (target ±2 mm).

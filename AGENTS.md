# AGENTS.md

Guide for coding agents working in this repo. Read this first.

## What this is
**Intake.ai**: camera-based meal intake tracking (currently aimed at nursing homes), built as a Roboflow
Field Engineering tech challenge (proof-of-concept). Live demo **Wed 2026-10-28, 6 pm CDT,
Zoom, 30 min hard stop, must be live**.

**Fixed (from the brief):** own data, a trained Roboflow model, a Workflow with a custom block,
deployment on Roboflow Inference, actionable insights. See `context/brief-summary.md`.

**Everything else is still open.** The current direction lives in `plans/` and changes as we
learn. Read the latest plan before building, and don't treat design choices below as settled.

## Repo map
| Path | What |
|---|---|
| `tools/preview.py` | Live color + depth view, for aiming the camera |
| `tools/measure.py` | Drag a box on depth → height (mm) + volume (cm³) |
| `tools/capture.py` | Shoot staged meals: raw color + 16-bit depth + scale grams → `data/raw/` + `log.csv` (`--fake` = no camera) |
| `tools/calibrate.py` | Click matching points → depth→color homography in `calib/depth_to_color.json` |
| `docs/calibration.md` | Why and how depth is lined up with color (homography math) |
| `docs/setup.md` | Hardware, decisions, driver setup, validation log (append results here) |
| `plans/` | Plain-English plans; one file per task |
| `context/` | Challenge brief + recruiting email summary |
| `context/market-research.md` | Competitors + similar initiatives (Meal Vision, Nuvilab, AFINI-T, waste vision, patents), market size, honest differentiation |
| `context/nursing-home-rules.md` | US nursing-home rules + practice for meal intake (CMS F-tags, MDS, HIPAA, design rules). Read before designing alerts, reports, or privacy |

## Setup (Windows laptop)
- Python **3.11** venv at `.venv` (`openni` breaks on 3.13): `py -3.11 -m venv .venv`
- Packages: `openni opencv-python numpy pygrabber`
- Camera: **Orbbec DaBai DCW**. Depth uses the legacy OpenNI protocol, which needs the Orbbec
  sensor driver, Orbbec OpenNI SDK 2.3.0.86, and the VC++ 2013 x64 runtime. Orbbec SDK v2 /
  `pyorbbecsdk2` does **not** see this camera. Details in `docs/setup.md`.
- OpenNI libs path defaults to `~/Downloads/orbbec_openni/...`; override with `OPENNI2_LIBS`.
- Run: `.venv/Scripts/python tools/preview.py` or `tools/measure.py` (q quits).
- Only one program can hold the camera at a time; close the preview before running another.
  Unplugging the camera ends the program.

## Current direction (open to change)
These are working choices, not rules. If one changes, update the plan and this list.
- Target customer: nursing homes (they already chart intake by eye, 0/25/50/75/100%).
- Approach: segmentation model finds foods + plate; before vs after compared with depth math.
- Classes so far: `chicken`, `rice`, `pasta`, `green-beans`, `fruit`, `plate`.
- Ground truth: whole-plate weight on a 1 g kitchen scale.
- Roboflow project: `manchado53/intake-ai-food-seg`.

## Hardware facts (measured, stable)
- Depth range starts ~30 cm; at ~37 cm the distance check matched a tape measure to ~0.3 mm.
- Dark, shiny, or steep surfaces read as holes (0 mm).

## Rules
- **Never commit to `main`.** Branch off the latest `main` first: `feature/…`, `fix/…`,
  `docs/…`, `research/…`, `experiment/…`. Merge only through a PR.
- Plan before non-trivial work: write a short plan to `plans/<task>.md`.
- Never commit secrets (`.env`, API keys) or bulky data (`data/raw/`, weights, `.db`).
  Roboflow key goes in a gitignored `.env` as `ROBOFLOW_API_KEY`.
- Don't touch the Robot-DS robot code; the Orin and camera are borrowed from it.
- Match the existing code style: small single-file tools, short docstring at the top saying how
  to run it, comments only where the why isn't obvious.
- Record new measurements or validation results in `docs/setup.md`.

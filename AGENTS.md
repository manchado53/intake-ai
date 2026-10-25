# AGENTS.md

Guide for coding agents working in this repo. Read this first.

## What this is
**Intake.ai**: camera-based meal intake tracking for **nursing homes**, built as a Roboflow
Field Engineering tech challenge (proof-of-concept). Live demo **Wed 2026-10-28, 6 pm CDT,
Zoom, 30 min hard stop, must be live**.

A color + depth camera looks straight down at a plate before and after a meal. A trained
Roboflow instance-segmentation model outlines each food and the plate. A custom Workflow block
uses depth inside each outline to get volume, then % eaten = 1 − after / before, then
protein/kcal from the menu portion. Alerts fire when a resident eats under 50% three meals in a
row. Runs offline on a Jetson Orin Nano with Roboflow Inference.

Source of truth for requirements: `context/brief-summary.md` (and the brief PDF next to it).

## Repo map
| Path | What |
|---|---|
| `tools/preview.py` | Live color + depth view, for aiming the camera |
| `tools/measure.py` | Drag a box on depth → height (mm) + volume (cm³) |
| `docs/setup.md` | Hardware, decisions, driver setup, validation log (append results here) |
| `plans/` | Plain-English plans; one file per task |
| `context/` | Challenge brief + recruiting email summary |

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

## Domain facts to keep straight
- Target: nursing homes (skilled nursing). Intake is charted by eye as 0/25/50/75/100%.
  Regular-texture diet only in v1.
- Model classes: `chicken`, `rice`, `pasta`, `green-beans`, `fruit`, `plate`.
- The model only finds **where** each food is. Before/after comparison is math, not training.
- The **before** scan is the reference (portions vary: large/small orders, scoop drift).
- Camera ~37–45 cm (15–18") above the plate, pointing straight down. Depth minimum ~30 cm.
- Dark, shiny, or steep surfaces read as holes (0 mm). Fill holes from nearby valid depth.
- Ground truth: whole-plate weight on a 1 g kitchen scale, typed in by hand.
- Roboflow project: `manchado53/intake-ai-food-seg` (instance segmentation, public, CC BY 4.0).

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

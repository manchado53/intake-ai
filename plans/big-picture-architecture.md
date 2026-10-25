# Plan: Plate Check — big picture + setup

## What
Lock the whole system shape before building pieces, so the weekend work
(photos, labels, training) feeds straight into the demo.

One camera (Logitech C270) looks straight down at a tray. A QR tray ticket
says which resident and which meal. A Roboflow segmentation model outlines
each food and the plate. A custom Workflow block compares the "after" scan
with the "before" scan (or a golden reference plate), using the plate's size
to cancel camera-height changes, and turns food area into % eaten and grams
(menu portion sizes). Results land in a small local database and fan out to
a station screen, a daily/weekly report, and a Slack alert when a resident
eats under 50% three meals in a row. It all runs offline on the Orin Nano
(still mounted on the JetRover, powered by the 19 V bench cable) with
Roboflow Inference in Docker. The laptop is the fallback.

Ground truth: whole-plate weighing on the Taylor 1 g scale, typed in by
hand, gives a scorecard of camera % vs scale %.

## Target customer
Nursing homes (skilled nursing; memory care next). They already chart intake by law
(0/25/50/75/100% by eye), run dietitian-approved cycle menus with standard portions
(e.g. Sysco IMPAC, CBORD), and print a tray ticket per resident per meal. So:
- The "before" scan is the reference, because portions vary (large/small orders, scoop drift).
- Output is % eaten per item, then protein/kcal eaten from the menu's per-portion data.
- The QR is the tray ticket: resident, diet, portion size, items.
- v1 = regular-texture diet only; mechanical soft / puree are future work.
Assisted and independent living are out of scope (restaurant-style, no intake charting).

## Why
Picking the pieces and the data shapes now means photos taken tonight are
labeled the right way (foods + plate), the capture script saves exactly what
the custom block and scorecard need, and nothing gets rebuilt Monday.

## Setup to prepare
- Capture station: C270 straight down, ~40–60 cm, lamp, taped plate spot.
- Laptop capture script: key press -> photo + tray ID + phase + grams.
- Roboflow project: instance segmentation, classes = ~5 foods + plate.
- Orin: SSH in, Docker, Roboflow Inference, without touching robot code.

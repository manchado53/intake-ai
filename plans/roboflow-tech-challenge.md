# Plan: Plate Check (Roboflow tech challenge)

## What
A proof of concept that tracks how much a senior-living resident ate.
A camera sees the plate before and after the meal. A Roboflow segmentation
model finds each food. A custom Workflow block compares before vs after,
turns it into % and grams eaten (using the menu's standard portions), and
flags residents who eat under 50% three meals in a row. Results go to a
station screen, a daily/weekly report, and a Slack alert. Everything runs
offline on the Orin Nano with Roboflow Inference.

## Why
Aides guess intake by eye and are badly off (guessed 79% eaten vs 59%
observed). Undernutrition in care homes is common and costly. Existing tools
either weigh plates by hand (slow) or are unproven. This is a real gap, and
it fits the brief: own data, labeling, training, a custom block, edge
deployment, and actionable outputs.

## Scope
- In: solid foods, ~5 named menu items, one camera, before/after scans
  paired by a QR tray ticket; golden-plate fallback when no "before" exists.
- Out: drinks, soups, liquids. Mixed leftovers are best effort.
- Proof: a scorecard of camera % vs kitchen-scale % per food.
- Stretch: depth camera for piles/bowls, GPIO LED/buzzer.

## Never cut
Own data, custom block, live demo, scorecard.
Cut order if behind: depth -> QR pairing -> Orin (use laptop) -> Slack.

## Schedule
Fri setup + buy scale/tripod · Sat photos, labels, train · Sun workflow +
custom block + live capture · Mon screen, Slack, reports, scorecard ·
Tue slides + rehearse · Wed demo.

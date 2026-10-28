# Live depth on the station (area + depth average)

**Why:** offline, the plate-shape depth fix plus averaging with area cut % eaten error from ~14.5 to
~5.5 points on our 5 meals (`docs/experiments/2026-10-28-depth-plate-shape.md`). The live station
still uses area only. Depth now runs on the Orin through Orbbec's OpenNI arm64 driver
(`~/intake/openni`), side by side with the station's color camera (tested 2026-10-28).

**What:** the station grabs a depth frame with every scan and, when it can, reports % eaten as the
average of the area % and the depth %. Same math as `eval/depth_vs_area.py`.

- The Workflow also returns the food and plate masks (two new outputs; contract 1 gains them).
  It stays the one place that sees and names food; the station only measures height inside its masks.
- New `station/depth.py`: OpenNI reader (averages ~10 frames per scan, warps depth onto color with
  `calib/depth_to_color.json`) and the pure math ported from the eval script (plate profile,
  food height above the plate's real shape, volume per food).
- A new **EMPTY PLATE** button: scan the empty plate once per plate type; it saves the plate's
  depth shape. With no saved shape, the station stays area-only.
- `intake.compare`: per item, % eaten = mean(area %, depth %) when both scans have depth, else
  area %. Contract 2 items gain optional `pct_area` / `pct_depth` so the dashboard and panel can see both.
- On by default; `--no-depth` turns it off. No OpenNI, no camera, or no shape -> area, as today.

**Safety for the demo:** branch + PR; tests on the laptop with a fake depth reader; then on the Orin
with one real plate before ~10:30 CDT. If it misbehaves: restart with `--no-depth`, demo = area.

**Open risk:** the depth->color calibration was made on the laptop rig (~37 cm); the robot camera
sits closer (~28 cm). Check the overlay on the Orin; if it's off by more than a few pixels, fix the
offset before trusting the numbers.

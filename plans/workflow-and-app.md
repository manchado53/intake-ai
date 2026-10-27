# Plan: Workflow + station + dashboard (for the Wed 2026-10-28 12 pm panel)

## What
Turn the trained model into the thing the panel sees, framed as See -> Understand -> Act
(the team's own discovery language, `context/prep-call-2026-10-27.md`).

The Orin on the JetRover is the kitchen station. Its own camera watches the plate spot. When a
resident's QR card and a plate sit still under it, it calls one Roboflow Workflow on Roboflow
Inference running on the Orin. The Workflow reads the QR, segments food and plate, names each food
blob against today's menu with CLIP, and a custom Python block turns each blob into "area / plate
area". The station remembers the meal: first scan = before, second = after, then % eaten per item,
the 0/25/50/75/100 chart value, kcal and protein. The robot's screen shows big status text for
kitchen staff. Only the numbers go to the dashboard; photos stay on the box.

The laptop plays "the cloud / the dietitian's PC": a Streamlit dashboard with the live feed of
scans, each resident's day, and a red alert for under 50% three meals in a row. Fake residents only.

Same code runs fully on the laptop against Roboflow's hosted API as the fallback.

## Why
- The brief requires a Workflow with a custom block, deployed on Roboflow Inference, and
  actionable insights. The model alone covers none of that.
- A box above the dish return, with a small screen and no laptop, is what a home would actually
  install; edge hardware is also what the Roboflow team wants to see.
- Workflows are stateless by design; meal memory belongs to the station / the facility's system.
  That keeps the Workflow testable (and Workflow Evals-ready).

## How we build it
Every piece is tested alone with fakes before it joins the next (`docs/contracts.md` fixes the
three JSON shapes between them). Three agents build in parallel: Workflow (area math + spec),
station (meal math + loop + screen), dashboard. Then: % eaten vs the scale through the real
Workflow, the end-to-end check on the laptop, the Orin, and a backup video.
Cut from the bottom if late: Active Learning, then the station on the Orin, then Inference on the
Orin (all hosted).

## Done when
QR card + plate under the robot's camera -> "BEFORE saved"; a second scan -> per-item % eaten on
the robot's screen; the laptop dashboard updates and shows the alert case; it runs through Roboflow
Inference; a backup video exists.

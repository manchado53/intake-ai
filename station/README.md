# Station

The kitchen box. Watches the plate spot, scans when a resident's QR card holds still for ~1 s,
remembers before/after per resident + meal, and POSTs the numbers to the dashboard
(`docs/contracts.md` section 2). Shows big status text on a small screen.

| File | What |
|---|---|
| `station.py` | Main loop + web screen (`--source`, `--fake-workflow`, `--meal`, `--port`) |
| `intake.py` | Meal math: group blobs per food, % eaten, chart bin, kcal/protein, current meal |
| `store.py` | `station.db` (SQLite): scans, open "before", outbox retried every 3 s |
| `workflow_client.py` | Real Workflow call (`inference_sdk`) or a fake (local QR + canned fractions) |
| `screen.html` | The screen: polls `/state` every 500 ms, live MJPEG `/video`, last scan `/annotated.jpg` |
| `make_demo_frames.py` | Builds `data/raw/test_station/` from meal_03 with a pasted "R01" card |

## Config
Env vars, else `.env` (repo root; from a worktree the main checkout's `.env` is read too):

| Var | Default |
|---|---|
| `ROBOFLOW_API_KEY` | (required for real mode) |
| `INFERENCE_URL` | `https://serverless.roboflow.com` |
| `WORKFLOW_ID` | `intake-plate` (workspace `manchado53`) |
| `DASHBOARD_URL` | `http://localhost:8000` (POSTs go to `/api/scan`) |
| `STATION_ID` | `laptop-station` |
| `CAMERA` | `0` (default `--source`) |
| `STATION_DB` | `station.db` in the repo root |

## Run on the laptop
```
.venv-app/Scripts/python station/make_demo_frames.py                 # once: test frames
.venv-app/Scripts/python tests/fake_dashboard.py                     # or the real dashboard
.venv-app/Scripts/python station/station.py --source data/raw/test_station --fake-workflow --meal lunch
.venv-app/Scripts/python station/station.py --source 0 --meal lunch  # camera + hosted Workflow
```
Open http://localhost:8080 and fullscreen it (F11). Folder mode = one scan per image
(`--pause` seconds apart); camera or video mode = scan on a steady QR, re-arm when the card
has been gone ~1.5 s. Close `tools/preview.py` first: only one program can hold the camera.

## Run on the Orin
```
export INFERENCE_URL=http://localhost:9001     # Roboflow Inference server on the Orin
export DASHBOARD_URL=http://<laptop-ip>:8000
export STATION_ID=orin-kitchen-1
python station/station.py --source 0 --port 8080
```
`--source` is the camera index (V4L2 on Linux; try 0, 1, ...). Open `http://localhost:8080` in
the robot screen's browser in kiosk/fullscreen mode, or `http://<orin-ip>:8080` from the laptop.

## Behaviour
- Scan: Workflow -> resident from QR (`config/profiles.json`) -> first ok scan of the
  resident + meal + day = BEFORE, later scans = AFTER against that before -> POST via outbox.
- The dashboard being down never blocks scanning: bodies wait in `station.db` and are re-sent;
  the dashboard ignores repeated `scan_id`s.
- A blob named off the resident's menu is reassigned to the closest menu item if the Workflow
  sends per-word scores (`scores`), else ignored and flagged `off_menu` (needs review).
- Screen texts: "Place plate + card", "Hold still…", "<name> – lunch – BEFORE saved ✓",
  "AFTER: ate 50% ✓" + per-item bars, "No card – show the QR", "Center the plate",
  amber "Unsure – sent for review".

## Tests
```
.venv-app/Scripts/python -m pytest tests/test_station_intake.py tests/test_station_store.py
```

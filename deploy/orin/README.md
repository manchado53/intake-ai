# Orin station scripts

Copied to `~/intake` on the Orin (next to `station/`, `config/`, `workflow/`, `venv/`, `.env`).
Setup steps are in `docs/research/orin-setup.md`.

| File | What |
|---|---|
| `run_station.sh` | (Re)start the station + fullscreen screen. `RESET=1` before the demo |
| `kiosk.py` | Fullscreen WebKit window for `localhost:8080` (snap browsers fail on this Jetson) |
| `wf_test.py` | Time 3 Workflow runs against the local Inference server on one image |

`.env` on the Orin holds `ROBOFLOW_API_KEY`, `INFERENCE_URL=http://localhost:9001`,
`WORKFLOW_SPEC=workflow/intake-plate.json`, `STATION_ID`, `DASHBOARD_URL`; never copied here.

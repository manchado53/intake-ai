# Dashboard (laptop = "the cloud / the RD's PC")

The kitchen station POSTs one JSON per plate scan (`docs/contracts.md` §2) to the API. The API
stores it in SQLite. The Streamlit page reads the same DB and refreshes every 2 s.

```
station --POST /api/scan--> server.py :8000 --> app/dashboard.db <-- dashboard.py :8501
```

| File | What |
|---|---|
| `server.py` | FastAPI: `POST /api/scan` (validates, ignores a repeated `scan_id`), `GET /api/health`, `GET /api/scans?limit=50` |
| `dashboard.py` | Streamlit: Live feed, Residents (table + trend + RD alert), QR cards (PNG/PDF sheet) |
| `alerts.py` | Pure alert rule: last 3 recorded meals < 50% → notify RD. Missing meal ≠ 0% |
| `seed.py` | Synthetic history for the 2 days before `profiles.json` date. R02 John D. is low 3 meals in a row |
| `store.py` | SQLite helpers. DB path = env `INTAKE_DB`, else `app/dashboard.db` (gitignored) |
| `cards.py` | QR cards: QR = resident id only (`R01`); name + room printed under it |

## Run (from the repo root, three terminals)

```
.venv-app/Scripts/python -m app.seed                                    # once; safe to re-run
.venv-app/Scripts/python -m uvicorn app.server:app --host 0.0.0.0 --port 8000
.venv-app/Scripts/python -m streamlit run app/dashboard.py --server.port 8501
```

Open http://localhost:8501. The station posts to `http://<laptop-ip>:8000/api/scan`
(`--host 0.0.0.0` lets the Orin reach it; allow port 8000 in the Windows firewall).

Without a station: `.venv-app/Scripts/python tests/fake_station.py --delay 2` posts ~10 scans
(before/after for R01, R03, R04, a `no_qr`, an unknown resident, a duplicate).

Fresh start: stop both, delete `app/dashboard.db`, re-seed. Seeded rows are tagged `synthetic`
in the DB (`synthetic=1`, `station_id="synthetic-seed"`, `scan_id` starts with `seed-`) and in the feed.

## Tests

```
.venv-app/Scripts/python -m pytest tests/test_app_alerts.py tests/test_app_server.py -q
```

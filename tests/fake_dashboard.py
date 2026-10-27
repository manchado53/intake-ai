"""Stand-in for the dashboard: accepts POST /api/scan, prints it, keeps it in memory.

    .venv-app/Scripts/python tests/fake_dashboard.py [--port 8000] [--log scans.jsonl]

GET /api/scans lists what arrived (repeated scan_ids are ignored, as the real one must).
"""
import argparse
import json

import uvicorn
from fastapi import FastAPI, Request

app = FastAPI(title="fake dashboard")
SCANS = {}
LOG = None


@app.post("/api/scan")
async def scan(req: Request):
    body = await req.json()
    if body["scan_id"] not in SCANS:
        SCANS[body["scan_id"]] = body
        short = {k: v for k, v in body.items() if k != "annotated_jpg_b64"}
        print("SCAN", json.dumps(short), flush=True)
        if LOG:
            with open(LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(short) + "\n")
    return {"ok": True}


@app.get("/api/scans")
def scans():
    return [{k: v for k, v in b.items() if k != "annotated_jpg_b64"} for b in SCANS.values()]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--log")
    a = ap.parse_args()
    LOG = a.log
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")

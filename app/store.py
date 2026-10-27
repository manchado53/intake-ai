"""SQLite store for scans (contract 2 bodies). Shared by the server, the dashboard and the seeder.

DB path: env INTAKE_DB, else app/dashboard.db (gitignored).
"""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
PROFILES_PATH = ROOT / "config" / "profiles.json"


def db_path() -> str:
    return os.environ.get("INTAKE_DB", str(APP_DIR / "dashboard.db"))


def load_profiles(path=PROFILES_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def connect(path: str | None = None) -> sqlite3.Connection:
    con = sqlite3.connect(path or db_path(), timeout=10)
    con.execute(
        """CREATE TABLE IF NOT EXISTS scans (
            scan_id     TEXT PRIMARY KEY,
            time        TEXT NOT NULL,
            resident_id TEXT,
            meal        TEXT,
            phase       TEXT,
            status      TEXT,
            synthetic   INTEGER NOT NULL DEFAULT 0,
            received_at TEXT NOT NULL,
            body        TEXT NOT NULL
        )"""
    )
    con.execute("CREATE INDEX IF NOT EXISTS scans_time ON scans(time)")
    return con


def insert_scan(con: sqlite3.Connection, body: dict, synthetic: bool = False) -> bool:
    """Store one scan. Returns False if the scan_id was already there (station retry)."""
    cur = con.execute(
        "INSERT OR IGNORE INTO scans VALUES (?,?,?,?,?,?,?,?,?)",
        (body["scan_id"], body["time"], body.get("resident_id"), body.get("meal"),
         body.get("phase"), body.get("status"), int(synthetic),
         datetime.now().isoformat(timespec="seconds"), json.dumps(body)),
    )
    con.commit()
    return cur.rowcount == 1


def list_scans(con: sqlite3.Connection, limit: int | None = None) -> list[dict]:
    """Scans newest first, each as its contract-2 dict plus `synthetic`."""
    sql = "SELECT body, synthetic FROM scans ORDER BY time DESC, received_at DESC"
    rows = con.execute(sql + (f" LIMIT {int(limit)}" if limit else "")).fetchall()
    out = []
    for body, synthetic in rows:
        d = json.loads(body)
        d["synthetic"] = bool(synthetic)
        out.append(d)
    return out

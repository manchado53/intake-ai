"""Station memory: scans + an outbox of POSTs to the dashboard, in one SQLite file.

The outbox is what keeps scanning alive when the dashboard (or Wi-Fi) is down: every scan
body is queued first, and a background thread keeps POSTing until it gets a 200. The
dashboard ignores a repeated scan_id, so retrying is safe.

    store = Store("station.db"); store.start_outbox("http://localhost:8000/api/scan")
"""
import json
from contextlib import contextmanager
import sqlite3
import threading
import time

import requests

SCHEMA = """
CREATE TABLE IF NOT EXISTS scans (
    scan_id TEXT PRIMARY KEY, time TEXT, date TEXT, resident_id TEXT, meal TEXT,
    phase TEXT, status TEXT, fracs TEXT, body TEXT);
CREATE TABLE IF NOT EXISTS outbox (
    scan_id TEXT PRIMARY KEY, body TEXT, created REAL, attempts INTEGER DEFAULT 0,
    last_error TEXT, sent REAL);
"""


class Store:
    def __init__(self, path="station.db"):
        self.path = path
        self.lock = threading.Lock()
        self._stop = threading.Event()
        with self._db() as db:
            db.executescript(SCHEMA)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:  # commit or roll back
                yield db
        finally:
            db.close()

    # --- scans ---------------------------------------------------------------
    def save_scan(self, body, date, fracs=None):
        """Keep one scan (contract-2 body) plus the grouped {name: area_frac} it measured."""
        with self.lock, self._db() as db:
            db.execute("INSERT OR REPLACE INTO scans VALUES (?,?,?,?,?,?,?,?,?)",
                       (body["scan_id"], body["time"], date, body.get("resident_id"), body.get("meal"),
                        body.get("phase"), body.get("status"), json.dumps(fracs or {}), json.dumps(body)))

    def open_before(self, resident_id, meal, date):
        """Latest ok "before" for this resident + meal + date, as {name: area_frac}, or None.

        Stays open after an "after": a re-scan of the same plate is compared to the same before.
        """
        with self.lock, self._db() as db:
            row = db.execute("SELECT fracs FROM scans WHERE resident_id=? AND meal=? AND date=? "
                             "AND phase='before' AND status='ok' ORDER BY time DESC LIMIT 1",
                             (resident_id, meal, date)).fetchone()
        return json.loads(row["fracs"]) if row else None

    # --- outbox --------------------------------------------------------------
    def enqueue(self, body):
        with self.lock, self._db() as db:
            db.execute("INSERT OR IGNORE INTO outbox (scan_id, body, created) VALUES (?,?,?)",
                       (body["scan_id"], json.dumps(body), time.time()))

    def pending(self):
        with self.lock, self._db() as db:
            return [dict(r) for r in db.execute(
                "SELECT scan_id, body, attempts, last_error FROM outbox WHERE sent IS NULL ORDER BY created")]

    def flush(self, url, timeout=3.0):
        """Try to POST every pending body once, oldest first. Returns how many were delivered."""
        sent = 0
        for row in self.pending():
            try:
                r = requests.post(url, data=row["body"], timeout=timeout,
                                  headers={"Content-Type": "application/json"})
                ok, err = r.status_code == 200, f"HTTP {r.status_code}"
            except requests.RequestException as ex:
                ok, err = False, type(ex).__name__
            with self.lock, self._db() as db:
                if ok:
                    db.execute("UPDATE outbox SET sent=?, attempts=attempts+1, last_error=NULL "
                               "WHERE scan_id=?", (time.time(), row["scan_id"]))
                else:
                    db.execute("UPDATE outbox SET attempts=attempts+1, last_error=? WHERE scan_id=?",
                               (err, row["scan_id"]))
            if not ok:
                break  # dashboard down: keep order, try again next round
            sent += 1
        return sent

    def start_outbox(self, url, every=3.0):
        """Background thread: flush every few seconds until stop()."""
        def loop():
            while not self._stop.is_set():
                try:
                    self.flush(url)
                except Exception as ex:  # never let the sender die mid-demo
                    print("outbox error:", ex)
                self._stop.wait(every)
        t = threading.Thread(target=loop, name="outbox", daemon=True)
        t.start()
        return t

    def stop(self):
        self._stop.set()

"""Store + outbox tests.  Run: pytest tests/test_station_store.py"""
import os
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from station import store as store_mod  # noqa: E402
from station.store import Store  # noqa: E402


def body(scan_id, phase="before", status="ok"):
    return {"scan_id": scan_id, "time": scan_id[:19], "resident_id": "R01", "meal": "lunch",
            "phase": phase, "status": status}


def test_open_before_by_resident_meal_date(tmp_path):
    s = Store(str(tmp_path / "s.db"))
    assert s.open_before("R01", "lunch", "2026-10-28") is None
    s.save_scan(body("2026-10-28T12:00:00-R01"), "2026-10-28", {"pasta": 0.2})
    s.save_scan(body("2026-10-28T12:00:05-R01", status="no_plate"), "2026-10-28", {})
    assert s.open_before("R01", "lunch", "2026-10-28") == {"pasta": 0.2}
    assert s.open_before("R01", "dinner", "2026-10-28") is None
    assert s.open_before("R01", "lunch", "2026-10-29") is None


def test_outbox_retries_and_dedupes(tmp_path, monkeypatch):
    s = Store(str(tmp_path / "s.db"))
    s.enqueue(body("a"))
    s.enqueue(body("a"))  # same scan_id queued twice -> one row
    s.enqueue(body("b"))
    assert len(s.pending()) == 2

    def down(*a, **k):
        raise requests.ConnectionError()
    monkeypatch.setattr(store_mod.requests, "post", down)
    assert s.flush("http://x/api/scan") == 0
    assert len(s.pending()) == 2

    got = []

    class OK:
        status_code = 200

    def up(url, data, **k):
        got.append(data)
        return OK()
    monkeypatch.setattr(store_mod.requests, "post", up)
    assert s.flush("http://x/api/scan") == 2
    assert s.pending() == [] and len(got) == 2


def test_reset_forgets_scans_and_outbox(tmp_path):
    s = Store(str(tmp_path / "s.db"))
    s.save_scan(body("2026-10-28T12:00:00-R01"), "2026-10-28", {"pasta": 0.2})
    s.enqueue(body("2026-10-28T12:00:00-R01"))
    assert s.reset() == 1
    assert s.open_before("R01", "lunch", "2026-10-28") is None
    assert s.pending() == []

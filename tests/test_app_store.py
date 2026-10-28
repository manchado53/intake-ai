"""Dashboard store tests.  Run: pytest tests/test_app_store.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import store  # noqa: E402


def scan(scan_id, t, phase="after", **kw):
    return {"scan_id": scan_id, "time": t, "resident_id": "R01", "meal": "lunch", "phase": phase,
            "status": "ok", **kw}


def test_redo_drops_replaced_scan(tmp_path):
    con = store.connect(str(tmp_path / "d.db"))
    store.insert_scan(con, scan("a", "2026-10-28T12:30:00", total_pct_eaten=0))
    store.insert_scan(con, scan("b", "2026-10-28T12:31:00", total_pct_eaten=50, replaces="a"))
    store.insert_scan(con, scan("c", "2026-10-28T13:00:00", phase="before"))
    assert [s["scan_id"] for s in store.list_scans(con)] == ["c", "b"]

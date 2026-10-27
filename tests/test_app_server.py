"""API + dashboard smoke test: real uvicorn on a free port, fake station scans, seed, Streamlit AppTest."""
import socket
import sys
import threading
import time
from pathlib import Path

import pytest
import requests
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import fake_station  # noqa: E402
from app import seed, server  # noqa: E402


@pytest.fixture(scope="module")
def api(tmp_path_factory):
    db = str(tmp_path_factory.mktemp("db") / "test.db")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    srv = uvicorn.Server(uvicorn.Config(server.create_app(db), port=port, log_level="warning"))
    threading.Thread(target=srv.run, daemon=True).start()
    url = f"http://127.0.0.1:{port}"
    for _ in range(50):
        try:
            requests.get(url + "/api/health", timeout=1)
            break
        except requests.ConnectionError:
            time.sleep(0.1)
    yield url, db
    srv.should_exit = True


def test_scan_flow(api):
    url, db = api
    assert requests.get(url + "/api/health").json() == {"ok": True}
    sent = fake_station.scans()
    for s in sent:
        r = requests.post(url + "/api/scan", json=s)
        assert r.status_code == 200 and r.json() == {"ok": True}
    got = requests.get(url + "/api/scans?limit=100").json()
    assert len(got) == len(sent) - 1  # duplicate scan_id stored once
    bad = dict(sent[0], scan_id="x", phase="during")
    assert requests.post(url + "/api/scan", json=bad).status_code == 422


def test_seed_idempotent(api):
    _, db = api
    first = seed.seed(db)
    assert first > 0 and seed.seed(db) == 0


def test_dashboard_renders(api, monkeypatch):
    from streamlit.testing.v1 import AppTest

    _, db = api
    monkeypatch.setenv("INTAKE_DB", db)
    at = AppTest.from_file(str(ROOT / "app" / "dashboard.py"), default_timeout=60)
    at.run()
    assert not at.exception, at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "John D." in md and "notify RD" in md  # seeded 3-low-meals alert
    assert "Mary R." in md and "ate" in md  # live feed
    assert [m.label for m in at.metric][:3] == ["Meals recorded today", "Average eaten", "Residents at risk"]

    at.button(key="n-R02").click().run()  # Notify RD clears the alert
    assert not at.exception, at.exception
    assert "LOW INTAKE" not in " ".join(m.value for m in at.markdown)

    at.button(key="o-R01").click().run()  # resident dialog
    assert not at.exception, at.exception

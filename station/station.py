"""The kitchen station: watch the plate spot, scan on a steady QR card, send numbers to the dashboard.

    .venv-app/Scripts/python station/station.py --source 0                       (camera index)
    .venv-app/Scripts/python station/station.py --source data/raw/test_station --fake-workflow
    .venv-app/Scripts/python station/station.py --source clip.mp4 --meal lunch --port 8080

Screen for the robot / Zoom share: http://localhost:8080 (fullscreen the browser).
Each scan: Workflow -> resident lookup -> before/after via station.db -> POST /api/scan
through the outbox (a down dashboard never blocks scanning). Config: see workflow_client.py.
"""
import argparse
import base64
import glob
import json
import os
import sys
import threading
import time
from datetime import datetime

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from intake import before_items, compare, current_meal, group_items  # noqa: E402
from store import Store  # noqa: E402
from workflow_client import ROOT, jpeg_b64, load_config, make_client, read_qr  # noqa: E402

STABLE_S, GONE_S = 1.0, 1.5   # QR must hold still this long to scan; be gone this long to re-arm
RESULT_S = 6.0                # keep a result on screen at least this long
IMG_EXT = (".png", ".jpg", ".jpeg", ".bmp")
GREEN, AMBER, RED, GREY, BLUE = "#1f9d55", "#d97706", "#dc2626", "#475569", "#2563eb"


class Screen:
    """What the station screen shows; read by /state, /video, /annotated.jpg."""

    def __init__(self):
        self.lock = threading.Lock()
        self.live_jpg = None
        self.annotated_jpg = None
        self.state = {}
        self.history = []
        self.since = 0.0
        self.set("idle", "Place plate + card", GREY)

    def set(self, kind, text, color, sub="", items=None):
        with self.lock:
            self.state = {"kind": kind, "text": text, "color": color, "sub": sub, "items": items or [],
                          "time": datetime.now().isoformat(timespec="seconds"),
                          "seq": self.state.get("seq", 0) + 1}
            self.since = time.time()
            self.history = (self.history + [{"kind": kind, "text": text, "sub": sub}])[-30:]

    def get(self):
        with self.lock:
            return dict(self.state, history=list(self.history), age_s=round(time.time() - self.since, 1))


# --- one scan ----------------------------------------------------------------
class Scanner:
    def __init__(self, cfg, profiles, client, store, screen, meal_override=None, send_photo=True):
        self.cfg, self.profiles, self.client, self.store, self.screen = cfg, profiles, client, store, screen
        self.meal_override, self.send_photo = meal_override, send_photo
        self.residents = {r["id"]: r for r in profiles["residents"]}
        self.menu = list(profiles["menu_items"])

    def scan(self, frame, hint=None, local_qr=None):
        now = datetime.now()
        date, t = now.date().isoformat(), now.isoformat(timespec="seconds")
        meal = current_meal(now, self.profiles["meal_times"], self.meal_override)
        body = {"scan_id": None, "station_id": self.cfg["STATION_ID"], "time": t, "resident_id": None,
                "meal": meal, "phase": "before", "status": "ok", "needs_review": False, "review_reasons": [],
                "items": [], "total_pct_eaten": None, "chart_bin": None, "kcal": None, "protein_g": None,
                "annotated_jpg_b64": None}
        fracs = None
        # QR already read on the station -> CLIP picks only among this resident's items
        # (fewer look-alikes, e.g. fish vs mashed potatoes); unknown card -> the whole menu
        plan_hint = self.residents.get(local_qr, {}).get("meals", {}).get(meal) if meal else None
        try:
            res = self.client.run(frame, plan_hint or self.menu, hint=hint)
        except Exception as ex:
            print(f"workflow error: {type(ex).__name__}: {ex}")
            res = None
        if res is None:
            body["status"] = "error"
            body["review_reasons"] = ["workflow_error"]
            res = {"qr": local_qr, "estimate": {}, "annotated_image": None}
        est = res.get("estimate") or {}
        ann = res.get("annotated_image")
        body["annotated_jpg_b64"] = (ann or jpeg_b64(frame)) if self.send_photo else None
        qr = res.get("qr") or local_qr
        body["resident_id"] = qr
        body["needs_review"] = bool(est.get("needs_review"))
        body["review_reasons"] = body["review_reasons"] + list(est.get("review_reasons") or [])
        person = self.residents.get(qr)
        plan = (person or {}).get("meals", {}).get(meal) if meal else None

        if body["status"] == "error":
            pass
        elif not qr:
            body["status"] = "no_qr"
        elif person is None:
            body["status"] = "unknown_resident"
        elif not plan:
            body["status"] = "error"
            body["review_reasons"].append("no_meal_plan")
        elif not est.get("plate_found"):
            body["status"] = "no_plate"
        else:
            fracs, reasons = group_items(est.get("items"), plan)
            body["review_reasons"] += reasons
            body["needs_review"] = body["needs_review"] or bool(reasons)
            before = self.store.open_before(qr, meal, date)
            if before is None:
                body["items"] = before_items(fracs)
                if not body["items"]:
                    # not "ok": an empty BEFORE must not open the meal (the AFTER would have nothing to compare)
                    body["status"] = "error"
                    body["needs_review"] = True
                    body["review_reasons"].append("no_food")
            else:
                body["phase"] = "after"
                body.update(compare(before, fracs, self.profiles["menu_items"]))
        body["scan_id"] = f"{t}-{qr or 'noqr'}-{meal}-{body['phase']}"

        self.store.save_scan(body, date, fracs)
        self.store.enqueue(body)
        if ann:
            self.screen.annotated_jpg = base64.b64decode(ann)
        self._show(body, person)
        print(f"scan {body['scan_id']}: {body['status']} {body['phase']} "
              f"total={body['total_pct_eaten']} bin={body['chart_bin']} review={body['review_reasons']}")
        return body

    def _show(self, b, person):
        s = self.screen
        st = b["status"]
        if st == "no_qr":
            return s.set("error", "No card – show the QR", RED)
        if st == "unknown_resident":
            return s.set("error", f"Unknown card {b['resident_id']}", RED, "Check the resident's card")
        if st == "no_plate":
            return s.set("error", "Center the plate", RED, "Plate not found")
        if st == "error" and "no_food" in b["review_reasons"]:
            return s.set("error", "No food seen – try again", RED, "Center the full plate under the camera")
        if st == "error":
            why = "No meal planned now" if "no_meal_plan" in b["review_reasons"] else "Try again"
            return s.set("error", "Error – " + why, RED, ", ".join(b["review_reasons"]))
        who = f"{person['name']} – {b['meal']}"
        review = "Unsure – sent for review" if b["needs_review"] else ""
        color = AMBER if b["needs_review"] else GREEN
        if b["phase"] == "before":
            items = [{"name": i["name"], "pct": None} for i in b["items"]]
            return s.set("before", f"{who} – BEFORE saved ✓", color, review, items)
        items = [{"name": i["name"], "pct": i["pct_eaten"]} for i in b["items"]]
        nutr = f"{b['kcal']:.0f} kcal, {b['protein_g']:.0f} g protein" if b["kcal"] is not None else ""
        sub = " · ".join(x for x in (who, nutr, review) if x)
        if b["chart_bin"] is None:
            return s.set("after", "AFTER: no change measured", AMBER, sub, items)
        return s.set("after", f"AFTER: ate {b['chart_bin']}% ✓", color, sub, items)


# --- sources -----------------------------------------------------------------
def open_camera(src):
    """Camera index (DirectShow on Windows, V4L2 on the Orin) or a video file path."""
    if src.isdigit():
        api = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY
        cap = cv2.VideoCapture(int(src), api)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        for _ in range(30):  # let auto exposure settle before locking (as tools/capture.py)
            cap.read()
        exp, wb = cap.get(cv2.CAP_PROP_EXPOSURE), cap.get(cv2.CAP_PROP_WB_TEMPERATURE)
        ok_e = cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) and cap.set(cv2.CAP_PROP_EXPOSURE, exp)
        ok_w = cap.set(cv2.CAP_PROP_AUTO_WB, 0) and cap.set(cv2.CAP_PROP_WB_TEMPERATURE, wb)
        print(f"camera {src}: exposure {'locked' if ok_e else 'auto'}, wb {'locked' if ok_w else 'auto'}")
        return cap, 0.0
    cap = cv2.VideoCapture(src)
    fps = cap.get(cv2.CAP_PROP_FPS) or 15
    return cap, 1.0 / fps


def run_live(src, scanner, screen, stop):
    """Camera / video: scan when the same QR text is steady for STABLE_S; re-arm after GONE_S without it."""
    cap, frame_dt = open_camera(src)
    if not cap.isOpened():
        raise SystemExit(f"cannot open source {src}")
    armed, cand, since, last_seen, last_check = True, None, 0.0, 0.0, 0.0
    busy = threading.Event()
    while not stop.is_set():
        ok, frame = cap.read()
        if not ok:
            if frame_dt:  # video ended
                break
            time.sleep(0.05)
            continue
        screen.live_jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])[1].tobytes()
        now = time.time()
        if frame_dt:
            time.sleep(frame_dt)
        if busy.is_set() or now - last_check < 0.2:
            continue
        last_check = now
        text = read_qr(frame)
        st = screen.get()
        if text:
            last_seen = now
            if text != cand:
                cand, since = text, now
            if armed and now - since >= STABLE_S:
                armed = False
                screen.set("busy", "Reading plate…", BLUE, f"card {text}")
                busy.set()

                def work(f=frame.copy(), q=text):
                    try:
                        scanner.scan(f, local_qr=q)
                    finally:
                        busy.clear()
                threading.Thread(target=work, daemon=True).start()
            elif armed and st["kind"] != "hold":
                screen.set("hold", "Hold still…", BLUE, f"card {text}")
        elif now - last_seen > GONE_S:
            armed, cand = True, None
            if st["kind"] == "hold" or (st["kind"] not in ("idle", "busy") and st["age_s"] > RESULT_S):
                screen.set("idle", "Place plate + card", GREY)
    cap.release()


def run_folder(folder, scanner, screen, stop, pause):
    """Each image = one scan."""
    files = sorted(f for f in glob.glob(os.path.join(folder, "*")) if f.lower().endswith(IMG_EXT)
                   and not os.path.basename(f).startswith("card_"))
    for path in files:
        if stop.is_set():
            break
        frame = cv2.imread(path)
        screen.live_jpg = cv2.imencode(".jpg", frame)[1].tobytes()
        screen.set("hold", "Hold still…", BLUE, os.path.basename(path))
        time.sleep(min(pause, 1.0))
        scanner.scan(frame, hint=os.path.basename(path), local_qr=read_qr(frame))
        time.sleep(pause)


# --- web screen --------------------------------------------------------------
def make_app(screen, store):
    from fastapi import FastAPI
    from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

    app = FastAPI(title="Intake.ai station")
    blank = cv2.imencode(".jpg", np.full((480, 640, 3), 40, np.uint8))[1].tobytes()

    @app.get("/")
    def index():
        return FileResponse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "screen.html"))

    @app.get("/state")
    def state():
        s = screen.get()
        s["outbox_pending"] = len(store.pending())
        return JSONResponse(s)

    @app.get("/annotated.jpg")
    def annotated():
        return Response(screen.annotated_jpg or blank, media_type="image/jpeg",
                        headers={"Cache-Control": "no-store"})

    @app.get("/video")
    def video():
        def gen():
            while True:
                jpg = screen.live_jpg or blank
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n"
                time.sleep(0.1)
        return StreamingResponse(gen(), media_type="multipart/x-mixed-replace; boundary=frame")

    return app


def serve(app, port):
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    return server


def main():
    cfg = load_config()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--source", default=cfg["CAMERA"], help="camera index | folder of images | video file")
    ap.add_argument("--fake-workflow", action="store_true", help="no model: local QR + canned fractions")
    ap.add_argument("--meal", choices=["breakfast", "lunch", "dinner"], help="override the meal clock")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--profiles", default=os.path.join(ROOT, "config", "profiles.json"))
    ap.add_argument("--db", default=os.environ.get("STATION_DB", os.path.join(ROOT, "station.db")))
    ap.add_argument("--pause", type=float, default=3.0, help="folder mode: seconds between images")
    ap.add_argument("--exit-when-done", action="store_true", help="folder/video: quit after the last frame")
    ap.add_argument("--no-photo", action="store_true", help="don't send the annotated photo to the dashboard")
    ap.add_argument("--reset", action="store_true", help="forget all saved scans + unsent results first")
    args = ap.parse_args()

    with open(args.profiles, encoding="utf-8") as fh:
        profiles = json.load(fh)
    screen = Screen()
    store = Store(args.db)
    if args.reset:
        print(f"reset: dropped {store.reset()} saved scans")
    scan_url = cfg["DASHBOARD_URL"].rstrip("/") + "/api/scan"
    store.start_outbox(scan_url)
    client = make_client(cfg, fake=args.fake_workflow)
    scanner = Scanner(cfg, profiles, client, store, screen, args.meal, send_photo=not args.no_photo)
    serve(make_app(screen, store), args.port)
    mode = "FAKE" if args.fake_workflow else f"{cfg['INFERENCE_URL']} / {cfg['WORKFLOW_ID']}"
    print(f"station {cfg['STATION_ID']}: screen http://localhost:{args.port}  workflow {mode}  -> {scan_url}")

    stop = threading.Event()
    try:
        if os.path.isdir(args.source):
            run_folder(args.source, scanner, screen, stop, args.pause)
        else:
            run_live(args.source, scanner, screen, stop)
        if not args.exit_when_done:
            print("source done; screen stays up (Ctrl+C to quit)")
            while True:
                time.sleep(1)
        else:
            store.flush(scan_url)  # last try before exit; whatever fails stays queued in the db
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        store.stop()


if __name__ == "__main__":
    main()

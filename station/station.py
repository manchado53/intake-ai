"""The kitchen station: watch the plate spot, scan on a steady QR card, send numbers to the dashboard.

    .venv-app/Scripts/python station/station.py --source 0                       (camera index)
    .venv-app/Scripts/python station/station.py --source data/raw/test_station --fake-workflow
    .venv-app/Scripts/python station/station.py --source clip.mp4 --meal lunch --port 8080

Screen for the robot / Zoom share: http://localhost:8080 (fullscreen the browser).
Each scan: station reads the QR -> resident's items -> Workflow -> before/after via station.db -> POST /api/scan
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
        self.before_jpg = None  # owner's BEFORE, then BEFORE + AFTER; kept until another card shows
        self.after_jpg = None
        self.owner = None       # card the pictures belong to
        self.can_redo = False   # owner has a scan REDO can replace
        self.scan_request = threading.Event()  # set by the SCAN button
        self.redo_request = threading.Event()  # set by the REDO LAST button
        self.state = {}
        self.history = []
        self.since = 0.0
        self.set("idle", "Place plate + card", GREY)

    def set(self, kind, text, color, sub="", items=None, **extra):
        with self.lock:
            self.state = {"kind": kind, "text": text, "color": color, "sub": sub, "items": items or [],
                          "time": datetime.now().isoformat(timespec="seconds"),
                          "seq": self.state.get("seq", 0) + 1, **extra}
            self.since = time.time()
            self.history = (self.history + [{"kind": kind, "text": text, "sub": sub}])[-30:]

    def get(self):
        with self.lock:
            return dict(self.state, history=list(self.history), age_s=round(time.time() - self.since, 1),
                        panels=[p for p in ("before", "after") if getattr(self, p + "_jpg")],
                        can_redo=self.can_redo)


# --- one scan ----------------------------------------------------------------
class Scanner:
    def __init__(self, cfg, profiles, client, store, screen, meal_override=None, send_photo=True):
        self.cfg, self.profiles, self.client, self.store, self.screen = cfg, profiles, client, store, screen
        self.meal_override, self.send_photo = meal_override, send_photo
        self.residents = {r["id"]: r for r in profiles["residents"]}

    def scan(self, frame, hint=None, local_qr=None, redo=False):
        """One scan. redo=True: replace this card's last ok scan (same phase); the old one is
        voided only if the new one is ok, so a failed redo loses nothing."""
        now = datetime.now()
        date, t = now.date().isoformat(), now.isoformat(timespec="seconds")
        meal = current_meal(now, self.profiles["meal_times"], self.meal_override)
        body = {"scan_id": None, "station_id": self.cfg["STATION_ID"], "time": t, "resident_id": None,
                "meal": meal, "phase": "before", "status": "ok", "needs_review": False, "review_reasons": [],
                "items": [], "total_pct_eaten": None, "chart_bin": None, "kcal": None, "protein_g": None,
                "annotated_jpg_b64": None}
        fracs = None
        # The station reads the card; the Workflow only measures. It runs once we know who and
        # what they were served, with just those items as CLIP's choices (fewer look-alikes).
        qr = local_qr
        person = self.residents.get(qr)
        plan = (person or {}).get("meals", {}).get(meal) if meal else None
        res = None
        if plan:
            try:
                res = self.client.run(frame, plan, hint=hint)
            except Exception as ex:
                print(f"workflow error: {type(ex).__name__}: {ex}")
        est = (res or {}).get("estimate") or {}
        ann = (res or {}).get("annotated_image")
        body["annotated_jpg_b64"] = (ann or jpeg_b64(frame)) if self.send_photo else None
        body["resident_id"] = qr
        body["needs_review"] = bool(est.get("needs_review"))
        body["review_reasons"] = list(est.get("review_reasons") or [])
        old = self.store.last_scan(qr, meal, date) if redo and qr else None
        skip = old["scan_id"] if old else None

        if not qr:
            body["status"] = "no_qr"
        elif person is None:
            body["status"] = "unknown_resident"
        elif not plan:
            body["status"] = "error"
            body["review_reasons"].append("no_meal_plan")
        elif res is None:
            body["status"] = "error"
            body["review_reasons"].append("workflow_error")
        elif not est.get("plate_found"):
            body["status"] = "no_plate"
        else:
            fracs, reasons = group_items(est.get("items"), plan)
            body["review_reasons"] += reasons
            body["needs_review"] = body["needs_review"] or bool(reasons)
            before = self.store.open_before(qr, meal, date, skip=skip)
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
        # "-redo": a redo can land in the same second as the scan it replaces; never overwrite it
        body["scan_id"] = f"{t}-{qr or 'noqr'}-{meal}-{body['phase']}" + ("-redo" if redo else "")
        if old and body["status"] == "ok":
            body["replaces"] = old["scan_id"]
            self.store.void_scan(old["scan_id"])

        self.store.save_scan(body, date, fracs)
        self.store.enqueue(body)
        pic = base64.b64decode(ann) if ann else None
        if pic:
            self.screen.annotated_jpg = pic
        if body["status"] == "ok":
            pic = pic or base64.b64decode(jpeg_b64(frame))
            self.store.save_picture(qr, meal, date, body["phase"], pic)
            before_pic = self.store.picture(qr, meal, date, "before")
            self.screen.before_jpg = before_pic
            self.screen.after_jpg = pic if body["phase"] == "after" else None
            self.screen.owner, self.screen.can_redo = qr, True
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
            return s.set("before", f"{who} – BEFORE saved ✓", color, review or "Bring the plate back after the meal", items)
        items = [{"name": i["name"], "pct": i["pct_eaten"]} for i in b["items"]]
        nutr = f"{b['kcal']:.0f} kcal, {b['protein_g']:.0f} g protein" if b["kcal"] is not None else ""
        sub = " · ".join(x for x in (who, nutr, review) if x)
        if b["chart_bin"] is None:
            return s.set("after", "AFTER: no change measured", AMBER, sub, items)
        return s.set("after", f"AFTER: ate {b['chart_bin']}% ✓", color, sub, items)

    def ready(self, qr):
        """A card is in view and the station waits for SCAN: welcome + what the press will do.
        Returns (text, sub, next_phase). A different card than the one on screen swaps the
        pictures to this resident's: their waiting BEFORE, or nothing (next press = BEFORE)."""
        person = self.residents.get(qr)
        meal = current_meal(datetime.now(), self.profiles["meal_times"], self.meal_override)
        date = datetime.now().date().isoformat()
        has_before = bool(person and meal) and self.store.open_before(qr, meal, date) is not None
        nxt = "after" if has_before else "before"
        if qr != self.screen.owner:
            self.screen.before_jpg = self.store.picture(qr, meal, date, "before") if has_before else None
            self.screen.after_jpg = None
            self.screen.owner = qr
            self.screen.can_redo = bool(person and meal) and self.store.last_scan(qr, meal, date) is not None
        if person is None:
            return f"Card {qr}", "Unknown card – press SCAN to try", nxt
        if has_before:
            sub = f"{meal} · BEFORE saved · press SCAN for AFTER"
        else:
            sub = f"{meal or 'no meal now'} · press SCAN for BEFORE"
        return f"Welcome, {person['name']}", sub, nxt


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


def run_live(src, scanner, screen, stop, auto=False):
    """Camera / video: a card in view shows "press SCAN"; the SCAN button scans the newest frame.
    auto=True: scan on its own once the same QR text is steady for STABLE_S (old behaviour)."""
    cap, frame_dt = open_camera(src)
    if not cap.isOpened():
        raise SystemExit(f"cannot open source {src}")
    armed, cand, since, last_seen, last_check = True, None, 0.0, 0.0, 0.0
    busy = threading.Event()

    def start_scan(f, q, redo=False):
        screen.set("busy", "Redoing last scan…" if redo else "Reading plate…", BLUE, f"card {q}", card=q)
        busy.set()

        def work():
            try:
                scanner.scan(f, local_qr=q, redo=redo)
            finally:
                busy.clear()
        threading.Thread(target=work, daemon=True).start()
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
        if busy.is_set():
            screen.scan_request.clear()  # a press while reading doesn't queue a second scan
            screen.redo_request.clear()
            continue
        card_here = cand and now - last_seen <= GONE_S
        if screen.scan_request.is_set():
            screen.scan_request.clear()
            if card_here:
                armed = False
                start_scan(frame.copy(), cand)
                continue
        if screen.redo_request.is_set():
            screen.redo_request.clear()
            if card_here and cand == screen.owner:
                armed = False
                start_scan(frame.copy(), cand, redo=True)
                continue
            screen.set("error", "Show the card to redo", RED, "Put the plate + card back under the camera")
        if now - last_check < 0.2:
            continue
        last_check = now
        text = read_qr(frame)
        st = screen.get()
        if text:
            last_seen = now
            if text != cand:
                cand, since = text, now
            if auto:
                if armed and now - since >= STABLE_S:
                    armed = False
                    start_scan(frame.copy(), text)
                elif armed and st["kind"] != "hold":
                    screen.set("hold", "Hold still…", BLUE, f"card {text}")
            elif (st["kind"] == "idle" or (st["kind"] == "ready" and st.get("card") != text)
                  or (st["kind"] == "error" and st["age_s"] > RESULT_S / 2)):  # error: let them try again
                words, sub, nxt = scanner.ready(text)
                screen.set("ready", words, BLUE, sub, card=text, next=nxt)
        elif now - last_seen > GONE_S:
            armed, cand = True, None
            if st["kind"] in ("hold", "ready") or (st["kind"] not in ("idle", "busy") and st["age_s"] > RESULT_S):
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

    @app.get("/before.jpg")
    def before():
        return Response(screen.before_jpg or blank, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

    @app.get("/after.jpg")
    def after():
        return Response(screen.after_jpg or blank, media_type="image/jpeg", headers={"Cache-Control": "no-store"})

    @app.post("/scan")
    def scan():
        ready = screen.get()["kind"] == "ready"
        if ready:
            screen.scan_request.set()
        return JSONResponse({"ok": ready})

    @app.post("/redo")
    def redo():
        ok = screen.can_redo and screen.get()["kind"] != "busy"
        if ok:
            screen.redo_request.set()
        return JSONResponse({"ok": ok})

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
    ap.add_argument("--auto", action="store_true", help="scan on a steady card without waiting for SCAN")
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
            run_live(args.source, scanner, screen, stop, auto=args.auto)
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

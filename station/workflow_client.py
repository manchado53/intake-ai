"""Calls the `intake-plate` Workflow (real) or makes up a plausible answer (fake).

Both return one contract-1 dict (docs/contracts.md section 1):
    {"estimate": {...}, "annotated_image": <base64 jpeg> | None}

Config comes from env vars, then the repo's .env (the main checkout's .env too, when running
from a worktree): INFERENCE_URL, WORKFLOW_ID, ROBOFLOW_API_KEY, DASHBOARD_URL, STATION_ID, CAMERA, WORKFLOW_SPEC (inline spec path).
"""
import base64
import json
import os
import re
from pathlib import Path

import cv2
import numpy as np
from dotenv import dotenv_values

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MAIN_ROOT = re.split(r"[\\/]\.claude[\\/]worktrees[\\/]", ROOT)[0]
WORKSPACE = "manchado53"
DEFAULTS = {"INFERENCE_URL": "https://serverless.roboflow.com", "WORKFLOW_ID": "intake-plate",
            "DASHBOARD_URL": "http://localhost:8000", "STATION_ID": "laptop-station", "CAMERA": "0"}


def load_config():
    """env var > local .env > main checkout .env > default. The key is never printed."""
    cfg = dict(DEFAULTS)
    for path in (os.path.join(MAIN_ROOT, ".env"), os.path.join(ROOT, ".env")):
        if os.path.exists(path):
            cfg.update({k: v for k, v in dotenv_values(path).items() if v})
    cfg.update({k: os.environ[k] for k in list(DEFAULTS) + ["ROBOFLOW_API_KEY", "WORKFLOW_SPEC"] if os.environ.get(k)})
    return cfg


def jpeg_b64(img, quality=80):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf.tobytes()).decode() if ok else None


def annotated_b64(value):
    """Contract 1 allows {"type": "base64", "value": ...} or a bare base64 string."""
    if isinstance(value, dict):
        return value.get("value")
    return value if isinstance(value, str) else None


def normalize(result):
    """Make a raw Workflow output dict look exactly like contract 1."""
    est = result.get("estimate") or {}
    if isinstance(est, str):
        est = json.loads(est)
    return {"estimate": est,
            "annotated_image": annotated_b64(result.get("annotated_image"))}


class WorkflowClient:
    """Real mode: Roboflow Inference (hosted or the Orin's local server)."""

    def __init__(self, cfg):
        from inference_sdk import InferenceHTTPClient
        self.cfg = cfg
        self.client = InferenceHTTPClient(api_url=cfg["INFERENCE_URL"], api_key=cfg.get("ROBOFLOW_API_KEY"))

    def run(self, frame, menu, hint=None):
        # WORKFLOW_SPEC = path to a spec JSON: sent inline, so no fetch from Roboflow (offline-safe)
        spec_path = self.cfg.get("WORKFLOW_SPEC")
        where = ({"specification": json.loads(Path(spec_path).read_text(encoding="utf-8"))} if spec_path
                 else {"workflow_id": self.cfg["WORKFLOW_ID"]})
        out = self.client.run_workflow(workspace_name=WORKSPACE, images={"image": frame},
                                       parameters={"menu": menu}, **where)
        return normalize(out[0])


# --- fake --------------------------------------------------------------------
# meal_03 (white fish + pasta + carrots): s0 full, s4 after ~40% by weight, s9 cleared.
CANNED = {
    "s0": {"white fish": [0.110, 0.068], "pasta": [0.164], "carrots": [0.070]},
    "s4": {"white fish": [0.105], "pasta": [0.068], "carrots": [0.030, 0.012, 0.009]},
    "s9": {"carrots": [0.004]},
}
_qr = cv2.QRCodeDetector()


def detect_qr(frame):
    """(text or None, corner points or None)."""
    try:
        text, pts, _ = _qr.detectAndDecode(frame)
    except cv2.error:
        return None, None
    return text or None, pts


def read_qr(frame):
    return detect_qr(frame)[0]


def plate_mask(frame, qr_pts=None):
    """Biggest bright blob = the plate (good enough for a fake). The white QR card is cut out."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    m = cv2.inRange(hsv, (0, 0, 185), (180, 255, 255))  # warm light: plate is bright, not grey
    if qr_pts is not None:
        x, y, w, h = cv2.boundingRect(qr_pts.reshape(-1, 2).astype(np.int32))
        pad = max(w, h) // 3  # the card's white border around the code
        m[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None
    i = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    if stats[i, cv2.CC_STAT_AREA] < 0.08 * m.size:
        return None
    hull = cv2.convexHull(cv2.findNonZero((lab == i).astype(np.uint8)))
    full = np.zeros_like(m)
    cv2.fillConvexPoly(full, hull, 255)
    return full


def color_fracs(frame, plate):
    """Orange -> carrots, yellow -> pasta, by hue, inside the plate."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    area = max(int((plate > 0).sum()), 1)
    out = {}
    for name, lo, hi in [("carrots", (5, 160, 80), (19, 255, 255)), ("pasta", (19, 145, 150), (35, 255, 255))]:
        px = int(((cv2.inRange(hsv, lo, hi) > 0) & (plate > 0)).sum())
        if px > 0.002 * area:
            out[name] = [round(px / area, 3)]
    return out


class FakeWorkflowClient:
    """Contract-1 answers without a model: canned or color-threshold fractions (QR only to find the plate)."""

    def run(self, frame, menu, hint=None):
        qr, pts = detect_qr(frame)
        plate = plate_mask(frame, pts)
        key = next((k for k in CANNED if hint and re.search(rf"(^|[_\-.]){k}([_\-.]|$)", hint)), None)
        if plate is None:
            fracs = {}
        elif key:
            fracs = CANNED[key]
        else:
            fracs = color_fracs(frame, plate)
        items, ys = [], np.linspace(0.3, 0.7, max(len(fracs), 1))
        for (name, blobs), y in zip(fracs.items(), ys):
            for j, f in enumerate(blobs):
                items.append({"name": name, "clip_score": 0.8, "det_conf": 0.9, "area_frac": f,
                              "centroid": [round(0.4 + 0.1 * j, 2), round(float(y), 2)]})
        plate_px = int((plate > 0).sum()) if plate is not None else 0
        est = {"plate_found": plate is not None, "plate_area_px": plate_px,
               "food_frac_total": round(sum(i["area_frac"] for i in items), 3),
               "needs_review": plate is None, "review_reasons": [] if plate is not None else ["no_plate"],
               "items": items}
        return {"estimate": est, "annotated_image": jpeg_b64(self._draw(frame, plate, items, qr))}

    @staticmethod
    def _draw(frame, plate, items, qr):
        img = frame.copy()
        if plate is not None:
            cs, _ = cv2.findContours(plate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(img, cs, -1, (255, 200, 0), 3)
        h, w = img.shape[:2]
        for it in items:
            x, y = int(it["centroid"][0] * w), int(it["centroid"][1] * h)
            cv2.putText(img, f"{it['name']} {it['area_frac']:.2f}", (x - 60, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 0), 4)
            cv2.putText(img, f"{it['name']} {it['area_frac']:.2f}", (x - 60, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (255, 255, 255), 1)
        cv2.putText(img, f"FAKE  qr={qr}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        return img


def make_client(cfg, fake=False):
    return FakeWorkflowClient() if fake else WorkflowClient(cfg)

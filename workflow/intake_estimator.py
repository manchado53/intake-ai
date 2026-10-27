"""Intake estimator: food masks + plate mask -> the `estimate` dict of docs/contracts.md (section 1).

No network. `workflow/build_spec.py` pastes this whole file into the Workflow's three Custom Python
blocks (`split_menu` = MenuSplit, `crop_name` = CropName, `run` = IntakeEstimator), so keep it self-contained
(numpy + cv2 only, both preloaded in Roboflow's Custom Python sandbox).

Test: .venv-app/Scripts/python -m pytest tests/test_workflow_estimator.py
"""
import cv2
import numpy as np

DET_CONF_MIN = 0.5
CLIP_SCORE_MIN = 0.5
CLIP_LOGIT_SCALE = 100.0  # CLIP's own logit scale; turns raw cosine sims into a softmax over the menu
# Hosted CLIP compare returns 500 for more than 8 prompts (measured 2026-10-27), so the menu goes
# to CLIP in two chunks of <= 8; menus up to 16 words are supported.
CLIP_MAX_PROMPTS = 8


def clip_pick(similarities, menu):
    """Raw CLIP cosine similarities (one per menu word) -> (best name, softmax prob of it)."""
    sims = np.asarray(similarities, dtype=float)
    if sims.size == 0 or not menu:
        return "unknown", 0.0
    z = CLIP_LOGIT_SCALE * (sims - sims.max())
    p = np.exp(z) / np.exp(z).sum()
    i = int(np.argmax(p))
    return str(menu[i]), float(p[i])


def estimate(plate_masks, foods):
    """plate_masks: list of HxW bool arrays (largest one is used).
    foods: list of dicts {"mask": HxW bool, "name": str, "clip_score": float, "det_conf": float}.
    Returns the contract `estimate` dict."""
    plates = [np.asarray(m, dtype=bool) for m in plate_masks]
    plate = max(plates, key=lambda m: int(m.sum())) if plates else None
    plate_px = int(plate.sum()) if plate is not None else 0
    plate_found = plate_px > 0

    items = []
    for f in foods:
        mask = np.asarray(f["mask"], dtype=bool)
        h, w = mask.shape
        px = int(mask.sum())
        if px:
            ys, xs = np.nonzero(mask)
            centroid = [round(float(xs.mean()) / w, 4), round(float(ys.mean()) / h, 4)]
        else:
            centroid = [None, None]
        items.append({
            "name": str(f["name"]),
            "clip_score": round(float(f["clip_score"]), 4),
            "det_conf": round(float(f["det_conf"]), 4),
            "area_frac": round(px / plate_px, 4) if plate_found else 0.0,
            "centroid": centroid,
        })

    reasons = []
    if not plate_found:
        reasons.append("no_plate")
    if any(it["det_conf"] < DET_CONF_MIN for it in items):
        reasons.append("low_det_conf")
    if any(it["clip_score"] < CLIP_SCORE_MIN for it in items):
        reasons.append("low_clip")

    return {
        "plate_found": plate_found,
        "plate_area_px": plate_px,
        "food_frac_total": round(sum(it["area_frac"] for it in items), 4),
        "needs_review": bool(reasons),
        "review_reasons": reasons,
        "items": items,
    }


def read_qr(bgr):
    """Decoded text of the QR card in a BGR image, or None.
    Single-code detector first: the multi-code one (used by roboflow_core/qr_code_detector@v1)
    misses clean cards and the block crashes on images without a code."""
    det = cv2.QRCodeDetector()
    try:
        text, _, _ = det.detectAndDecode(bgr)
        if text:
            return str(text)
        ok, texts, _, _ = det.detectAndDecodeMulti(bgr)
        if ok and texts:
            return next((str(t) for t in texts if t), None)
    except cv2.error:
        pass
    return None


def menu_chunks(menu):
    """Menu -> (head, tail) prompt lists for the two CLIP steps; tail is never empty
    (CLIP rejects an empty class list), its sims are dropped when the menu fits in head."""
    menu = [str(m) for m in menu]
    head = menu[:CLIP_MAX_PROMPTS]
    tail = menu[CLIP_MAX_PROMPTS:2 * CLIP_MAX_PROMPTS] or menu[:1]
    return head, tail


def join_sims(head_sims, tail_sims, n_menu):
    sims = list(head_sims)
    if n_menu > CLIP_MAX_PROMPTS:
        sims += list(tail_sims)
    return sims[:n_menu]


def split_menu(self, menu):
    """Custom Python block MenuSplit."""
    head, tail = menu_chunks(menu)
    return {"head": head, "tail": tail}


def crop_name(self, sims_head, sims_tail, menu):
    """Custom Python block CropName: one crop's CLIP sims -> menu name (feeds the label block)."""
    menu = [str(m) for m in menu]
    sims = join_sims(sims_head or [], sims_tail or [], len(menu))
    return {"name": clip_pick(sims, menu[:len(sims)])[0]}


def run(self, image, predictions, foods, sims_head, sims_tail, menu):
    """Custom Python block IntakeEstimator.
    predictions: seg model sv.Detections (plate + food-item); foods: the food-item subset, in the
    same order as the CLIP crops; sims_head / sims_tail: per-crop raw CLIP sims vs menu_chunks()."""
    menu = [str(m) for m in menu]
    names = predictions.data.get("class_name", [])
    plate_masks = [predictions.mask[i] for i in range(len(predictions))
                   if names[i] == "plate" and predictions.mask is not None]
    sh = list(sims_head) if sims_head is not None else []
    st = list(sims_tail) if sims_tail is not None else []
    food_list = []
    for i in range(len(foods)):
        sims = join_sims(sh[i] if i < len(sh) else [], st[i] if i < len(st) else [], len(menu))
        name, score = clip_pick(sims, menu[:len(sims)])
        food_list.append({"mask": foods.mask[i], "name": name, "clip_score": score,
                          "det_conf": float(foods.confidence[i])})
    return {"estimate": estimate(plate_masks, food_list), "qr": read_qr(image.numpy_image)}

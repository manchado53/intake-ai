"""Intake estimator: food masks + plate mask -> the `estimate` dict of docs/contracts.md (section 1).

No network. `workflow/build_spec.py` pastes this whole file into the Workflow's two Custom Python
blocks (`crop_name` = CropName, `run` = IntakeEstimator), so keep it self-contained
(numpy only, preloaded in Roboflow's Custom Python sandbox).

The menu is one resident's planned items for this meal (the station reads the QR card and sends
them), at most 8 words: hosted CLIP compare returns 500 above 8 prompts (measured 2026-10-27).

Test: .venv-app/Scripts/python -m pytest tests/test_workflow_estimator.py
"""
import numpy as np

DET_CONF_MIN = 0.5
CLIP_SCORE_MIN = 0.5
CLIP_LOGIT_SCALE = 100.0  # CLIP's own logit scale; turns raw cosine sims into a softmax over the menu


def clip_probs(similarities, menu):
    """Raw CLIP cosine similarities (one per menu word) -> softmax prob per menu word."""
    sims = np.asarray(similarities, dtype=float)
    if sims.size == 0 or not menu:
        return {}
    z = CLIP_LOGIT_SCALE * (sims - sims.max())
    p = np.exp(z) / np.exp(z).sum()
    return {str(m): float(v) for m, v in zip(menu, p)}


def clip_pick(similarities, menu):
    """Raw CLIP cosine similarities (one per menu word) -> (best name, softmax prob of it)."""
    probs = clip_probs(similarities, menu)
    if not probs:
        return "unknown", 0.0
    name = max(probs, key=probs.get)
    return name, probs[name]


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
            # per-menu-word probs: lets the station pick among one resident's items
            "scores": {k: round(float(v), 4) for k, v in (f.get("scores") or {}).items()},
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


def crop_name(self, sims, menu):
    """Custom Python block CropName: one crop's CLIP sims -> menu name (feeds the label block)."""
    menu = [str(m) for m in menu]
    return {"name": clip_pick(list(sims or []), menu)[0]}


def run(self, predictions, foods, sims, menu):
    """Custom Python block IntakeEstimator.
    predictions: seg model sv.Detections (plate + food-item); foods: the food-item subset, in the
    same order as the CLIP crops; sims: per-crop raw CLIP cosine sims vs the menu words."""
    menu = [str(m) for m in menu]
    names = predictions.data.get("class_name", [])
    plate_masks = [predictions.mask[i] for i in range(len(predictions))
                   if names[i] == "plate" and predictions.mask is not None]
    per_crop = list(sims) if sims is not None else []
    food_list = []
    for i in range(len(foods)):
        s = list(per_crop[i]) if i < len(per_crop) else []
        name, score = clip_pick(s, menu[:len(s)])
        food_list.append({"mask": foods.mask[i], "name": name, "clip_score": score,
                          "det_conf": float(foods.confidence[i]), "scores": clip_probs(s, menu[:len(s)])})
    return {"estimate": estimate(plate_masks, food_list)}

"""Unit tests for workflow/intake_estimator.py (no network).

Run: .venv-app/Scripts/python -m pytest tests/test_workflow_estimator.py
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "workflow"))
from intake_estimator import clip_pick, crop_name, estimate  # noqa: E402

H, W = 200, 300


def circle(cx, cy, r):
    yy, xx = np.mgrid[:H, :W]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2


def square(x0, y0, side):
    m = np.zeros((H, W), bool)
    m[y0:y0 + side, x0:x0 + side] = True
    return m


def food(mask, name="pasta", clip=0.9, conf=0.9):
    return {"mask": mask, "name": name, "clip_score": clip, "det_conf": conf}


def test_exact_fractions_and_centroid():
    plate = circle(150, 100, 80)
    plate_px = int(plate.sum())
    out = estimate([plate], [food(square(100, 60, 20)), food(square(160, 100, 10), "carrots")])
    assert out["plate_found"] is True
    assert out["plate_area_px"] == plate_px
    assert out["items"][0]["area_frac"] == round(400 / plate_px, 4)
    assert out["items"][1]["area_frac"] == round(100 / plate_px, 4)
    assert out["food_frac_total"] == pytest.approx(500 / plate_px, abs=2e-4)
    # square 100..119 x 60..79 -> centre (109.5, 69.5)
    assert out["items"][0]["centroid"] == [round(109.5 / W, 4), round(69.5 / H, 4)]
    assert out["needs_review"] is False and out["review_reasons"] == []


def test_largest_plate_is_used():
    small, big = circle(50, 50, 20), circle(150, 100, 80)
    out = estimate([small, big], [food(square(100, 60, 20))])
    assert out["plate_area_px"] == int(big.sum())


def test_no_plate():
    out = estimate([], [food(square(10, 10, 5))])
    assert out["plate_found"] is False
    assert out["needs_review"] is True
    assert "no_plate" in out["review_reasons"]
    assert out["items"][0]["area_frac"] == 0.0


def test_low_det_conf():
    out = estimate([circle(150, 100, 80)], [food(square(100, 60, 20), conf=0.3)])
    assert out["needs_review"] is True
    assert out["review_reasons"] == ["low_det_conf"]


def test_low_clip():
    out = estimate([circle(150, 100, 80)], [food(square(100, 60, 20), clip=0.2)])
    assert out["needs_review"] is True
    assert out["review_reasons"] == ["low_clip"]


def test_clip_pick_softmax():
    name, p = clip_pick([0.20, 0.30, 0.21], ["fish", "pasta", "carrots"])
    assert name == "pasta"
    assert p > 0.99
    name, p = clip_pick([0.25, 0.25], ["a", "b"])
    assert p == pytest.approx(0.5)


def test_crop_name_picks_best_word():
    assert crop_name(None, [0.20, 0.31, 0.22], ["white fish", "pasta", "carrots"]) == {"name": "pasta"}

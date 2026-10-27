"""Meal math tests (docs/contracts.md section 2).  Run: pytest tests/test_station_intake.py"""
import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from station.intake import chart_bin, compare, current_meal, group_items  # noqa: E402

MENU = ["white fish", "pasta", "carrots"]
NUTR = {"white fish": {"kcal": 120, "protein_g": 26}, "pasta": {"kcal": 220, "protein_g": 8},
        "carrots": {"kcal": 27, "protein_g": 1}}
MEAL_TIMES = {"breakfast": ["06:00", "10:00"], "lunch": ["10:00", "15:00"], "dinner": ["15:00", "21:00"]}


def blob(name, frac, **kw):
    return {"name": name, "clip_score": 0.8, "det_conf": 0.9, "area_frac": frac, **kw}


def by_name(res):
    return {i["name"]: i for i in res["items"]}


def test_normal_matches_contract_items():
    before, _ = group_items([blob("white fish", 0.178), blob("pasta", 0.164), blob("carrots", 0.070)], MENU)
    after, _ = group_items([blob("white fish", 0.036), blob("pasta", 0.123), blob("carrots", 0.070)], MENU)
    res = compare(before, after, NUTR)
    it = by_name(res)
    assert it["white fish"]["pct_eaten"] == 79.8
    assert it["white fish"]["kcal"] == 95.8 and it["white fish"]["protein_g"] == 20.7
    assert it["pasta"]["pct_eaten"] == 25.0 and it["pasta"]["kcal"] == 55.0
    assert it["carrots"]["pct_eaten"] == 0.0 and it["carrots"]["kcal"] == 0.0
    # total from the sums: 1 - 0.229 / 0.412
    assert res["total_pct_eaten"] == 44.4
    assert res["chart_bin"] == 50
    assert res["kcal"] == pytest.approx(95.8 + 55.0 + 0.0, abs=0.15)


def test_item_eaten_fully_missing_after():
    before, _ = group_items([blob("pasta", 0.2), blob("carrots", 0.1)], MENU)
    after, _ = group_items([blob("carrots", 0.1)], MENU)
    it = by_name(compare(before, after, NUTR))
    assert it["pasta"]["pct_eaten"] == 100.0 and it["pasta"]["after_frac"] == 0.0
    assert it["pasta"]["kcal"] == 220.0


def test_after_bigger_than_before_clips_to_zero():
    res = compare({"pasta": 0.10}, {"pasta": 0.13}, NUTR)
    assert res["items"][0]["pct_eaten"] == 0.0
    assert res["total_pct_eaten"] == 0.0 and res["chart_bin"] == 0


def test_unknown_blob_ignored_and_flagged():
    sums, reasons = group_items([blob("pasta", 0.2), blob("pizza", 0.3)], MENU)
    assert sums["pasta"] == 0.2 and "pizza" not in sums
    assert reasons == ["off_menu"]


def test_unknown_blob_reassigned_when_scores_given():
    sums, reasons = group_items([blob("rice", 0.05, scores={"rice": 0.6, "pasta": 0.3, "carrots": 0.1})], MENU)
    assert sums["pasta"] == 0.05 and reasons == []


def test_two_blobs_same_food_summed():
    sums, _ = group_items([blob("white fish", 0.1), blob("white fish", 0.08)], MENU)
    assert sums["white fish"] == pytest.approx(0.18)


def test_before_zero_skipped():
    res = compare({"pasta": 0.2, "carrots": 0.0}, {"pasta": 0.1}, NUTR)
    assert [i["name"] for i in res["items"]] == ["pasta"]
    assert res["total_pct_eaten"] == 50.0


@pytest.mark.parametrize("pct,binv", [(0, 0), (12.4, 0), (12.5, 25), (37.4, 25), (37.5, 50),
                                      (62.6, 75), (87.5, 100), (100, 100)])
def test_bin_rounding(pct, binv):
    assert chart_bin(pct) == binv


def test_current_meal_and_override():
    assert current_meal(datetime(2026, 10, 28, 12, 5), MEAL_TIMES) == "lunch"
    assert current_meal(datetime(2026, 10, 28, 15, 0), MEAL_TIMES) == "dinner"
    assert current_meal(datetime(2026, 10, 28, 23, 0), MEAL_TIMES) is None
    assert current_meal(datetime(2026, 10, 28, 23, 0), MEAL_TIMES, "lunch") == "lunch"

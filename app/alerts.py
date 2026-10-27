"""Low-intake alert rule and meal grouping. Pure functions, no I/O.

Rule: the last 3 *recorded* meals all under 50% -> notify the RD.
Missing data is not 0%: a meal with no after-scan is skipped, it neither counts as low nor breaks the run.
"""

LOW_PCT = 50.0
RUN = 3


def low_streak(pcts, threshold: float = LOW_PCT, run: int = RUN) -> bool:
    """pcts: meal totals oldest -> newest; None = missing (skipped)."""
    recorded = [p for p in pcts if p is not None]
    return len(recorded) >= run and all(p < threshold for p in recorded[-run:])


def meal_records(scans) -> list[dict]:
    """Group contract-2 scans into one record per (resident, date, meal), oldest first.

    pct/kcal/protein come from the latest ok after-scan; a meal with only a before-scan
    gets pct None (missing). Non-ok scans are ignored.
    """
    meals: dict[tuple, dict] = {}
    for s in sorted(scans, key=lambda s: s["time"]):
        if s.get("status") != "ok" or not s.get("resident_id") or not s.get("meal"):
            continue
        key = (s["resident_id"], s["time"][:10], s["meal"])
        rec = meals.setdefault(key, {
            "resident_id": key[0], "date": key[1], "meal": key[2], "time": s["time"],
            "pct": None, "chart_bin": None, "kcal": None, "protein_g": None, "synthetic": False,
        })
        if s.get("phase") == "after" and s.get("total_pct_eaten") is not None:
            rec.update(time=s["time"], pct=s["total_pct_eaten"], chart_bin=s.get("chart_bin"),
                       kcal=s.get("kcal"), protein_g=s.get("protein_g"),
                       synthetic=bool(s.get("synthetic")))
    return sorted(meals.values(), key=lambda r: r["time"])


def resident_alerts(records, residents) -> list[dict]:
    """One alert per resident whose last 3 recorded meals were all low."""
    out = []
    for r in residents:
        mine = [m for m in records if m["resident_id"] == r["id"]]
        if low_streak([m["pct"] for m in mine]):
            last = [m for m in mine if m["pct"] is not None][-RUN:]
            out.append({"resident": r, "meals": last})
    return out

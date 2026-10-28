"""Insights only the camera can give: protein vs goal, items a resident keeps leaving, food that
comes back to the kitchen. Pure functions, no I/O (like alerts.py).

Item-level numbers come from each meal's latest ok after-scan (`items[].pct_eaten`).
"""
from datetime import date, timedelta

LEFT_PCT = 50.0   # an item under this % eaten counts as "left"
LEFT_LAST = 6     # look at the last N times an item was served to the resident
LEFT_MIN = 4      # ...and flag it when it was left at least this many times
ON_TRACK = 0.75   # protein eaten so far >= 75% of the protein served so far


def meal_afters(scans) -> list[dict]:
    """Latest ok after-scan per (resident, date, meal), oldest first."""
    last = {}
    for s in sorted(scans, key=lambda s: s["time"]):
        if s.get("status") == "ok" and s.get("phase") == "after" and s.get("resident_id") and s.get("meal"):
            last[(s["resident_id"], s["time"][:10], s["meal"])] = s
    return sorted(last.values(), key=lambda s: s["time"])


def day_nutrition(scans, menu_items, rid, day: str) -> dict:
    """One resident, one day: kcal + protein eaten, protein served, meals recorded."""
    out = {"kcal": 0.0, "protein_g": 0.0, "protein_served_g": 0.0, "meals": 0}
    for s in meal_afters(scans):
        if s["resident_id"] != rid or s["time"][:10] != day:
            continue
        out["meals"] += 1
        for it in s.get("items") or []:
            out["kcal"] += it.get("kcal") or 0
            out["protein_g"] += it.get("protein_g") or 0
            out["protein_served_g"] += menu_items.get(it["name"], {}).get("protein_g", 0)
    return out


def protein_on_track(day: dict) -> bool | None:
    """On track = ate at least 75% of the protein served so far today. None = no meals yet."""
    if not day["meals"] or not day["protein_served_g"]:
        return None
    return day["protein_g"] >= ON_TRACK * day["protein_served_g"]


def left_items(scans, rid, last=LEFT_LAST, min_left=LEFT_MIN) -> list[dict]:
    """Items this resident left (< 50% eaten) at least `min_left` of the last `last` times served."""
    seen: dict[str, list[bool]] = {}
    for s in meal_afters(scans):
        if s["resident_id"] != rid:
            continue
        for it in s.get("items") or []:
            if it.get("pct_eaten") is not None:
                seen.setdefault(it["name"], []).append(it["pct_eaten"] < LEFT_PCT)
    out = []
    for name, hist in seen.items():
        recent = hist[-last:]
        if sum(recent) >= min_left:
            out.append({"name": name, "left": sum(recent), "served": len(recent)})
    return sorted(out, key=lambda x: (-x["left"] / x["served"], x["name"]))


def kitchen_waste(scans, menu_items, today: date, days=7) -> list[dict]:
    """Per menu item over the last `days` days: times served, average % left, $ left on plates."""
    start = (today - timedelta(days=days - 1)).isoformat()
    acc: dict[str, dict] = {}
    for s in meal_afters(scans):
        if not (start <= s["time"][:10] <= today.isoformat()):
            continue
        for it in s.get("items") or []:
            if it.get("pct_eaten") is None:
                continue
            left = max(0.0, min(100.0, 100 - it["pct_eaten"]))
            a = acc.setdefault(it["name"], {"name": it["name"], "served": 0, "left_sum": 0.0, "usd": 0.0})
            a["served"] += 1
            a["left_sum"] += left
            a["usd"] += left / 100 * menu_items.get(it["name"], {}).get("cost_usd", 0.0)
    out = [{"name": a["name"], "served": a["served"], "pct_left": round(a["left_sum"] / a["served"], 1),
            "usd": round(a["usd"], 2)} for a in acc.values()]
    return sorted(out, key=lambda x: -x["usd"])

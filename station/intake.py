"""Meal math for the station: pure functions, no I/O (docs/contracts.md sections 1-3).

    group_items(workflow_items, resident_menu) -> ({name: area_frac}, review_reasons)
    compare(before, after, menu_items)          -> per-item rows + totals for an "after" scan
    current_meal(now, meal_times, override)     -> "breakfast" | "lunch" | "dinner" | None
"""
from datetime import datetime, time as dtime

BINS = (0, 25, 50, 75, 100)


def _best_on_menu(blob, resident_menu):
    """Resident item with the highest similarity for an off-menu blob, or None.

    The Workflow only promises `name` + `clip_score`; if it also sends per-word scores
    (`scores` or `clip_scores`: {menu word: score}) we use them to reassign the blob.
    """
    scores = blob.get("scores") or blob.get("clip_scores") or {}
    cands = [(s, n) for n, s in scores.items() if n in resident_menu and s is not None]
    return max(cands)[1] if cands else None


def group_items(workflow_items, resident_menu):
    """Sum blob area_frac per name, keeping only this resident's menu words.

    Returns ({name: area_frac} with every resident item present (0.0 if not seen),
             review reasons added here, e.g. ["off_menu"]).
    """
    sums = {name: 0.0 for name in resident_menu}
    reasons = []
    for blob in workflow_items or []:
        name = blob.get("name")
        if name not in sums:
            name = _best_on_menu(blob, resident_menu)
            if name is None:
                if "off_menu" not in reasons:
                    reasons.append("off_menu")
                continue
        sums[name] += float(blob.get("area_frac") or 0.0)
    return {n: round(v, 4) for n, v in sums.items()}, reasons


def pct_eaten(before_frac, after_frac):
    """clip(100 * (1 - after/before), 0, 100); None when before is 0 (item skipped)."""
    if not before_frac:
        return None
    return max(0.0, min(100.0, 100.0 * (1.0 - (after_frac or 0.0) / before_frac)))


def chart_bin(total_pct):
    """Nearest of 0/25/50/75/100 (halves round up: 12.5 -> 25, 37.5 -> 50)."""
    if total_pct is None:
        return None
    return min(BINS, key=lambda b: (abs(b - total_pct), -b))


def before_items(before):
    """Contract-2 item rows for a "before" scan (after fields are null)."""
    return [{"name": n, "before_frac": round(f, 4), "after_frac": None, "pct_eaten": None,
             "kcal": None, "protein_g": None} for n, f in before.items() if f > 0]


def _mean(a, d):
    """Average of the area % and the depth %; area alone when depth is missing."""
    return a if d is None or a is None else (a + d) / 2


def compare(before, after, menu_items, before_vol=None, after_vol=None):
    """Per-item % eaten + nutrition for an "after" scan.

    before / after: {name: area_frac}; an item missing from `after` counts as 0 (all eaten).
    before_vol / after_vol: {name: volume} from depth, or None. With both, % eaten = mean of the
    area % and the depth % (area errs low on piles, depth errs high; the mean cancels most of both,
    docs/experiments/2026-10-28-depth-plate-shape.md).
    Returns {"items": [...], "total_pct_eaten", "chart_bin", "kcal", "protein_g"}.
    """
    use_vol = before_vol is not None and after_vol is not None
    items, sum_b, sum_a, sum_bv, sum_av, kcal, prot = [], 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    for name, b in before.items():
        a = after.get(name, 0.0) or 0.0
        pa = pct_eaten(b, a)
        if pa is None:
            continue
        bv, av = (before_vol.get(name), after_vol.get(name, 0.0) or 0.0) if use_vol else (None, None)
        pd = pct_eaten(bv, av) if use_vol else None
        p = round(_mean(pa, pd), 1)  # nutrition from the reported %, so the numbers on screen add up
        info = menu_items.get(name, {})
        k = p / 100 * info.get("kcal", 0)
        g = p / 100 * info.get("protein_g", 0)
        items.append({"name": name, "before_frac": round(b, 4), "after_frac": round(a, 4),
                      "pct_eaten": p, "pct_area": round(pa, 1),
                      "pct_depth": None if pd is None else round(pd, 1),
                      "kcal": round(k, 1), "protein_g": round(g, 1)})
        sum_b, sum_a, kcal, prot = sum_b + b, sum_a + a, kcal + k, prot + g
        if pd is not None:
            sum_bv, sum_av = sum_bv + bv, sum_av + av
    # same clip rule on the sums; per-item after > before can't push the total below 0
    total = _mean(pct_eaten(sum_b, sum_a), pct_eaten(sum_bv, sum_av) if use_vol else None)
    return {"items": items,
            "total_pct_eaten": None if total is None else round(total, 1),
            "chart_bin": chart_bin(total),
            "kcal": round(kcal, 1) if items else None,
            "protein_g": round(prot, 1) if items else None}


def _hhmm(s):
    h, m = s.split(":")
    return dtime(int(h), int(m))


def current_meal(now, meal_times, override=None):
    """Meal whose [start, end) window holds `now`; `override` wins if given."""
    if override:
        return override
    t = (now or datetime.now()).time()
    for meal, (start, end) in meal_times.items():
        if _hhmm(start) <= t < _hhmm(end):
            return meal
    return None

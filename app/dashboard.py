"""Intake.ai dietitian view: one "Today" screen. Who needs me -> every resident (protein vs goal, items
left) -> what comes back to the kitchen -> live kitchen feed.

Run (repo root): .venv-app/Scripts/python -m streamlit run app/dashboard.py --server.port 8501
Reads the same SQLite DB the API server writes (env INTAKE_DB, default app/dashboard.db).
"""
import base64
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import alerts, cards, insights, store  # noqa: E402

REFRESH_S = 2
FEED_LIMIT = 8
MEALS = ("breakfast", "lunch", "dinner")
ACCENT, LOW, INK = "#8B5CF6", "#EF4444", "#251742"  # match .streamlit/config.toml
CSS = """<style>
[data-testid="stSidebarCollapsedControl"], [data-testid="stSidebar"] { display: none; }
[data-testid="stHeader"] { background: #251742; border-bottom: 3px solid #C29AF6; height: 4rem; }
[data-testid="stHeader"] * { color: #F4F2EC !important; }
[data-testid="stToolbar"] button:hover { background: #3A2766; }
h1, h2, h3 { letter-spacing: -.03em; }
h1 { color: #251742; }
[data-testid="stMetricLabel"] p, [data-testid="stCaptionContainer"], [data-testid="stSidebar"] label p {
  font-family: "Geist Mono", ui-monospace, monospace; text-transform: uppercase; letter-spacing: .08em; font-size: .75rem; }
[data-testid="stMetricValue"] { letter-spacing: -.03em; }
[data-testid="stProgress"] div[role="progressbar"] > div > div { background: linear-gradient(90deg, #6F3FD8, #C29AF6); }
.lbl { font-family: "Geist Mono", ui-monospace, monospace; text-transform: uppercase; letter-spacing: .1em;
  font-size: .78rem; color: #6F3FD8; margin: .4rem 0 .2rem; }
.lbl::before { content: "■  "; color: #C29AF6; }
</style>"""

st.set_page_config(page_title="Intake.ai – dietitian view", page_icon="🍽️", layout="wide",
                   initial_sidebar_state="collapsed")

profiles = store.load_profiles()
RESIDENTS = {r["id"]: r for r in profiles["residents"]}
MENU = profiles["menu_items"]
ACTION = "check chewing, ask about a soft diet or a swap"


def load():
    con = store.connect()
    try:
        scans, acks = store.list_scans(con), store.list_acks(con)
    finally:
        con.close()
    return scans, alerts.meal_records(scans), acks


def ack(key, action):
    con = store.connect()
    try:
        store.add_ack(con, key, action)
    finally:
        con.close()


def today_of(scans):
    """The day on screen: the newest real scan's date, else the profiles' service date."""
    real = [s["time"][:10] for s in scans if not s.get("synthetic")]
    return date.fromisoformat(max(real)) if real else date.fromisoformat(profiles["date"])


def who(rid):
    r = RESIDENTS.get(rid)
    return f"{r['name']} · Room {r['room']}" if r else (rid or "no resident")


def fmt_pct(p):
    return "—" if p is None else f"{p:.0f}%"


def hhmm(t):
    return t[11:16] if t and len(t) >= 16 else t


def label(text, where=st):
    where.markdown(f'<div class="lbl">{text}</div>', unsafe_allow_html=True)


def chip(meal, pct):
    tag = meal[0].upper()
    if pct is None:
        return f":gray-badge[{tag} —]"
    return f":{'red' if pct < alerts.LOW_PCT else 'violet'}-badge[{tag} {pct:.0f}%]"


def trend(mine, height=70, axes=False):
    """Bars of % eaten, oldest -> newest; red under the 50% line."""
    df = pd.DataFrame([{"meal": f"{m['date'][5:]} {m['meal']}", "pct": m["pct"],
                        "low": m["pct"] < alerts.LOW_PCT} for m in mine])
    x = alt.X("meal:N", sort=None, title=None, axis=alt.Axis(labelAngle=-30) if axes else None)
    y = alt.Y("pct:Q", scale=alt.Scale(domain=[0, 100]), title="% eaten" if axes else None,
              axis=None if not axes else alt.Axis())
    bars = alt.Chart(df).mark_bar().encode(x=x, y=y, tooltip=["meal", "pct"],
                                           color=alt.condition("datum.low", alt.value(LOW), alt.value(ACCENT)))
    rule = alt.Chart(pd.DataFrame({"y": [alerts.LOW_PCT]})).mark_rule(strokeDash=[4, 4], color=INK).encode(y="y:Q")
    return (bars + rule).properties(height=height)


FOOD_GROUP = {  # colors the per-food pieces of a meal bar
    **dict.fromkeys(["chicken", "pork chop", "white fish", "scrambled eggs", "yogurt", "edamame"], "protein"),
    **dict.fromkeys(["pasta", "rice", "mashed potatoes", "toast", "oatmeal"], "starch"),
    **dict.fromkeys(["carrots", "green beans", "mixed vegetables", "fruit cup"], "veg / fruit"),
}
GROUP_COLORS = {"protein": "#6329B7", "starch": "#F5A524", "veg / fruit": "#15803D", "other": "#94A3B8"}  # Roboflow UI purple, amber, green


def trend_by_food(scans, rid, last=10, height=260):
    """Meal bars split by food: each piece = that food's share of the meal's % eaten, so the pieces add
    up to the total (total = area gone / area served, summed over foods)."""
    rows = []
    for s in [s for s in insights.meal_afters(scans) if s["resident_id"] == rid][-last:]:
        served = sum(it.get("before_frac") or 0 for it in s.get("items") or [])
        for it in s.get("items") or []:
            if served and it.get("before_frac"):
                gone = it["before_frac"] - (it.get("after_frac") or 0)
                rows.append({"meal": f"{s['time'][5:10]} {s['meal']}", "food": it["name"],
                             "group": FOOD_GROUP.get(it["name"], "other"),
                             "share": round(100 * gone / served, 1), "ate": it.get("pct_eaten")})
    if not rows:
        return None
    groups = [g for g in GROUP_COLORS if any(r["group"] == g for r in rows)]
    bars = alt.Chart(pd.DataFrame(rows)).mark_bar(stroke="white", strokeWidth=1).encode(
        x=alt.X("meal:N", sort=None, title=None, axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("sum(share):Q", scale=alt.Scale(domain=[0, 100]), title="% eaten"),
        color=alt.Color("group:N", title=None,
                        scale=alt.Scale(domain=groups, range=[GROUP_COLORS[g] for g in groups]),
                        legend=alt.Legend(orient="top")),
        order=alt.Order("group:N"),
        tooltip=["meal", "food", alt.Tooltip("ate:Q", title="% of this food eaten"),
                 alt.Tooltip("share:Q", title="points of the meal %")])
    rule = alt.Chart(pd.DataFrame({"y": [alerts.LOW_PCT]})).mark_rule(strokeDash=[4, 4], color=INK).encode(y="y:Q")
    return (bars + rule).properties(height=height)


def photo(b64, where=st):
    if b64:
        try:
            where.image(base64.b64decode(b64), width="stretch")
            return
        except Exception:
            pass
    where.caption("no photo")


def left_text(left):
    return ", ".join(f"{x['name']} {x['left']}/{x['served']}" for x in left)


def nutrition_bars(day, goals, where=st):
    """Protein + kcal eaten today vs the resident's plate goals."""
    for key, unit, name in (("protein_g", "g", "protein"), ("kcal", "kcal", "kcal")):
        goal = (goals or {}).get(key)
        if goal:
            where.progress(min(day[key] / goal, 1.0), text=f"{name} today {day[key]:.0f} / {goal} {unit}")


# ---------- resident detail (dialog) ----------

@st.dialog("Resident", width="large")
def resident_dialog(rid):
    scans, records, _ = load()
    r = RESIDENTS[rid]
    st.subheader(who(rid))
    st.caption(f"Diet: {r.get('diet', '—')}")
    mine = [m for m in records if m["resident_id"] == rid]
    done = [m for m in mine if m["pct"] is not None][-10:]
    chart = trend_by_food(scans, rid)
    if chart is not None:
        st.altair_chart(chart, width="stretch")
    elif done:
        st.altair_chart(trend(done, height=220, axes=True), width="stretch")
    label("Meals, newest first")
    by_meal = {}
    for s in scans:
        if s.get("resident_id") == rid and s.get("status") == "ok":
            by_meal.setdefault((s["time"][:10], s["meal"]), {}).setdefault(s["phase"], s)
    for m in reversed(mine):
        pair = by_meal.get((m["date"], m["meal"]), {})
        with st.container(border=True):
            st.markdown(f"**{m['date'][5:]} {m['meal']}** · ate **{fmt_pct(m['pct'])}**"
                        + (f" · {m['kcal']:.0f} kcal · {m['protein_g']:.0f} g protein" if m["kcal"] is not None else "")
                        + (f"  \n:orange-badge[REVIEW] :gray[{', '.join(pair['after'].get('review_reasons') or [])}]"
                           if (pair.get("after") or {}).get("needs_review") else ""))
            if pair.get("before") or pair.get("after"):
                a, b = st.columns(2)
                label("Before", a)
                photo((pair.get("before") or {}).get("annotated_jpg_b64"), a)
                label("After", b)
                photo((pair.get("after") or {}).get("annotated_jpg_b64"), b)
                for it in (pair.get("after") or {}).get("items", []):
                    p = it.get("pct_eaten") or 0
                    st.progress(min(max(p / 100, 0.0), 1.0), text=f"{it['name']} · {p:.0f}%")


@st.dialog("QR cards", width="large")
def cards_dialog():
    st.caption("Each QR holds only the resident id. Print, cut, put next to the plate.")
    cols = st.columns(4)
    for i, r in enumerate(profiles["residents"]):
        cols[i % 4].image(cards.card(r), width="stretch")
    sheet = cards.sheet(profiles["residents"])
    c1, c2 = st.columns(2)
    c1.download_button("Save all cards (PNG)", cards.to_bytes(sheet, "PNG"), "intake-qr-cards.png", "image/png")
    c2.download_button("Save all cards (PDF)", cards.to_bytes(sheet, "PDF"), "intake-qr-cards.pdf",
                       "application/pdf")


# ---------- the Today screen ----------

def station_status(scans):
    """Kitchen station health from its newest real scan."""
    real = [s["time"] for s in scans if not s.get("synthetic")]
    if not real:
        return "station: no scans yet"
    mins = (datetime.now() - datetime.fromisoformat(max(real))).total_seconds() / 60
    return f"station last scan {'just now' if mins < 1 else f'{mins:.0f} min ago'}"


def export_csv():
    scans, records, _ = load()
    rows = [{"date": m["date"], "meal": m["meal"], "resident_id": m["resident_id"],
             "resident": RESIDENTS.get(m["resident_id"], {}).get("name"),
             "room": RESIDENTS.get(m["resident_id"], {}).get("room"),
             "pct_eaten": m["pct"], "chart_bin": m["chart_bin"], "kcal": m["kcal"], "protein_g": m["protein_g"],
             "synthetic": m["synthetic"]} for m in records]
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def kpis(scans, records, review, at_risk, today):
    done = [m for m in records if m["date"] == today.isoformat() and m["pct"] is not None]
    track = [insights.protein_on_track(insights.day_nutrition(scans, MENU, r["id"], today.isoformat()))
             for r in profiles["residents"]]
    track = [t for t in track if t is not None]
    a, b, c, d = st.columns(4)
    a.metric("Meals recorded today", len(done))
    b.metric("Protein on track today", f"{sum(track)} / {len(track)}" if track else "—",
             help="Ate at least 75% of the protein served so far today")
    c.metric("Residents at risk", len(at_risk))
    d.metric("Scans to review", len(review))


def needs_attention(scans, review, at_risk, today):
    label("Needs attention")
    if not at_risk and not review:
        st.success("Nobody needs attention right now.", icon="✅")
        return
    for a in at_risk:
        r = a["resident"]
        with st.container(border=True):
            left, mid, right = st.columns([3, 2, 1.3], vertical_alignment="center")
            meals = ", ".join(f"{m['date'][5:]} {m['meal']} {fmt_pct(m['pct'])}" for m in a["meals"])
            day = insights.day_nutrition(scans, MENU, r["id"], today.isoformat())
            goal = (r.get("goals") or {}).get("protein_g")
            leaves = insights.left_items(scans, r["id"])
            why = f"  \n:orange-badge[LEAVES] {left_text(leaves)} → {ACTION}" if leaves else ""
            left.markdown(f":red-badge[LOW INTAKE] **{r['name']}** · Room {r['room']}  \n"
                          f"Under 50% for {alerts.RUN} meals in a row → notify RD  \n"
                          f"Protein today **{day['protein_g']:.0f}" + (f" / {goal} g**" if goal else " g**")
                          + f"{why}  \n:gray[{meals}]")
            mid.altair_chart(trend(a["meals"]), width="stretch")
            if right.button("Notify RD", key=f"n-{r['id']}", type="primary", width="stretch"):
                ack(f"risk:{r['id']}:{a['meals'][-1]['time']}", "notified")
                st.rerun()
    for s in review:
        with st.container(border=True):
            left, right = st.columns([5, 1.3], vertical_alignment="center")
            why = ", ".join(s.get("review_reasons") or []) or "unsure"
            left.markdown(f":orange-badge[REVIEW] **{who(s.get('resident_id'))}** · {s.get('meal')} "
                          f"{s['phase']} {hhmm(s['time'])}  \n:gray[{why} · camera said {fmt_pct(s.get('total_pct_eaten'))}]")
            if right.button("Mark reviewed", key=f"r-{s['scan_id']}", width="stretch"):
                ack(f"review:{s['scan_id']}", "reviewed")
                st.rerun()


def resident_grid(scans, records, today):
    label("Residents")
    cols = st.columns(2)
    for i, r in enumerate(profiles["residents"]):
        mine = [m for m in records if m["resident_id"] == r["id"]]
        todays = {m["meal"]: m["pct"] for m in mine if m["date"] == today.isoformat()}
        done = [m for m in mine if m["pct"] is not None][-8:]
        with cols[i % 2].container(border=True):
            top, btn = st.columns([4, 1.4], vertical_alignment="center")
            risk = " :red-badge[AT RISK]" if alerts.low_streak([m["pct"] for m in mine]) else ""
            leaves = insights.left_items(scans, r["id"])
            if leaves:
                risk += f" :orange-badge[leaves {leaves[0]['name']}]"
            top.markdown(f"**{r['name']}** · Room {r['room']}{risk}  \n"
                         + " ".join(chip(meal, todays.get(meal)) for meal in MEALS))
            if btn.button("Open", key=f"o-{r['id']}", width="stretch"):
                st.session_state.open_rid = r["id"]
                st.rerun()
            if done:
                st.altair_chart(trend(done), width="stretch")
            nutrition_bars(insights.day_nutrition(scans, MENU, r["id"], today.isoformat()), r.get("goals"))


def kitchen_waste(scans, today):
    label("Kitchen · what comes back (7 days)")
    waste = insights.kitchen_waste(scans, MENU, today)
    if not waste:
        st.caption("No after-scans this week yet.")
        return
    bars = alt.Chart(pd.DataFrame(waste[:8])).mark_bar(color=ACCENT).encode(
        x=alt.X("pct_left:Q", scale=alt.Scale(domain=[0, 100]), title="% left on the plate"),
        y=alt.Y("name:N", sort="-x", title=None, axis=alt.Axis(labelOverlap=False)),
        tooltip=["name", "served", "pct_left", "usd"])
    st.altair_chart(bars.properties(height=240), width="stretch")
    week, beds, top = sum(w["usd"] for w in waste), len(profiles["residents"]), waste[0]
    # "\\$" keeps Streamlit from reading the dollar amounts as LaTeX
    st.markdown(f"**\\${week:,.0f}** of food left on plates this week · {beds} residents  \n"
                f":gray[≈ \\${week * 52 * 100 / beds:,.0f} a year at 100 beds · est. portion cost]  \n"
                f"Most money back: **{top['name']}** ({top['pct_left']:.0f}% left) → menu review")


def kitchen_feed(scans):
    """Live proof the station works: camera scans only (seeded history without a photo is skipped)."""
    label("From the kitchen · live")
    feed = [s for s in scans if not s.get("synthetic") or s.get("annotated_jpg_b64")]
    if not feed:
        st.info("No scans yet. Waiting for the kitchen station…")
    for s in feed[:FEED_LIMIT]:
        with st.container(border=True):
            pic, txt = st.columns([1, 2.2], vertical_alignment="center")
            if s.get("annotated_jpg_b64") and s.get("status") == "ok":
                photo(s["annotated_jpg_b64"], pic)
            name = RESIDENTS.get(s.get("resident_id"), {}).get("name", s.get("resident_id") or "no card")
            if s.get("status") != "ok":
                result = f":gray-badge[{s['status']}]"
            elif s["phase"] == "before":
                result = ":gray-badge[BEFORE saved]"
            else:
                result = f":violet-badge[ate {fmt_pct(s.get('total_pct_eaten'))}]"
            flag = " :orange-badge[review]" if s.get("needs_review") and s.get("status") == "ok" else ""
            txt.markdown(f"**{name}** · {s.get('meal') or ''}  \n{hhmm(s['time'])} {result}{flag}")


@st.fragment(run_every=REFRESH_S)
def today_screen():
    scans, records, acks = load()
    today = today_of(scans)
    at_risk = [a for a in alerts.resident_alerts(records, profiles["residents"])
               if f"risk:{a['resident']['id']}:{a['meals'][-1]['time']}" not in acks]
    review = [s for s in scans if s.get("status") == "ok" and s.get("needs_review")
              and f"review:{s['scan_id']}" not in acks][:5]
    st.caption(f"Today · {today.strftime('%a %b %d, %Y')} · {station_status(scans)} · updates every {REFRESH_S} s")
    kpis(scans, records, review, at_risk, today)
    main, side = st.columns([2.2, 1], gap="large")
    with main:
        needs_attention(scans, review, at_risk, today)
        resident_grid(scans, records, today)
    with side:
        kitchen_waste(scans, today)
        kitchen_feed(scans)


st.markdown(CSS, unsafe_allow_html=True)
st.logo(str(Path(__file__).resolve().parent / "assets" / "roboflow-logo.svg"), size="large")
head, qr, csv = st.columns([5, 1.2, 1.2], vertical_alignment="bottom")
head.title("Intake.ai – dietitian view")
if qr.button("Print QR cards", width="stretch"):
    cards_dialog()
csv.download_button("Export for charting", export_csv(), "intake-meals.csv", "text/csv", width="stretch",
                    help="Every recorded meal as CSV, for the EHR / MDS Section K paperwork")

today_screen()
rid = st.session_state.pop("open_rid", None)
if rid in RESIDENTS:
    resident_dialog(rid)

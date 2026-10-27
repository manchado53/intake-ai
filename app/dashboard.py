"""Intake.ai dietitian view: live scan feed, residents + low-intake alert, printable QR cards.

Run (repo root): .venv-app/Scripts/python -m streamlit run app/dashboard.py --server.port 8501
Reads the same SQLite DB the API server writes (env INTAKE_DB, default app/dashboard.db).
"""
import base64
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import altair as alt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import alerts, cards, store  # noqa: E402

REFRESH_S = 2
FEED_LIMIT = 30
ACCENT, LOW, INK = "#C29AF6", "#EF4444", "#121110"  # match .streamlit/config.toml
CSS = """<style>
h1, h2, h3 { letter-spacing: -.03em; }
[data-testid="stMetricLabel"] p, [data-testid="stCaptionContainer"], [data-testid="stSidebar"] label p {
  font-family: "Geist Mono", ui-monospace, monospace; text-transform: uppercase; letter-spacing: .08em; font-size: .75rem; }
[data-testid="stMetricValue"] { letter-spacing: -.03em; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { color: #C29AF6; }
</style>"""

st.set_page_config(page_title="Intake.ai – dietitian view", page_icon="🍽️", layout="wide")

profiles = store.load_profiles()
RESIDENTS = {r["id"]: r for r in profiles["residents"]}
TODAY = date.fromisoformat(profiles["date"])


def load():
    con = store.connect()
    try:
        scans = store.list_scans(con)
    finally:
        con.close()
    return scans, alerts.meal_records(scans)


def who(rid):
    r = RESIDENTS.get(rid)
    return f"{r['name']} · Room {r['room']}" if r else (rid or "no resident")


def fmt_pct(p):
    return "—" if p is None else f"{p:.0f}%"


def hhmm(t):
    return t[11:16] if t and len(t) >= 16 else t


# ---------- pieces ----------

def alert_banner(records):
    for a in alerts.resident_alerts(records, profiles["residents"]):
        r = a["resident"]
        meals = ", ".join(f"{m['date'][5:]} {m['meal']} {fmt_pct(m['pct'])}" for m in a["meals"])
        st.error(f"**{r['name']} (Room {r['room']}) ate under 50% for 3 meals in a row → notify RD**  \n{meals}",
                 icon="🚨")


def scan_card(s):
    if s.get("status") != "ok":
        st.caption(f"⚪ {hhmm(s['time'])} · **{s['status']}** · {s.get('resident_id') or 'no QR'} · "
                   f"{s.get('meal') or ''} · {s.get('station_id')}")
        return
    with st.container(border=True):
        photo = s.get("annotated_jpg_b64")
        left, right = st.columns([2, 3]) if photo else (None, st.container())
        if photo:
            try:
                left.image(base64.b64decode(photo), width="stretch")
            except Exception:
                left.caption("photo unreadable")
        with right:
            tags = [":gray-badge[BEFORE]" if s["phase"] == "before" else ":blue-badge[AFTER]"]
            if s.get("needs_review"):
                tags.append(f":orange-badge[needs review: {', '.join(s.get('review_reasons') or [])}]")
            if s.get("synthetic"):
                tags.append(":gray-badge[synthetic]")
            st.markdown(f"#### {who(s.get('resident_id'))}")
            st.markdown(f"{(s.get('meal') or '').capitalize()} · {hhmm(s['time'])} &nbsp; " + " ".join(tags))
            if s["phase"] == "before":
                st.markdown("Before photo saved: " + ", ".join(i["name"] for i in s["items"]))
                return
            a, b, c, d = st.columns(4)
            a.metric("Eaten", fmt_pct(s.get("total_pct_eaten")))
            b.metric("Chart", f"{s.get('chart_bin')}%")
            c.metric("kcal", f"{s.get('kcal') or 0:.0f}")
            d.metric("Protein", f"{s.get('protein_g') or 0:.0f} g")
            for it in s["items"]:
                p = it.get("pct_eaten") or 0
                st.progress(min(max(p / 100, 0.0), 1.0), text=f"{it['name']} · {p:.0f}%")


def residents_table(records):
    days = [TODAY - timedelta(days=d) for d in (2, 1, 0)]
    rows = []
    for r in profiles["residents"]:
        mine = [m for m in records if m["resident_id"] == r["id"]]
        today = {m["meal"]: m["pct"] for m in mine if m["date"] == TODAY.isoformat()}
        row = {"Resident": r["name"], "Room": r["room"]}
        for meal in ("breakfast", "lunch", "dinner"):
            row[f"Today {meal}"] = fmt_pct(today.get(meal)) if meal in today else ""
        last3 = [m for m in mine if m["date"] >= days[0].isoformat()]
        kcal = sum(m["kcal"] or 0 for m in last3)
        prot = sum(m["protein_g"] or 0 for m in last3)
        row["3-day kcal"] = round(kcal)
        row["3-day protein (g)"] = round(prot)
        row["Alert"] = "notify RD" if alerts.low_streak([m["pct"] for m in mine]) else ""
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(f"Today = {TODAY.isoformat()}. 3-day = {days[0].isoformat()} to today. "
               "Blank = no scan yet (missing is not 0%).")


def resident_detail(records):
    names = {f"{r['name']} · Room {r['room']}": r["id"] for r in profiles["residents"]}
    rid = names[st.selectbox("Resident", list(names), index=1 if len(names) > 1 else 0)]
    mine = [m for m in records if m["resident_id"] == rid and m["pct"] is not None][-8:]
    if not mine:
        st.info("No recorded meals yet.")
        return
    df = pd.DataFrame([{"meal": f"{m['date'][5:]} {m['meal']}", "pct": m["pct"],
                        "low": m["pct"] < alerts.LOW_PCT} for m in mine])
    bars = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("meal:N", sort=None, title=None),
        y=alt.Y("pct:Q", scale=alt.Scale(domain=[0, 100]), title="% eaten"),
        color=alt.condition("datum.low", alt.value(LOW), alt.value(ACCENT)),
        tooltip=["meal", "pct"],
    )
    rule = alt.Chart(pd.DataFrame({"y": [alerts.LOW_PCT]})).mark_rule(strokeDash=[4, 4], color=INK).encode(y="y:Q")
    st.altair_chart((bars + rule).properties(height=260), width="stretch")


# ---------- page ----------

st.markdown(CSS, unsafe_allow_html=True)
st.title("Intake.ai – dietitian view")


@st.fragment(run_every=REFRESH_S)
def live(page):
    scans, records = load()
    alert_banner(records)
    if page == "Live feed":
        if not scans:
            st.info("No scans yet. Waiting for the kitchen station…")
        for s in scans[:FEED_LIMIT]:
            scan_card(s)
    else:
        residents_table(records)
        st.subheader("Trend")
        resident_detail(records)


page = st.sidebar.radio("Page", ["Live feed", "Residents", "QR cards"])
st.sidebar.caption(f"Auto-refresh every {REFRESH_S} s · fake residents only")
st.sidebar.caption("Runs on Roboflow Inference")

if page != "QR cards":
    live(page)
else:
    st.subheader("QR cards")
    st.caption("Each QR holds only the resident id. Print, cut, put on the tray.")
    cols = st.columns(4)
    for i, r in enumerate(profiles["residents"]):
        cols[i % 4].image(cards.card(r), width="stretch")
    sheet = cards.sheet(profiles["residents"])
    c1, c2 = st.columns(2)
    c1.download_button("Save all cards (PNG)", cards.to_bytes(sheet, "PNG"), "intake-qr-cards.png", "image/png")
    c2.download_button("Save all cards (PDF)", cards.to_bytes(sheet, "PDF"), "intake-qr-cards.pdf",
                       "application/pdf")

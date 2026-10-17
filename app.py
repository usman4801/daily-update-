import html
import io
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Daily Manpower & Employee Transport Tracker",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

NAVY, BLUE, ORANGE = "#14284b", "#1b4b8f", "#f7941d"
STATUSES = ["On Route", "Delayed", "Arrived", "Not Started"]
PILL = {
    "On Route": ("#dcf5e4", "#1a8a45"),
    "Delayed": ("#fde2e2", "#c62828"),
    "Arrived": ("#dde9fb", "#1b4b8f"),
    "Not Started": ("#eceff4", "#5b6778"),
}
COORD = "+971 52 553 9471 / +971 55 530 9916"
COORD_BY_BUS = {
    "DXB-07": "+971 55 530 9916 / +971 52 553 9471",
    "DXB-08": "+971 55 530 9916 / +971 52 553 9471",
    "DXB-09": "+971 58 588 7560",
    "DXB-10": "+971 58 588 7560",
    "DXB-11": "+971 58 588 7560",
}
MAPS = {
    "DXB5": "Amazon DXB5 Dubai",
    "AUH1": "Amazon AUH1 Abu Dhabi",
    "DXB3": "Amazon DXB3 Dubai",
}
SEATS = 22  # every bus has 22 seats
MANIFEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.csv")
MAN_COLS = ["AMZ ID", "Employee Name", "Bus No", "Pickup Location", "Shift"]
STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bus_status.json")

# =============================================================================
# DATA  (edit here, or upload a pickup schedule file in the app)
# =============================================================================
D8 = "Day Shift (08:00 AM)"
N610 = "Night Shift (06:10 PM)"
A730 = "Day Shift (07:30 AM)"
N6 = "Night Shift (06:00 PM)"
MG, MS = "Mango Transport", "Mango / Shahara Sky"
DU, FL = "Dulsco Transport", "Fastlink Transport"

# Site, Shift, Bus No, Plate No, Route, Capacity, Booked, Vendor, Driver, Phone
FLEET_ROWS = [
    ("DXB5", D8, "DXB-01", "DXB-10101 (Temp)", "Sahara / Stadium / Al Nahda / DAFZA / Etisalat", 50, 46, MG, "Driver 1", "525539471"),
    ("DXB5", D8, "DXB-02", "DXB-10102 (Temp)", "Rashidiya Metro / International City / DIP Metro", 50, 44, MG, "Driver 2", "555309916"),
    ("DXB5", D8, "DXB-03", "DXB-10103 (Temp)", "Abuhail / Abubacker / Baniyas / Salah Din / Union / Al Rigga", 50, 48, MG, "Driver 3", "525539471"),
    ("DXB5", D8, "DXB-04", "DXB-10104 (Temp)", "Al Ghubaiba / Sharaf DG / Burjuman / ADCB / Satwa / WTC / Financial Ctr", 50, 45, MG, "Driver 4", "555309916"),
    ("DXB5", D8, "DXB-05", "DXB-10105 (Temp)", "Onpassive / MOE / Mashreq / Internet City / Gardens / Expo Rove", 50, 42, MG, "Driver 5", "525539471"),
    ("DXB5", D8, "DXB-06", "DXB-10106 (Temp)", "Dulsco Camps (Al Quoz, Liwan, Rahaba) & EFS Camps (Jabel Ali, Al Quoz)", 60, 55, MG, "Driver 6", "555309916"),
    ("DXB5", N610, "DXB-07", "DXB-20201 (Temp)", "Sahara Bus Stops / DAFZA Metro / Etisalat Metro", 50, 47, MS, "Driver 7", "555309916"),
    ("DXB5", N610, "DXB-08", "DXB-20202 (Temp)", "Abuhail / Abubacker / Baniyas / Salah Din / Union / Al Rigga", 50, 49, MS, "Driver 8", "525539471"),
    ("DXB5", N610, "DXB-09", "DXB-20203 (Temp)", "Rashidiya Metro / International City / DIP MS", 50, 43, MS, "Driver 9", "585887560"),
    ("DXB5", N610, "DXB-10", "DXB-20204 (Temp)", "Al Ghubaiba / Al Fahidi / Burjuman / ADCB / Financial Ctr / MOE / Satwa", 50, 46, MS, "Driver 10", "585887560"),
    ("DXB5", N610, "DXB-11", "DXB-20205 (Temp)", "Dulsco Village Alquoz / Livon / Rahaba & EFS Camps (Jabel Ali / Alquoz)", 60, 58, MS, "Driver 11", "585887560"),
    ("AUH1", A730, "AUH-01", "AUH-50101 (Temp)", "Dulsco ICAD-1 Bus Stop & Dulsco Camp", 65, 62, DU, "Driver 12", "500000001"),
    ("AUH1", A730, "AUH-02", "AUH-50102 (Temp)", "Dulsco Al Razeen Camp Abu Dhabi", 65, 60, DU, "Driver 13", "500000002"),
    ("AUH1", A730, "AUH-03", "AUH-50103 (Temp)", "Abu Dhabi Mall / Al Salama Hospital (Tourist Club Area)", 55, 52, FL, "Driver 14", "500000003"),
    ("AUH1", A730, "AUH-04", "AUH-50104 (Temp)", "Shinning Tower (Khalidiyah) / LifeLine Hospital / Central Bus Station", 60, 57, FL, "Driver 15", "500000004"),
    ("AUH1", A730, "AUH-05", "AUH-50105 (Temp)", "Shabiya 10 / 11 / 12 Bus Stop / Filli Cafe / Mussafah Workers Village", 60, 54, FL, "Driver 16", "500000005"),
    ("AUH1", N6, "AUH-06", "AUH-50201 (Temp)", "Dulsco ICAD-1 Bus Stop & Dulsco Camp (Night)", 65, 61, DU, "Driver 17", "500000006"),
    ("AUH1", N6, "AUH-07", "AUH-50202 (Temp)", "Dulsco Al Razeen Camp Abu Dhabi (Night)", 60, 54, DU, "Driver 18", "500000007"),
    ("AUH1", N6, "AUH-08", "AUH-50203 (Temp)", "Abu Dhabi Mall / Al Salama / Shinning Tower / LifeLine / Central Bus Stn", 65, 63, FL, "Driver 19", "500000008"),
    ("DXB3", D8, "DXB3-01", "DXB-30101 (Temp)", "Deira / BurJuman / Satwa / Sheikh Zayed Road Route", 50, 45, MG, "Driver 20", "525539471"),
    ("DXB3", D8, "DXB3-02", "DXB-30102 (Temp)", "Dulsco & EFS Accommodations Route (Al Quoz / Jabel Ali)", 60, 53, MG, "Driver 21", "555309916"),
    ("DXB3", N6, "DXB3-03", "DXB-30201 (Temp)", "Deira / BurJuman / Satwa / Camps Night Route", 60, 51, MG, "Driver 22", "585887560"),
]

# Site, Shift, Bus No, Pickup Location, Pickup Time
# Built in: DXB5 day buses DXB-01 and part of DXB-02, and all DXB5 night buses (DXB-07 to DXB-11).
# Upload the rest in the "Pickup Timings & Routes" tab (or add rows here).
PICKUP_ROWS = [
    ("DXB5", D8, "DXB-01", "Sahara _ ENOC Fuel Filling Station Backside Sahara Centre", "06:25 AM"),
    ("DXB5", D8, "DXB-01", "Sahara _ Foot Bridge Parking lot Near Save More Supermarket / Aster", "06:30 AM"),
    ("DXB5", D8, "DXB-01", "Stadium Metro _ Near Lulu round about & Adnoc Fuel Station", "06:35 AM"),
    ("DXB5", D8, "DXB-01", "Al Nahda Metro _ Service Road Bus Stop Sharjah Route", "06:40 AM"),
    ("DXB5", D8, "DXB-01", "DAFZA Metro _ Bus Stop Sharjah Route", "06:42 AM"),
    ("DXB5", D8, "DXB-01", "Etisalat Metro _ Bus Stop Sharjah Route", "06:45 AM"),
    ("DXB5", D8, "DXB-02", "Rashidiya Metro _ Near KFC", "06:35 AM"),
    ("DXB5", D8, "DXB-02", "International City (Near Post office Bus Stop)", "06:45 AM"),
]


def _stops(site, shift, bus, items):
    return [(site, shift, bus, loc, t) for loc, t in items]


# DXB5 06:10 PM night shift (Mango Transport / Shahara Sky), from the pickup-time sheet
PICKUP_ROWS += _stops("DXB5", N610, "DXB-07", [
    ("Sahara _ Before Foot Bridge Bus Stop", "04:20 PM"),
    ("Sahara _ Foot Bridge Bus Stop _ Near Sand area", "04:22 PM"),
    ("Sahara _ Bus Stop _ Near Sand area", "04:24 PM"),
    ("Sahara _ Bus Stop _ Naer ENOC Fuel Filling Station", "04:26 PM"),
    ("DAFZA Metro _ Bus Stop Sharjah Route", "04:40 PM"),
    ("Etisalat Metro _ Bus Stop Sharjah Route", "04:45 PM"),
])
PICKUP_ROWS += _stops("DXB5", N610, "DXB-08", [
    ("Abuhail Metro _ Parking Oposit Al Kabayel Centre or Near Bus Stand Abu Hail", "04:25 PM"),
    ("Abubacker Metro _ Bust Stoplocated Down of Metro towards to Deira Route", "04:30 PM"),
    ("Baniyas Metro _ Parking area Metro Exit 2 near RTA building parking", "04:30 PM"),
    ("Salah Din Metro _ Near Needs n Wants Supermarket opposite Side of Reef Mall", "04:30 PM"),
    ("Union Metro _ Alrigga Road First Parking area opposite side Algurrair Mcdonald", "04:35 PM"),
    ("Al Rigga Metro _ Near Barako Café / Citi Pharmacy", "04:37 PM"),
])
PICKUP_ROWS += _stops("DXB5", N610, "DXB-09", [
    ("Rashidiya Metro _ Near KFC", "04:35 PM"),
    ("International City (Near Post office Bus Stop)", "04:50 PM"),
    ("DIP MS", "05:15 PM"),
])
PICKUP_ROWS += _stops("DXB5", N610, "DXB-10", [
    ("Al Ghubaiba Palm City Hotel", "04:30 PM"),
    ("Al Fahidi Or Sharaf DG Metro Station", "04:33 PM"),
    ("Burjuman Metro _ Near Carrfour", "04:40 PM"),
    ("ADCB MS", "04:45 PM"),
    ("Financial Center", "04:10 PM"),
    ("Noor Bank/ Al Safa OR Onpassive MS", "04:15 PM"),
    ("Mall of Emirates", "04:25 PM"),
    ("Dubai Internet City Metro Station", "04:30 PM"),
    ("Discovery Gardens", "04:45 PM"),
    ("Satwa, Round about Near Kabab Rolls Restaurant", "04:55 PM"),
])
PICKUP_ROWS += _stops("DXB5", N610, "DXB-11", [
    ("Dulsco Village Camp Alquoz", "04:55 PM"),
    ("EFS Male Camp Jabel Ali/Parco", "05:05 PM"),
    ("New EFS Male Camp Jabel Ali/Parco", "05:05 PM"),
    ("EFS Female Camp Alquoz", "04:55 PM"),
    ("Dulsco Livon Female Camp", "05:05 PM"),
    ("Dulsco Al Rahaba Camp Men", "05:05 PM"),
])

FLEET = pd.DataFrame(
    FLEET_ROWS,
    columns=["Site", "Shift", "Bus No", "Plate No", "Route", "Capacity", "Booked", "Vendor", "Driver Name", "Phone"],
)
FLEET["Capacity"] = SEATS
FLEET["Phone"] = "971" + FLEET["Phone"]
FLEET["AMPM"] = FLEET["Shift"].map(lambda s: "PM" if "Night" in s else "AM")
FLEET["ShiftTime"] = FLEET["Shift"].str.extract(r"\((.*)\)")[0]
FLEET["Live"] = "https://wa.me/" + FLEET["Phone"]
PICKUPS = pd.DataFrame(PICKUP_ROWS, columns=["Site", "Shift", "Bus No", "Pickup Location", "Pickup Time"])

# =============================================================================
# STATE + HELPERS
# =============================================================================
S = st.session_state


def load_status():
    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_status():
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(S.status, f)
    except Exception:
        pass


def load_manifest():
    try:
        d = pd.read_csv(MANIFEST_FILE, dtype=str).fillna("")
        return d if len(d) else None
    except Exception:
        return None


def save_manifest():
    try:
        (S.manifest if S.manifest is not None else pd.DataFrame(columns=MAN_COLS)).to_csv(MANIFEST_FILE, index=False)
    except Exception:
        pass


S.setdefault("status", load_status())
S.setdefault("manifest", load_manifest())
S.setdefault("sched_up", None)


def esc(x):
    return html.escape(str(x))


def pill(s):
    bg, fg = PILL.get(s, PILL["Not Started"])
    return f'<span class="pill" style="background:{bg};color:{fg}">{esc(s)}</span>'


def full_schedule():
    p = PICKUPS.copy()
    up = S.sched_up
    if up is not None and len(up):
        p = pd.concat([p[~p["Bus No"].isin(up["Bus No"])], up], ignore_index=True)
    vend = FLEET.set_index("Bus No")["Vendor"]
    p["Vendor"] = p["Bus No"].map(vend)
    p["Coordinator"] = p["Bus No"].map(COORD_BY_BUS).fillna(COORD)
    return p


def read_upload(f):
    return pd.read_csv(f, dtype=str) if f.name.lower().endswith(".csv") else pd.read_excel(f, dtype=str)


def to_excel(sheets):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()


# =============================================================================
# STYLE
# =============================================================================
st.markdown(
    f"""
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] {{display:none !important;}}
.stApp {{background:#f3f5fa;}}
.block-container {{padding-top:4.5rem; padding-bottom:2rem; max-width:1500px;}}
.st-key-hdr {{background:linear-gradient(90deg,{NAVY},#1d3a66); border-radius:14px; padding:10px 22px; color:#fff;}}
.hdr-title {{font-size:21px; font-weight:700; line-height:1.2;}}
.hdr-sub {{font-size:12px; opacity:.85;}}
.logo {{font-size:30px; font-weight:800; letter-spacing:-1px; margin-right:14px;}}
.logo span {{color:{ORANGE};}}
[class*="st-key-card"] {{background:#fff; border-radius:14px; padding:16px 18px; box-shadow:0 1px 4px rgba(20,40,75,.08);}}
.kpi {{display:flex; gap:14px; align-items:center; background:#fff; border-radius:14px; padding:16px 18px; box-shadow:0 1px 4px rgba(20,40,75,.08); height:124px; box-sizing:border-box;}}
.kpi .ic {{width:54px; height:54px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:26px;}}
.kpi .lb {{font-weight:600; color:{NAVY};}} .kpi .v {{font-size:32px; font-weight:800; color:{NAVY}; line-height:1.1;}}
.kpi .sb {{font-size:12px; color:#6b7686;}}
.bar {{height:7px; background:#e8ebf2; border-radius:5px; margin-top:6px;}} .bar div {{height:7px; border-radius:5px; background:{ORANGE};}}
.card-t {{font-size:17px; font-weight:700; color:{NAVY}; margin:0 0 6px 0;}}
.pill {{padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600; white-space:nowrap;}}
.bgrid {{display:grid; grid-template-columns:repeat(auto-fill,minmax(168px,1fr)); gap:10px; max-height:400px; overflow-y:auto; padding-right:4px;}}
.bc {{border:1px solid #e8ebf2; border-radius:12px; padding:10px 12px; background:#fff;}}
.bh {{display:flex; justify-content:space-between; align-items:center; color:{NAVY}; font-size:13px;}}
.seats {{display:grid; grid-template-columns:repeat(11,1fr); gap:3px; margin:9px 0;}}
.seats i {{aspect-ratio:1; border-radius:3px; background:#dfe6f3;}} .seats i.f {{background:{ORANGE};}}
.bf {{display:flex; justify-content:space-between; font-size:12px; color:#5b6778;}}
.bf .ok {{color:#1a8a45; font-weight:700;}} .bf .ov {{color:#c62828; font-weight:700;}}
.lg {{font-size:12px; color:#5b6778; margin:2px 0 8px;}}
[class*="st-key-qa_"] {{border-radius:12px; padding:2px 8px; margin-bottom:8px;}}
.st-key-qa_export {{background:#eaf1fd; border-left:5px solid {BLUE};}}
.st-key-qa_wa {{background:#e6f7ec; border-left:5px solid #25a55a;}}
.st-key-qa_delay {{background:#fff3e0; border-left:5px solid {ORANGE};}}
.st-key-qa_print {{background:#f1ecfb; border-left:5px solid #7c4dcc;}}
[class*="st-key-qa_"] button {{border:0 !important; background:transparent !important; justify-content:flex-start; font-weight:700; color:{NAVY};}}
[class*="st-key-qa_"] details {{border:0 !important;}}
[class*="st-key-qa_"] summary {{font-weight:700; color:{NAVY};}}
.fs {{max-height:300px; overflow-y:auto;}}
.fs-row {{display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #f0f2f7; font-size:13px; color:{NAVY};}}
.tbl-wrap {{overflow-x:auto;}}
table.t {{border-collapse:collapse; width:100%; font-size:12.5px; color:{NAVY};}}
table.t th {{background:{NAVY}; color:#fff; padding:9px 8px; text-align:left; font-weight:600; white-space:nowrap;}}
table.t td {{padding:8px; border-bottom:1px solid #eef0f5; vertical-align:middle;}}
table.t tr:nth-child(even) td {{background:#fafbfd;}}
.ap {{display:inline-block; padding:1px 8px; border-radius:9px; font-size:11px; font-weight:700; background:#eceff4; color:#8a93a3;}}
.ap.on {{background:{BLUE}; color:#fff;}}
.rt {{max-width:230px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}}
a.wa {{color:#1b8a4a; font-weight:600; text-decoration:none;}}
.stTabs [data-baseweb="tab"] {{font-weight:600;}}
</style>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# HEADER
# =============================================================================
now = datetime.now(timezone(timedelta(hours=4)))  # Gulf Standard Time
with st.container(key="hdr"):
    h1, h2, h3 = st.columns([6, 2, 1.6], vertical_alignment="center")
    h1.markdown(
        '<div style="display:flex;align-items:center"><div class="logo">amazon<span>⌣</span></div>'
        '<div style="font-size:28px;margin-right:14px">🚌</div><div>'
        '<div class="hdr-title">Daily Manpower &amp; Employee Transport Tracker</div>'
        '<div class="hdr-sub">Safe Journeys &nbsp;•&nbsp; On Time &nbsp;•&nbsp; A Better Tomorrow</div></div></div>',
        unsafe_allow_html=True,
    )
    h2.markdown(
        f'<div style="text-align:right">📅 <b>{now.strftime("%a, %d %b %Y")}</b>'
        f'<div class="hdr-sub">(Today) &nbsp; {now.strftime("%I:%M %p")} GST</div></div>',
        unsafe_allow_html=True,
    )
    site = h3.selectbox("Site", ["All Sites", "DXB5", "AUH1", "DXB3"], label_visibility="collapsed")

fleet = FLEET.copy()
fleet["Status"] = fleet["Bus No"].map(lambda b: S.status.get(b, "On Route"))
if S.manifest is not None and len(S.manifest) and "Bus No" in S.manifest.columns:
    fleet["Booked"] = fleet["Bus No"].map(S.manifest["Bus No"].value_counts()).fillna(0).astype(int)
fl = fleet if site == "All Sites" else fleet[fleet["Site"] == site]
sched = full_schedule()
sched = sched if site == "All Sites" else sched[sched["Site"] == site]

tab1, tab2, tab3, tab4 = st.tabs(
    ["🚌 Live Bus Fleet", "🗺️ Pickup Timings & Routes", "👥 Pickup Headcounts", "📄 Employee Manifest (AMZ ID)"]
)

# =============================================================================
# TAB 1 - LIVE BUS FLEET
# =============================================================================
with tab1:
    cap, booked, nbus = int(fl["Capacity"].sum()), int(fl["Booked"].sum()), len(fl)
    delayed = fl[fl["Status"] == "Delayed"]
    pct = booked / cap if cap else 0
    ontime = (nbus - len(delayed)) / nbus if nbus else 0
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(
        f'<div class="kpi"><div class="ic" style="background:#dde9fb">🚌</div><div><div class="lb">Total Buses</div>'
        f'<div class="v">{nbus}</div><div class="sb">Active Fleet</div></div></div>', unsafe_allow_html=True)
    k2.markdown(
        f'<div class="kpi"><div class="ic" style="background:#fde9d2">👥</div><div style="flex:1">'
        f'<div class="lb">Total Assigned Passengers</div><div class="v">{booked}</div>'
        f'<div class="sb">of {cap} Seats ({pct:.0%})</div>'
        f'<div class="bar"><div style="width:{min(pct, 1)*100:.0f}%"></div></div></div></div>', unsafe_allow_html=True)
    k3.markdown(
        f'<div class="kpi"><div class="ic" style="background:#dde9fb">💺</div><div><div class="lb">Total Seat Capacity</div>'
        f'<div class="v">{cap}</div><div class="sb">Across {nbus} Buses</div></div></div>', unsafe_allow_html=True)
    k4.markdown(
        f'<div class="kpi"><div class="ic" style="background:#dcf5e4">⏱️</div><div><div class="lb">On-Time Pickups</div>'
        f'<div class="v">{ontime:.0%}</div><div class="sb">{len(delayed)} Delays Today</div></div></div>', unsafe_allow_html=True)

    left, right = st.columns([2.9, 1.1])

    with left:
        with st.container(key="card_chart"):
            st.markdown(f'<div class="card-t">💺 Seat Map · {SEATS} seats per bus</div>', unsafe_allow_html=True)
            d1, d2 = st.columns([1, 3], vertical_alignment="center")
            filled = min(booked, cap)
            fig = go.Figure(go.Pie(values=[filled, max(cap - filled, 0)], hole=0.72, sort=False, textinfo="none",
                                   marker=dict(colors=[ORANGE, "#dfe6f3"]), hoverinfo="skip"))
            fig.update_layout(height=230, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, paper_bgcolor="white",
                              annotations=[dict(text=f"<b>{pct:.0%}</b><br>seats filled", showarrow=False, font=dict(size=17, color=NAVY))])
            d1.plotly_chart(fig, use_container_width=True)
            cards = []
            for _, b in fl.iterrows():
                a_, over = int(b["Booked"]), int(b["Booked"]) - SEATS
                dots = "".join(f'<i class="{"f" if i < min(a_, SEATS) else ""}"></i>' for i in range(SEATS))
                tag = f'<span class="ov">+{over} over</span>' if over > 0 else f'<span class="ok">{SEATS - a_} free</span>'
                cards.append(
                    f'<div class="bc"><div class="bh"><b>🚌 {esc(b["Bus No"])}</b>{pill(b["Status"])}</div>'
                    f'<div class="seats">{dots}</div><div class="bf"><span>{a_} / {SEATS} seats</span>{tag}</div></div>')
            d2.markdown('<div class="lg">🟧 Assigned &nbsp; ⬜ Free seat</div><div class="bgrid">' + "".join(cards) + "</div>",
                        unsafe_allow_html=True)

        with st.container(key="card_sched"):
            s1, s2 = st.columns([4, 1], vertical_alignment="center")
            s1.markdown('<div class="card-t">📅 Pickup Schedule &amp; Live Locations</div>', unsafe_allow_html=True)
            ampm = s2.radio("Shift", ["AM", "PM"], horizontal=True, label_visibility="collapsed")
            rows, n = [], 0
            for _, b in fl[fl["AMPM"] == ampm].iterrows():
                sub = sched[sched["Bus No"] == b["Bus No"]]
                stops = list(zip(sub["Pickup Location"], sub["Pickup Time"])) or [("Timings not loaded", "—")]
                for loc, t in stops:
                    n += 1
                    am_t, pm_t = (t, "—") if ampm == "AM" else ("—", t)
                    rows.append(
                        f'<tr><td>{n}</td><td><b>{esc(loc)}</b></td>'
                        f'<td><div class="rt" title="{esc(b["Route"])}">{esc(b["Route"])}</div></td>'
                        f'<td><span class="ap {"on" if ampm == "AM" else ""}">AM</span> '
                        f'<span class="ap {"on" if ampm == "PM" else ""}">PM</span></td>'
                        f'<td>{am_t}</td><td>{pm_t}</td><td>{esc(b["Vendor"])}</td><td><b>{esc(b["Bus No"])}</b></td>'
                        f'<td>{b["Booked"]}</td><td>{b["Capacity"]}</td>'
                        f'<td><a class="wa" href="{esc(b["Live"])}" target="_blank">💬 View Live Location</a></td>'
                        f'<td>{pill(b["Status"])}</td></tr>'
                    )
            head = ("<tr><th>#</th><th>Pickup Location</th><th>Route / Area</th><th>Shift</th><th>AM</th><th>PM</th>"
                    "<th>Vendor</th><th>Bus No.</th><th>Assigned</th><th>Seat Capacity</th><th>Live Location</th><th>Status</th></tr>")
            st.markdown(f'<div class="tbl-wrap"><table class="t">{head}{"".join(rows)}</table></div>', unsafe_allow_html=True)

    with right:
        with st.container(key="card_fs"):
            st.markdown('<div class="card-t">Live Fleet Status</div>', unsafe_allow_html=True)
            items = "".join(
                f'<div class="fs-row"><span>🚌 <b>{esc(b["Bus No"])}</b></span>{pill(b["Status"])}'
                f'<span style="color:#6b7686">{esc(b["ShiftTime"])}</span></div>'
                for _, b in fl.iterrows()
            )
            st.markdown(f'<div class="fs">{items}</div>', unsafe_allow_html=True)
            with st.expander("Update bus status"):
                bus = st.selectbox("Bus", fl["Bus No"].tolist())
                new = st.selectbox("Status", STATUSES)
                if st.button("Save status", use_container_width=True):
                    S.status[bus] = new
                    save_status()
                    st.rerun()

        with st.container(key="card_map"):
            msite = "DXB5" if site == "All Sites" else site
            st.markdown(f'<div class="card-t">📍 Live Map · {msite}</div>', unsafe_allow_html=True)
            components.html(
                f'<iframe src="https://maps.google.com/maps?q={quote(MAPS[msite])}&z=13&output=embed" width="100%" '
                f'height="240" style="border:0;border-radius:12px" loading="lazy"></iframe>', height=250)
            st.link_button("🗺️ Open full map", f"https://www.google.com/maps/search/?api=1&query={quote(MAPS[msite])}",
                           use_container_width=True)

        with st.container(key="card_qa"):
            st.markdown('<div class="card-t">⚡ Quick Actions</div>', unsafe_allow_html=True)
            report = to_excel({"Fleet": fl.drop(columns=["AMPM", "ShiftTime", "Live"]), "Pickups": sched})
            with st.container(key="qa_export"):
                st.download_button("📥  Export Report (Excel)", report, f"transport_report_{now:%Y%m%d}.xlsx",
                                   use_container_width=True)
            with st.container(key="qa_wa"):
                with st.expander("💬  WhatsApp All Drivers"):
                    msg = st.text_input("Message", "Good morning, please share your live location.")
                    st.markdown("\n".join(
                        f"- [{r['Bus No']} · {r['Driver Name']}](https://wa.me/{r['Phone']}?text={quote(msg)})"
                        for _, r in fl.iterrows()))
            with st.container(key="qa_delay"):
                with st.expander(f"🚨  Delayed Buses ({len(delayed)})"):
                    if len(delayed):
                        st.dataframe(delayed[["Bus No", "Route", "Vendor", "Driver Name", "Phone"]], hide_index=True)
                    else:
                        st.success("✅ No delayed buses.")
            with st.container(key="qa_print"):
                man = S.manifest if S.manifest is not None else pd.DataFrame(columns=["AMZ ID", "Employee Name", "Bus No", "Pickup Location"])
                st.download_button("🖨️  Print Manifest (CSV)", man.to_csv(index=False), "manifest.csv", use_container_width=True)

# =============================================================================
# TAB 2 - PICKUP TIMINGS & ROUTES
# =============================================================================
with tab2:
    q1, q2 = st.columns([1, 2])
    which = q1.radio("Shift", ["All", "AM", "PM"], horizontal=True)
    text = q2.text_input("Search bus, location or vendor")
    view = sched.merge(fleet[["Bus No", "AMPM", "Route", "Status"]], on="Bus No", how="left")
    if which != "All":
        view = view[view["AMPM"] == which]
    if text:
        mask = view.astype(str).apply(lambda c: c.str.contains(text, case=False)).any(axis=1)
        view = view[mask]
    st.dataframe(view[["Site", "Shift", "Bus No", "Pickup Location", "Pickup Time", "Route", "Vendor", "Coordinator", "Status"]],
                 hide_index=True, use_container_width=True)
    loaded = set(sched["Bus No"])
    missing = [b for b in fl["Bus No"] if b not in loaded]
    if missing:
        st.warning(f"No pickup timings loaded for {len(missing)} bus(es): {', '.join(missing)}. Upload the schedule below.")
    with st.expander("Upload full pickup schedule (Excel / CSV)"):
        st.caption("Columns: Bus No, Pickup Location, Pickup Time. Site and Shift are optional.")
        tpl = pd.DataFrame(PICKUP_ROWS[:2], columns=PICKUPS.columns)
        st.download_button("Download template", tpl.to_csv(index=False), "pickup_schedule_template.csv")
        up = st.file_uploader("Pickup schedule", type=["xlsx", "xls", "csv"], key="sched_file")
        if up is not None:
            try:
                d = read_upload(up)
                d.columns = [c.strip() for c in d.columns]
                need = {"Bus No", "Pickup Location", "Pickup Time"}
                if not need.issubset(d.columns):
                    st.error(f"Missing column(s): {', '.join(sorted(need - set(d.columns)))}")
                else:
                    lk = FLEET.set_index("Bus No")
                    if "Site" not in d:
                        d["Site"] = d["Bus No"].map(lk["Site"])
                    if "Shift" not in d:
                        d["Shift"] = d["Bus No"].map(lk["Shift"])
                    S.sched_up = d[["Site", "Shift", "Bus No", "Pickup Location", "Pickup Time"]].dropna(subset=["Bus No"])
                    if S.get("sched_sig") != (up.name, up.size):
                        S.sched_sig = (up.name, up.size)
                        st.rerun()
                    st.success(f"Loaded {len(S.sched_up)} pickup rows.")
            except Exception as e:
                st.error(f"Could not read the file: {e}")

# =============================================================================
# TAB 3 - PICKUP HEADCOUNTS  (click a bus to see / edit who is travelling)
# =============================================================================
def stops_for(bus_no):
    route = FLEET.loc[FLEET["Bus No"] == bus_no, "Route"].iloc[0]
    known = full_schedule().query("`Bus No` == @bus_no")["Pickup Location"].tolist()
    return list(dict.fromkeys(known + route.split(" / ")))


with tab3:
    hc = fl[["Site", "Shift", "Bus No", "Route", "Capacity", "Booked"]].copy().reset_index(drop=True)
    hc["Free Seats"] = hc["Capacity"] - hc["Booked"]
    hc["Occupancy"] = (hc["Booked"] / hc["Capacity"] * 100).round(0)
    st.caption("👆 Click a bus row to see who is travelling. You can add, remove or move employees below it.")
    bus = None
    cfg = {"Occupancy": st.column_config.ProgressColumn("Occupancy %", min_value=0, max_value=100, format="%d%%")}
    try:
        ev = st.dataframe(hc, hide_index=True, use_container_width=True, on_select="rerun",
                          selection_mode="single-row", key="hc_tbl", column_config=cfg)
        if ev.selection.rows:
            bus = hc.iloc[ev.selection.rows[0]]["Bus No"]
    except TypeError:  # older Streamlit without row selection
        st.dataframe(hc, hide_index=True, use_container_width=True, column_config=cfg)
        bus = st.selectbox("Bus", hc["Bus No"].tolist(), key="pax_bus")

    if bus:
        b = FLEET[FLEET["Bus No"] == bus].iloc[0]
        man = S.manifest if S.manifest is not None else pd.DataFrame(columns=MAN_COLS)
        mine = man[man["Bus No"] == bus]
        with st.container(key="card_pax"):
            st.markdown(f'<div class="card-t">👥 Passengers on {esc(bus)} · {esc(b["Shift"])}</div>', unsafe_allow_html=True)
            stops = stops_for(bus)
            counts = mine["Pickup Location"].value_counts()
            if len(counts):
                st.markdown(" &nbsp;".join(f'<span class="pill" style="background:#eaf1fd;color:{BLUE}">📍 {esc(k)} · {v}</span>'
                                           for k, v in counts.items()), unsafe_allow_html=True)
            loc_f = st.selectbox("📍 Filter by pickup location", ["All locations"] + stops)
            view = mine if loc_f == "All locations" else mine[mine["Pickup Location"] == loc_f]
            st.caption(f"{len(view)} employee(s) shown · {len(mine)} on this bus · {SEATS} seats")

            W = [1.5, 2.2, 1.9, 3.2, 0.7]
            hd = st.columns(W)
            for col, t in zip(hd, ["🪪 Login", "👤 Name", "🕒 Shift", "📍 Pickup location", ""]):
                col.markdown(f"**{t}**")
            for idx, r in view.iterrows():
                c = st.columns(W, vertical_alignment="center")
                c[0].write(r["AMZ ID"])
                c[1].write(r["Employee Name"] or "—")
                c[2].write(r["Shift"] or b["Shift"])
                c[3].write(r["Pickup Location"] or "—")
                if c[4].button("🗑️", key=f"del_{idx}", help=f"Remove {r['AMZ ID']} from {bus}"):
                    S.manifest = man.drop(idx).reset_index(drop=True)
                    save_manifest()
                    st.rerun()
            if not len(view):
                st.info("No employees here yet. Add one below or upload the manifest.")

            with st.form("add_emp", clear_on_submit=True):
                st.markdown("**➕ Add employee to this bus**")
                f = st.columns([1.5, 2.2, 1.9, 3.2, 0.9], vertical_alignment="bottom")
                n_id = f[0].text_input("Login / AMZ ID")
                n_name = f[1].text_input("Name")
                shifts = list(dict.fromkeys(FLEET["Shift"]))
                n_shift = f[2].selectbox("Shift", shifts, index=shifts.index(b["Shift"]))
                n_loc = f[3].selectbox("Pickup location", stops)
                go_add = f[4].form_submit_button("➕ Add")
            if go_add:
                n_id = n_id.strip()
                dup = man[man["AMZ ID"].str.lower() == n_id.lower()]
                if not n_id:
                    st.error("Enter the employee login / AMZ ID.")
                elif len(dup):
                    st.error(f"{n_id} is already on {dup.iloc[0]['Bus No']}. Use 'Move employee' below instead.")
                else:
                    row = pd.DataFrame([[n_id, n_name.strip(), bus, n_loc, n_shift]], columns=MAN_COLS)
                    S.manifest = pd.concat([man, row], ignore_index=True)
                    save_manifest()
                    st.rerun()

            if len(mine):
                with st.expander("🔁 Move an employee to another bus or location"):
                    m1, m2, m3, m4 = st.columns([2.4, 1.4, 2.6, 1], vertical_alignment="bottom")
                    emp = m1.selectbox("Employee", list(mine.index),
                                       format_func=lambda i: f"{mine.loc[i, 'AMZ ID']} · {mine.loc[i, 'Employee Name']}")
                    buses = FLEET["Bus No"].tolist()
                    nb = m2.selectbox("To bus", buses, index=buses.index(bus))
                    nl = m3.selectbox("New pickup location", stops_for(nb))
                    if m4.button("🔁 Move"):
                        man.loc[emp, ["Bus No", "Pickup Location", "Shift"]] = [
                            nb, nl, FLEET.loc[FLEET["Bus No"] == nb, "Shift"].iloc[0]]
                        S.manifest = man
                        save_manifest()
                        st.rerun()
            if len(mine) > SEATS:
                st.warning(f"⚠️ {bus} has {len(mine)} employees but only {SEATS} seats.")

# =============================================================================
# TAB 4 - EMPLOYEE MANIFEST
# =============================================================================
with tab4:
    st.caption("Upload the roster with columns: AMZ ID, Employee Name, Bus No, Pickup Location (optional: Shift).")
    tpl = pd.DataFrame(columns=["AMZ ID", "Employee Name", "Bus No", "Pickup Location", "Shift"])
    st.download_button("Download template", tpl.to_csv(index=False), "manifest_template.csv")
    mf = st.file_uploader("Manifest file", type=["xlsx", "xls", "csv"], key="man_file")
    if mf is not None:
        try:
            d = read_upload(mf)
            d.columns = [c.strip() for c in d.columns]
            if "AMZ ID" not in d.columns:
                st.error("The file needs an 'AMZ ID' column.")
            elif S.get("man_sig") != (mf.name, mf.size):
                S.man_sig = (mf.name, mf.size)
                for col in MAN_COLS:
                    if col not in d.columns:
                        d[col] = ""
                S.manifest = d.fillna("").reset_index(drop=True)
                save_manifest()
                st.rerun()
        except Exception as e:
            st.error(f"Could not read the file: {e}")
    m = S.manifest
    if m is not None:
        f1, f2 = st.columns([2, 1])
        look = f1.text_input("Search by AMZ ID or name")
        v = m
        if site != "All Sites" and "Bus No" in m.columns:
            v = m[m["Bus No"].isin(fl["Bus No"])]
        if look:
            v = v[v.astype(str).apply(lambda c: c.str.contains(look, case=False)).any(axis=1)]
        f2.metric("Employees", len(v))
        st.dataframe(v, hide_index=True, use_container_width=True)
    else:
        st.info("No manifest uploaded yet.")

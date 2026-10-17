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

NAVY, BLUE, ORANGE, GREEN = "#0f2147", "#1b5cc8", "#f7941d", "#1fa855"
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
NAV = ["🚌 Live Bus Fleet", "📍 Pickup Timings & Routes", "👥 Pickup Headcounts", "📄 Employee Manifest (AMZ ID)"]

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


def contains(df, text):
    return df.astype(str).apply(lambda c: c.str.contains(text, case=False, regex=False)).any(axis=1)


def short_route(route):
    first = route.replace(" & ", " / ").split(" / ")[0]
    return first[:26]


# =============================================================================
# STYLE
# =============================================================================
st.markdown(
    f"""
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] {{display:none !important;}}
header[data-testid="stHeader"] {{background:transparent;}}
.stApp {{background:#f2f5fb;}}
.block-container {{padding-top:3.4rem; padding-bottom:1.2rem; max-width:1600px;}}

/* ---------- top header ---------- */
.st-key-hdr {{background:{NAVY}; border-radius:12px; padding:8px 22px; color:#fff;}}
.hdr-title {{font-size:20px; font-weight:700; line-height:1.2;}}
.hdr-sub {{font-size:11.5px; opacity:.85;}}
.logo {{font-size:30px; font-weight:800; letter-spacing:-1.5px; line-height:.9; margin-right:16px; padding-right:18px; border-right:1px solid rgba(255,255,255,.25);}}
.logo small {{display:block; color:{ORANGE}; font-size:22px; margin-top:-8px; text-align:center;}}
.busbox {{font-size:30px; margin-right:16px;}}
.hbtn {{display:inline-flex; width:40px; height:40px; border-radius:50%; align-items:center; justify-content:center; font-size:20px; position:relative;}}
.hbtn.av {{background:#fff; color:{NAVY};}}
.hbtn b {{position:absolute; top:4px; right:5px; width:9px; height:9px; border-radius:50%; background:#ff5a3c;}}
.st-key-hdr [data-baseweb="select"] > div {{background:rgba(255,255,255,.08); border:0; color:#fff;}}
.st-key-hdr [data-baseweb="select"] * {{color:#fff !important; fill:#fff !important;}}

/* ---------- nav bar ---------- */
.st-key-navbar {{background:#fff; border-radius:12px; padding:0 10px; box-shadow:0 1px 4px rgba(15,33,71,.08);}}
.st-key-navbar [role="radiogroup"] {{width:100%; gap:0; flex-wrap:nowrap;}}
.st-key-navbar [role="radiogroup"] label {{flex:1; justify-content:center; margin:0; padding:15px 8px; border-bottom:3px solid transparent; cursor:pointer;}}
.st-key-navbar [role="radiogroup"] label > div:first-child {{display:none;}}
.st-key-navbar [role="radiogroup"] label p {{font-weight:600; font-size:14px; color:{NAVY};}}
.st-key-navbar [role="radiogroup"] label:has(input:checked) {{border-bottom-color:{ORANGE}; background:#fff5e9;}}
.st-key-navbar [role="radiogroup"] label:has(input:checked) p {{color:{ORANGE};}}

/* ---------- cards ---------- */
[class*="st-key-card"] {{background:#fff; border-radius:12px; padding:16px 18px; box-shadow:0 1px 4px rgba(15,33,71,.08);}}
.card-t {{font-size:16px; font-weight:700; color:{NAVY}; line-height:1.2;}}
.card-s {{font-size:11.5px; color:#6b7686; margin-bottom:8px;}}
.card-h {{display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8px;}}
.lnk {{font-size:12px; font-weight:600; color:{BLUE}; white-space:nowrap;}}
.dot {{display:inline-block; width:8px; height:8px; border-radius:50%; margin:0 4px 0 12px;}}
.lg {{font-size:11px; color:#5b6778; white-space:nowrap;}}

/* ---------- KPI ---------- */
.kpi {{display:flex; gap:16px; align-items:center; background:#fff; border-radius:12px; padding:16px 20px; box-shadow:0 1px 4px rgba(15,33,71,.08); height:118px; box-sizing:border-box;}}
.kpi.warm {{background:linear-gradient(135deg,#fff,#fff4e8);}}
.kpi .ic {{width:60px; height:60px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:28px; flex:none;}}
.kpi .lb {{font-weight:600; color:{NAVY}; font-size:14px;}}
.kpi .v {{font-size:34px; font-weight:800; color:{NAVY}; line-height:1.1;}}
.kpi .sb {{font-size:12px; color:#6b7686;}}
.kpi .ok {{font-size:12px; color:{GREEN}; font-weight:600;}}
.kpi .bad {{font-size:12px; color:#c62828; font-weight:600;}}
.kpi .wn {{font-size:12px; color:{ORANGE}; font-weight:600;}}
.bar {{height:7px; background:#e8ebf2; border-radius:5px; margin-top:6px;}} .bar div {{height:7px; border-radius:5px; background:{GREEN};}}

/* ---------- seat usage ---------- */
.ub {{display:grid; grid-template-columns:50px 1fr 46px 38px; gap:8px; align-items:center; font-size:11px; color:{NAVY}; padding:3px 0;}}
.ub .tr {{height:6px; background:#e8ebf2; border-radius:4px;}} .ub .tr div {{height:6px; border-radius:4px;}}
.ub span:nth-child(3), .ub span:nth-child(4) {{text-align:right; color:#4a5568;}}
.ubox {{max-height:300px; overflow-y:auto;}}
.stat {{display:flex; justify-content:space-between; align-items:center; font-size:13px; color:{NAVY}; padding:7px 0;}}
.stat b {{font-size:15px;}}
.sd {{display:inline-block; width:9px; height:9px; border-radius:50%; margin-right:8px;}}

/* ---------- fleet status ---------- */
.fs {{max-height:430px; overflow-y:auto;}}
.fs-row {{display:flex; align-items:center; gap:8px; padding:9px 0; border-bottom:1px solid #f0f2f7; font-size:12.5px; color:{NAVY};}}
.fs-row .bn {{font-weight:700; font-size:13.5px;}} .fs-row .rt2 {{font-size:11px; color:#6b7686;}}
.fs-row .tm {{margin-left:auto; color:#4a5568; font-size:12px; white-space:nowrap;}}
.pill {{padding:2px 10px; border-radius:10px; font-size:10.5px; font-weight:700; white-space:nowrap;}}

/* ---------- alerts ---------- */
.al {{display:flex; align-items:center; gap:10px; padding:8px 0; font-size:12.5px; color:{NAVY};}}
.al .ai {{width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:12px; color:#fff; flex:none;}}
.al .tm {{margin-left:auto; color:#6b7686; font-size:11.5px; white-space:nowrap;}}

/* ---------- table ---------- */
.tbl-wrap {{overflow-x:auto; border:1px solid #eef0f5; border-radius:10px; max-height:430px; overflow-y:auto;}}
table.t {{border-collapse:collapse; width:100%; font-size:12px; color:{NAVY};}}
table.t th {{background:#f7f9fd; color:{NAVY}; padding:8px; text-align:left; font-weight:700; white-space:nowrap; border-bottom:1px solid #e8ebf2; position:sticky; top:0;}}
table.t td {{padding:8px; border-bottom:1px solid #f0f2f7; vertical-align:middle;}}
.ap {{display:inline-block; padding:1px 8px; border-radius:9px; font-size:11px; font-weight:700; background:#eceff4; color:#8a93a3;}}
.ap.on {{background:{BLUE}; color:#fff;}}
.rt {{max-width:200px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}}
a.wa {{color:{BLUE}; font-weight:600; text-decoration:none; white-space:nowrap;}}
.chip {{border:1px solid #dfe4ee; border-radius:8px; padding:7px 12px; font-size:12px; color:{NAVY}; background:#fff; white-space:nowrap; text-align:center;}}
.st-key-ampm [role="radiogroup"] {{gap:0; flex-wrap:nowrap;}}
.st-key-ampm label {{margin:0; padding:5px 22px; border:1px solid #dfe4ee; justify-content:center;}}
.st-key-ampm label:first-child {{border-radius:8px 0 0 8px;}} .st-key-ampm label:last-child {{border-radius:0 8px 8px 0;}}
.st-key-ampm label > div:first-child {{display:none;}}
.st-key-ampm label:has(input:checked) {{background:{NAVY}; border-color:{NAVY};}}
.st-key-ampm label:has(input:checked) p {{color:#fff;}}
.foot {{display:flex; justify-content:space-between; font-size:11px; color:#6b7686; padding:10px 6px 0;}}
</style>
""",
    unsafe_allow_html=True,
)

# =============================================================================
# HEADER + NAV BAR
# =============================================================================
now = datetime.now(timezone(timedelta(hours=4)))  # Gulf Standard Time
with st.container(key="hdr"):
    h1, h2, h3, h4 = st.columns([6, 2.2, 1.5, 1.1], vertical_alignment="center")
    h1.markdown(
        '<div style="display:flex;align-items:center"><div class="logo">amazon<small>⌣</small></div>'
        '<div class="busbox">🚌</div><div>'
        '<div class="hdr-title">Daily Manpower &amp; Employee Transport Tracker</div>'
        '<div class="hdr-sub">Safe Journeys &nbsp;•&nbsp; On Time &nbsp;•&nbsp; A Better Tomorrow</div></div></div>',
        unsafe_allow_html=True,
    )
    h2.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;justify-content:flex-end">📅 <div><b>{now.strftime("%a, %d %b %Y")}</b>'
        f'<div class="hdr-sub">(Today) &nbsp; {now.strftime("%I:%M %p")} GST</div></div></div>',
        unsafe_allow_html=True,
    )
    site = h3.selectbox("Site", ["All Sites", "DXB5", "AUH1", "DXB3"], index=1, label_visibility="collapsed")
    h4.markdown('<div style="display:flex;gap:10px;justify-content:flex-end"><span class="hbtn">🔔<b></b></span>'
                '<span class="hbtn av">👤</span></div>', unsafe_allow_html=True)

st.write("")
with st.container(key="navbar"):
    n1, n2, n3 = st.columns([5, 1.8, 0.8], vertical_alignment="center")
    nav = n1.radio("Navigation", NAV, horizontal=True, label_visibility="collapsed", key="nav")
    gq = n2.text_input("Search", placeholder="Search bus, location, or employee…", label_visibility="collapsed").strip()
    with n3.popover("Filters", icon=":material/filter_alt:", use_container_width=True):
        f_shift = st.radio("Shift", ["All", "AM", "PM"], horizontal=True)
        f_stat = st.multiselect("Status", STATUSES, default=STATUSES)
st.write("")

# ---------- data used by every page ----------
fleet = FLEET.copy()
fleet["Status"] = fleet["Bus No"].map(lambda b: S.status.get(b, "On Route"))
if S.manifest is not None and len(S.manifest) and "Bus No" in S.manifest.columns:
    fleet["Booked"] = fleet["Bus No"].map(S.manifest["Bus No"].value_counts()).fillna(0).astype(int)
fl = fleet if site == "All Sites" else fleet[fleet["Site"] == site]
if f_shift != "All":
    fl = fl[fl["AMPM"] == f_shift]
fl = fl[fl["Status"].isin(f_stat)]
sched = full_schedule()
sched = sched if site == "All Sites" else sched[sched["Site"] == site]
sched_q = sched[contains(sched, gq)] if gq else sched

# =============================================================================
# PAGE 1 - LIVE BUS FLEET
# =============================================================================
if nav == NAV[0]:
    cap, booked, nbus = int(fl["Capacity"].sum()), int(fl["Booked"].sum()), len(fl)
    delayed = fl[fl["Status"] == "Delayed"]
    pct = booked / cap if cap else 0
    ontime = (nbus - len(delayed)) / nbus if nbus else 0
    avail = max(cap - booked, 0)

    run_txt = (f'<div class="ok">● All Running</div>' if not len(delayed)
               else f'<div class="bad">● {len(delayed)} delayed</div>')
    delay_txt = (f'<div class="wn">0 Delays Today</div>' if not len(delayed)
                 else f'<div class="bad">{len(delayed)} Delays Today</div>')
    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(
        f'<div class="kpi"><div class="ic" style="background:#e3edfc">🚌</div><div><div class="lb">Total Buses</div>'
        f'<div class="v">{nbus}</div>{run_txt}</div></div>', unsafe_allow_html=True)
    k2.markdown(
        f'<div class="kpi"><div class="ic" style="background:#dcf5e4">👥</div><div style="flex:1">'
        f'<div class="lb">Total Assigned Passengers</div><div class="v">{booked}</div>'
        f'<div class="sb">of {cap} Seats ({pct:.0%})</div>'
        f'<div class="bar"><div style="width:{min(pct, 1)*100:.0f}%"></div></div></div></div>', unsafe_allow_html=True)
    k3.markdown(
        f'<div class="kpi"><div class="ic" style="background:#e3edfc">💺</div><div><div class="lb">Total Seat Capacity</div>'
        f'<div class="v">{cap}</div><div class="sb">Across {nbus} Buses</div></div></div>', unsafe_allow_html=True)
    k4.markdown(
        f'<div class="kpi warm"><div class="ic" style="background:#fde9d2">⏱️</div><div><div class="lb">On-Time Pickups</div>'
        f'<div class="v">{ontime:.0%}</div>{delay_txt}</div></div>', unsafe_allow_html=True)

    st.write("")
    msite = "DXB5" if site == "All Sites" else site
    gmap = quote(MAPS[msite])

    # ---------------- row 2: map | seat utilization | fleet status ----------------
    c_map, c_util, c_fs = st.columns([1.5, 1.25, 1.0])

    with c_map:
        with st.container(key="card_map"):
            st.markdown(
                '<div class="card-h"><div><div class="card-t">📍 Live Bus Fleet</div>'
                '<div class="card-s">Real-time tracking of all buses</div></div>'
                '<div class="lg"><span class="dot" style="background:#1fa855"></span>On Route'
                '<span class="dot" style="background:#f7941d"></span>At Pickup'
                '<span class="dot" style="background:#e53935"></span>Delayed'
                '<span class="dot" style="background:#7a8699"></span>Offline</div></div>',
                unsafe_allow_html=True)
            components.html(
                f'<iframe src="https://maps.google.com/maps?q={gmap}&z=11&output=embed" width="100%" '
                f'height="300" style="border:0;border-radius:10px" loading="lazy"></iframe>', height=310)
            st.link_button("🗺️ View Full Map", f"https://www.google.com/maps/search/?api=1&query={gmap}")

    with c_util:
        with st.container(key="card_util"):
            st.markdown(
                f'<div class="card-h"><div class="card-t">📊 Bus Seat Utilization</div>'
                f'<div class="lnk">View Details →</div></div>', unsafe_allow_html=True)
            d1, d2 = st.columns([1, 1.15], vertical_alignment="center")
            filled = min(booked, cap)
            fig = go.Figure(go.Pie(values=[filled, max(cap - filled, 0)], hole=0.74, sort=False, textinfo="none",
                                   marker=dict(colors=[BLUE, "#e3e8f2"]), hoverinfo="skip"))
            fig.update_layout(height=170, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, paper_bgcolor="white",
                              annotations=[dict(text=f"<b>{pct:.0%}</b><br><span style='font-size:10px'>Overall<br>Utilization</span>",
                                                showarrow=False, font=dict(size=20, color=NAVY))])
            d1.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            d2.markdown(
                f'<div class="stat"><span><i class="sd" style="background:{BLUE}"></i>Assigned Passengers</span><b>{booked}</b></div>'
                f'<div class="stat"><span><i class="sd" style="background:#c9d1e0"></i>Available Seats</span><b>{avail}</b></div>'
                f'<div class="stat" style="border-top:1px solid #eef0f5"><span>Total Capacity</span><b>{cap}</b></div>',
                unsafe_allow_html=True)
            st.markdown('<div style="font-weight:700;font-size:12.5px;color:#0f2147;margin:4px 0">Seat Usage by Bus</div>',
                        unsafe_allow_html=True)
            rows_u = []
            for _, b in fl.iterrows():
                a_ = int(b["Booked"])
                r_ = a_ / SEATS
                col = "#e53935" if r_ > 1 else (ORANGE if r_ >= 0.9 else BLUE)
                rows_u.append(
                    f'<div class="ub"><span><b>{esc(b["Bus No"])}</b></span>'
                    f'<span class="tr"><div style="width:{min(r_, 1)*100:.0f}%;background:{col}"></div></span>'
                    f'<span>{a_}/{SEATS}</span><span><b>{r_:.0%}</b></span></div>')
            st.markdown(f'<div class="ubox">{"".join(rows_u)}</div>', unsafe_allow_html=True)

    with c_fs:
        with st.container(key="card_fs"):
            ok_all = "● All Buses Running" if not len(delayed) else f"● {len(delayed)} Delayed"
            ok_col = GREEN if not len(delayed) else "#c62828"
            st.markdown(
                f'<div class="card-h"><div class="card-t">🔔 Live Fleet Status</div>'
                f'<div class="lg" style="color:{ok_col};font-weight:600">{ok_all} &nbsp;<span class="lnk">View All →</span></div></div>',
                unsafe_allow_html=True)
            items = "".join(
                f'<div class="fs-row"><span style="font-size:20px">🚌</span>'
                f'<div><div class="bn">{esc(b["Bus No"])}</div>'
                f'<div class="rt2">({esc(short_route(b["Route"]))} → {esc(b["Site"])})</div></div>'
                f'{pill(b["Status"])}<span class="tm">{esc(b["ShiftTime"])}</span></div>'
                for _, b in fl.iterrows()
            )
            st.markdown(f'<div class="fs">{items}</div>', unsafe_allow_html=True)
            with st.expander("Update bus status"):
                if len(fl):
                    bus_u = st.selectbox("Bus", fl["Bus No"].tolist())
                    new = st.selectbox("Status", STATUSES)
                    if st.button("Save status", use_container_width=True):
                        S.status[bus_u] = new
                        save_status()
                        st.rerun()

    # ---------------- row 3: schedule | snapshot + alerts ----------------
    c_sch, c_right = st.columns([2.75, 1.0])

    with c_sch:
        with st.container(key="card_sched"):
            s1, s2, s3 = st.columns([3.2, 1.3, 1.1], vertical_alignment="center")
            s1.markdown('<div class="card-t">🚌 Pickup Schedule &amp; Live Locations</div>', unsafe_allow_html=True)
            s2.markdown(f'<div class="chip">📅 {now.strftime("%a, %d %b %Y")}</div>', unsafe_allow_html=True)
            ampm = s3.radio("Shift", ["AM", "PM"], horizontal=True, label_visibility="collapsed", key="ampm")
            rows, n = [], 0
            for _, b in fl[fl["AMPM"] == ampm].iterrows():
                sub = sched_q[sched_q["Bus No"] == b["Bus No"]]
                stops = list(zip(sub["Pickup Location"], sub["Pickup Time"]))
                if not stops and not gq:
                    stops = [("Timings not loaded", "—")]
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
                        f'<td><a class="wa" href="{esc(b["Live"])}" target="_blank">💬 View Location</a></td>'
                        f'<td>{pill(b["Status"])}</td></tr>'
                    )
            head = ('<tr><th rowspan="2">#</th><th rowspan="2">Pickup Location</th><th rowspan="2">Route / Area</th>'
                    '<th rowspan="2">Shift</th><th colspan="2" style="text-align:center">Departure Timings</th>'
                    '<th rowspan="2">Vendor</th><th rowspan="2">Bus No.</th><th rowspan="2">Assigned</th>'
                    '<th rowspan="2">Seat Cap.</th><th rowspan="2">Live Location</th><th rowspan="2">Status</th></tr>'
                    '<tr><th style="top:32px">AM</th><th style="top:32px">PM</th></tr>')
            st.markdown(f'<div class="tbl-wrap"><table class="t">{head}{"".join(rows)}</table></div>', unsafe_allow_html=True)

    with c_right:
        with st.container(key="card_snap"):
            st.markdown('<div class="card-h"><div class="card-t">🔔 Live Map Snapshot</div></div>', unsafe_allow_html=True)
            components.html(
                f'<iframe src="https://maps.google.com/maps?q={gmap}&z=12&output=embed" width="100%" '
                f'height="150" style="border:0;border-radius:10px" loading="lazy"></iframe>', height=158)
            st.link_button("Open Live Map →", f"https://www.google.com/maps/search/?api=1&query={gmap}",
                           use_container_width=True)

        st.write("")
        with st.container(key="card_alerts"):
            tm = now.strftime("%I:%M %p")
            over = fl[fl["Booked"] > SEATS]
            alerts = []
            if len(delayed):
                for _, b in delayed.iterrows():
                    alerts.append(("#e53935", "!", f'{b["Bus No"]} is delayed'))
            else:
                alerts += [(GREEN, "✓", "All buses are running as per schedule"), (BLUE, "i", "No delays reported")]
            if len(over):
                alerts.append((ORANGE, "!", f'{len(over)} bus(es) over seat capacity: {", ".join(over["Bus No"])}'))
            else:
                alerts.append((ORANGE, "!", "Headcount matches with capacity"))
            st.markdown('<div class="card-h"><div class="card-t">🔔 Alerts &amp; Notifications</div>'
                        '<div class="lnk">View All →</div></div>', unsafe_allow_html=True)
            st.markdown("".join(
                f'<div class="al"><span class="ai" style="background:{c}">{i}</span><span>{esc(t)}</span>'
                f'<span class="tm">{tm}</span></div>' for c, i, t in alerts), unsafe_allow_html=True)

    # ---------------- quick actions (kept from the original app) ----------------
    st.write("")
    with st.container(key="card_qa"):
        st.markdown('<div class="card-t">⚡ Quick Actions</div>', unsafe_allow_html=True)
        qa1, qa2, qa3, qa4 = st.columns(4)
        report = to_excel({"Fleet": fl.drop(columns=["AMPM", "ShiftTime", "Live"]), "Pickups": sched})
        qa1.download_button("📥  Export Report (Excel)", report, f"transport_report_{now:%Y%m%d}.xlsx",
                            use_container_width=True)
        with qa2.popover("💬  WhatsApp All Drivers", use_container_width=True):
            msg = st.text_input("Message", "Good morning, please share your live location.")
            st.markdown("\n".join(
                f"- [{r['Bus No']} · {r['Driver Name']}](https://wa.me/{r['Phone']}?text={quote(msg)})"
                for _, r in fl.iterrows()))
        with qa3.popover(f"🚨  Delayed Buses ({len(delayed)})", use_container_width=True):
            if len(delayed):
                st.dataframe(delayed[["Bus No", "Route", "Vendor", "Driver Name", "Phone"]], hide_index=True)
            else:
                st.success("✅ No delayed buses.")
        man_q = S.manifest if S.manifest is not None else pd.DataFrame(columns=["AMZ ID", "Employee Name", "Bus No", "Pickup Location"])
        qa4.download_button("🖨️  Print Manifest (CSV)", man_q.to_csv(index=False), "manifest.csv", use_container_width=True)

# =============================================================================
# PAGE 2 - PICKUP TIMINGS & ROUTES
# =============================================================================
elif nav == NAV[1]:
    which = st.radio("Shift", ["All", "AM", "PM"], horizontal=True)
    view = sched_q.merge(fleet[["Bus No", "AMPM", "Route", "Status"]], on="Bus No", how="left")
    if which != "All":
        view = view[view["AMPM"] == which]
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
# PAGE 3 - PICKUP HEADCOUNTS  (click a bus to see / edit who is travelling)
# =============================================================================
def stops_for(bus_no):
    route = FLEET.loc[FLEET["Bus No"] == bus_no, "Route"].iloc[0]
    known = full_schedule().query("`Bus No` == @bus_no")["Pickup Location"].tolist()
    return list(dict.fromkeys(known + route.split(" / ")))


if nav == NAV[2]:
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
# PAGE 4 - EMPLOYEE MANIFEST
# =============================================================================
elif nav == NAV[3]:
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
        look = f1.text_input("Search by AMZ ID or name", value=gq)
        v = m
        if site != "All Sites" and "Bus No" in m.columns:
            v = m[m["Bus No"].isin(fl["Bus No"])]
        if look:
            v = v[contains(v, look)]
        f2.metric("Employees", len(v))
        st.dataframe(v, hide_index=True, use_container_width=True)
    else:
        st.info("No manifest uploaded yet.")

st.markdown(
    '<div class="foot"><span>Amazon Employee Transport Management &nbsp;|&nbsp; DXB5, DXB3 &amp; AUH1 Sites</span>'
    '<span><span style="color:#f7941d">⌣</span> &nbsp;Safe Rides &nbsp;•&nbsp; Punctual Workforce &nbsp;•&nbsp; A Stronger Amazon</span></div>',
    unsafe_allow_html=True,
)

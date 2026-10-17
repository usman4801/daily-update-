import html
import io
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

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
MAPS = {
    "DXB5": "Amazon DXB5 Dubai",
    "AUH1": "Amazon AUH1 Abu Dhabi",
    "DXB3": "Amazon DXB3 Dubai",
}
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
# Your pasted file was cut off after DXB-02, so only these rows are built in.
# Upload the full schedule in the "Pickup Timings & Routes" tab (or add rows here).
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

FLEET = pd.DataFrame(
    FLEET_ROWS,
    columns=["Site", "Shift", "Bus No", "Plate No", "Route", "Capacity", "Booked", "Vendor", "Driver Name", "Phone"],
)
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


S.setdefault("status", load_status())
S.setdefault("manifest", None)
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
    p["Coordinator"] = COORD
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
.block-container {{padding-top:1rem; padding-bottom:2rem; max-width:1500px;}}
.st-key-hdr {{background:linear-gradient(90deg,{NAVY},#1d3a66); border-radius:14px; padding:10px 22px; color:#fff;}}
.hdr-title {{font-size:21px; font-weight:700; line-height:1.2;}}
.hdr-sub {{font-size:12px; opacity:.85;}}
.logo {{font-size:30px; font-weight:800; letter-spacing:-1px; margin-right:14px;}}
.logo span {{color:{ORANGE};}}
[class*="st-key-card"] {{background:#fff; border-radius:14px; padding:16px 18px; box-shadow:0 1px 4px rgba(20,40,75,.08);}}
.kpi {{display:flex; gap:14px; align-items:center; background:#fff; border-radius:14px; padding:16px 18px; box-shadow:0 1px 4px rgba(20,40,75,.08); min-height:112px;}}
.kpi .ic {{width:54px; height:54px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:26px;}}
.kpi .lb {{font-weight:600; color:{NAVY};}} .kpi .v {{font-size:32px; font-weight:800; color:{NAVY}; line-height:1.1;}}
.kpi .sb {{font-size:12px; color:#6b7686;}}
.bar {{height:7px; background:#e8ebf2; border-radius:5px; margin-top:6px;}} .bar div {{height:7px; border-radius:5px; background:{ORANGE};}}
.card-t {{font-size:17px; font-weight:700; color:{NAVY}; margin:0 0 6px 0;}}
.pill {{padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600; white-space:nowrap;}}
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
        f'<div class="kpi" style="display:block"><div style="display:flex;gap:14px;align-items:center">'
        f'<div class="ic" style="background:#fde9d2">👥</div><div><div class="lb">Total Assigned Passengers</div>'
        f'<div class="v">{booked}</div><div class="sb">of {cap} Seats ({pct:.0%})</div></div></div>'
        f'<div class="bar"><div style="width:{pct*100:.0f}%"></div></div></div>', unsafe_allow_html=True)
    k3.markdown(
        f'<div class="kpi"><div class="ic" style="background:#dde9fb">💺</div><div><div class="lb">Total Seat Capacity</div>'
        f'<div class="v">{cap}</div><div class="sb">Across {nbus} Buses</div></div></div>', unsafe_allow_html=True)
    k4.markdown(
        f'<div class="kpi"><div class="ic" style="background:#dcf5e4">⏱️</div><div><div class="lb">On-Time Pickups</div>'
        f'<div class="v">{ontime:.0%}</div><div class="sb">{len(delayed)} Delays Today</div></div></div>', unsafe_allow_html=True)

    left, right = st.columns([2.9, 1.1])

    with left:
        with st.container(key="card_chart"):
            c1, c2 = st.columns([3, 1.6], vertical_alignment="center")
            c1.markdown('<div class="card-t">📊 Bus Seat Capacity vs Assigned Passengers</div>', unsafe_allow_html=True)
            mode = c2.radio("View", ["By Bus", "By Location"], horizontal=True, label_visibility="collapsed")
            if mode == "By Bus":
                g = fl[["Bus No", "Capacity", "Booked"]].rename(columns={"Bus No": "k"})
            else:
                key = "Site" if site == "All Sites" else "Shift"
                g = fl.groupby(key, as_index=False)[["Capacity", "Booked"]].sum().rename(columns={key: "k"})
            fig = go.Figure()
            fig.add_bar(x=g["k"], y=g["Capacity"], name="Seat Capacity", marker_color=BLUE,
                        text=g["Capacity"], textposition="outside")
            fig.add_bar(x=g["k"], y=g["Booked"], name="Assigned Passengers", marker_color=ORANGE,
                        text=g["Booked"], textposition="outside")
            fig.update_layout(barmode="group", height=340, margin=dict(l=10, r=10, t=30, b=10),
                              legend=dict(orientation="h", y=1.12, x=1, xanchor="right"),
                              plot_bgcolor="white", paper_bgcolor="white", yaxis=dict(gridcolor="#e6e9f0"))
            st.plotly_chart(fig, use_container_width=True)

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
            st.markdown('<div class="card-t">📍 Live Map</div>', unsafe_allow_html=True)
            st.caption("Open the site in Google Maps. Live bus positions come from each driver's WhatsApp location.")
            for s_name, q in MAPS.items():
                if site in ("All Sites", s_name):
                    st.link_button(f"View {s_name} Map", f"https://www.google.com/maps/search/?api=1&query={quote(q)}",
                                   use_container_width=True)

        with st.container(key="card_qa"):
            st.markdown('<div class="card-t">Quick Actions</div>', unsafe_allow_html=True)
            report = to_excel({"Fleet": fl.drop(columns=["AMPM", "ShiftTime", "Live"]), "Pickups": sched})
            st.download_button("📄 Export Report (Excel)", report, f"transport_report_{now:%Y%m%d}.xlsx",
                               use_container_width=True)
            with st.expander("💬 Send WhatsApp to All Drivers"):
                msg = st.text_input("Message", "Good morning, please share your live location.")
                st.markdown("\n".join(
                    f"- [{r['Bus No']} · {r['Driver Name']}](https://wa.me/{r['Phone']}?text={quote(msg)})"
                    for _, r in fl.iterrows()))
            with st.expander(f"⚠️ View Delayed Buses ({len(delayed)})"):
                if len(delayed):
                    st.dataframe(delayed[["Bus No", "Route", "Vendor", "Driver Name", "Phone"]], hide_index=True)
                else:
                    st.success("No delayed buses.")
            man = S.manifest if S.manifest is not None else pd.DataFrame(columns=["AMZ ID", "Employee Name", "Bus No", "Pickup Location"])
            st.download_button("🖨️ Print Manifest (CSV)", man.to_csv(index=False), "manifest.csv", use_container_width=True)

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
                    st.success(f"Loaded {len(S.sched_up)} pickup rows. Switch tabs to refresh.")
            except Exception as e:
                st.error(f"Could not read the file: {e}")

# =============================================================================
# TAB 3 - PICKUP HEADCOUNTS
# =============================================================================
with tab3:
    hc = fl[["Site", "Shift", "Bus No", "Route", "Capacity", "Booked"]].copy()
    hc["Free Seats"] = hc["Capacity"] - hc["Booked"]
    hc["Occupancy"] = (hc["Booked"] / hc["Capacity"] * 100).round(0)
    st.dataframe(
        hc, hide_index=True, use_container_width=True,
        column_config={"Occupancy": st.column_config.ProgressColumn("Occupancy %", min_value=0, max_value=100, format="%d%%")},
    )
    m = S.manifest
    if m is not None and "Pickup Location" in m.columns:
        st.markdown("**Headcount per pickup location (from manifest)**")
        pc = m.groupby(["Bus No", "Pickup Location"]).size().reset_index(name="Employees")
        st.dataframe(pc, hide_index=True, use_container_width=True)
    else:
        st.info("Upload the employee manifest (with a Pickup Location column) to see headcount per pickup point.")

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
            else:
                S.manifest = d
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

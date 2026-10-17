"""
Daily Manpower Dashboard (DMD) & Transport Tracking – Single-File Streamlit App
Fully self-contained (dmd_engine integrated) with multi-site Transport & Live Bus Tracking.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# MUST BE LINE 1 OF STREAMLIT COMMANDS
st.set_page_config(page_title="Daily Manpower & Transport Dashboard", page_icon="📊", layout="wide")

# =============================================================================
# 1. ENGINE CONSTANTS & TRANSPORT SCHEDULES (DXB5, DXB3, AUH1)
# =============================================================================
SHIFTS = ["Day Shift", "Mid Shift", "Night Shift"]
SITES = {
    "DXB5": (["DXB5"], ["ICQA", "Inbound", "Outbound", "CRET"], "DXB5"),
    "DXB8": (["DXB8", "DDB1"], ["Warehouse Deals"], "DXB8 (SC)"),
    "DWC3": (["DWC3"], ["ICQA", "Inbound", "Outbound"], "DWC3"),
    "AUH1": (["AUH1"], ["CRET", "ICQA", "Inbound", "Outbound", "Sort Center", "Warehouse Deals"], "AUH1"),
    "DXB3": (["DXB3"], ["ICQA", "Inbound", "Outbound", "CRET"], "DXB3"),
}
SUPERVISOR_TITLE = {
    "DXB5": "FC Associate III",
    "DXB8": "Hub Supervisor",
    "DWC3": "FC Associate III",
    "AUH1": "FC Associate III",
    "DXB3": "FC Associate III",
}
ATT_ORDER = ["0", "OFF", "PL", "P", "SL", "AB"]

DEFAULT_PREV_HC = {"DXB5": 1503, "DXB8": 132, "DWC3": 43, "AUH1": 653, "DXB3": 450}
DEFAULT_REMARKS = {"DXB5": "2 NFTE Terminated", "DXB8": "", "DWC3": "", "AUH1": "", "DXB3": ""}
DEFAULT_TARGETS = pd.DataFrame(
    [
        ("DXB5", "All", "Day Shift", "All", 0.8734),
        ("DXB5", "All", "Mid Shift", "All", 0.0),
        ("DXB5", "All", "Night Shift", "All", 0.879),
        ("DXB5", "All", "All", "All", 0.8769),
        ("DXB5", "ICQA", "Day Shift", "All", 0.9079),
        ("DXB5", "ICQA", "Night Shift", "All", 0.6317),
        ("DXB5", "ICQA", "All", "All", 0.8141),
        ("DXB5", "Inbound", "Day Shift", "All", 0.8719),
        ("DXB5", "Inbound", "Night Shift", "All", 0.8558),
        ("DXB5", "Inbound", "All", "All", 0.8648),
        ("DXB5", "Outbound", "Day Shift", "All", 0.8699),
        ("DXB5", "Outbound", "Night Shift", "All", 0.902),
        ("DXB5", "Outbound", "All", "All", 0.889),
        ("DXB8", "All", "All", "Regular", 0.8778),
        ("DXB8", "All", "All", "Temporary", 0.8974),
        ("DWC3", "All", "Day Shift", "All", 0.9375),
        ("DWC3", "All", "Mid Shift", "All", 0.0),
        ("DWC3", "All", "Night Shift", "All", 0.9557),
        ("DWC3", "All", "All", "All", 0.9496),
        ("AUH1", "All", "Day Shift", "All", 0.9000),
        ("AUH1", "All", "Mid Shift", "All", 0.9000),
        ("AUH1", "All", "Night Shift", "All", 0.9000),
        ("AUH1", "All", "All", "All", 0.9000),
        ("DXB3", "All", "Day Shift", "All", 0.8800),
        ("DXB3", "All", "Mid Shift", "All", 0.8800),
        ("DXB3", "All", "Night Shift", "All", 0.8800),
        ("DXB3", "All", "All", "All", 0.8800),
    ],
    columns=["Site", "Department", "Shift", "Employee Type", "LM Target"],
)

# Official DXB5 Day & Night Shift Pickup Schedules + AUH1 & DXB3 Routes
BUS_SCHEDULES_DATA = [
    # DXB5 & DXB8 - DAY SHIFT (08:00 AM SOS) - Vendor: Mango Transport
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Pickup Location": "Sahara _ ENOC Fuel Filling Station Backside Sahara Centre", "Pickup Time": "06:25 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Pickup Location": "Sahara _ Foot Bridge Parking lot Near Save More Supermarket / Aster", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Pickup Location": "Stadium Metro _ Near Lulu round about & Adnoc Fuel Station", "Pickup Time": "06:35 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Pickup Location": "Al Nahda Metro _ Service Road Bus Stop Sharjah Route", "Pickup Time": "06:40 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Pickup Location": "DAFZA Metro _ Bus Stop Sharjah Route", "Pickup Time": "06:42 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Pickup Location": "Etisalat Metro _ Bus Stop Sharjah Route", "Pickup Time": "06:45 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-02", "Plate No": "DXB-10102 (Temp)", "Pickup Location": "Rashidiya Metro _ Near KFC", "Pickup Time": "06:35 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-02", "Plate No": "DXB-10102 (Temp)", "Pickup Location": "International City (Near Post office Bus Stop)", "Pickup Time": "06:45 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-02", "Plate No": "DXB-10102 (Temp)", "Pickup Location": "International City (Near Civil Defense Bus Stop)", "Pickup Time": "06:50 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-02", "Plate No": "DXB-10102 (Temp)", "Pickup Location": "DIP Metro _ Bus Stop Near NMC Hospital", "Pickup Time": "07:10 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Temp)", "Pickup Location": "Abuhail Metro _ Parking Oposit Al Kabayel Centre", "Pickup Time": "06:25 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Temp)", "Pickup Location": "Abubacker Metro _ Bus Stop towards Deira Route", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Temp)", "Pickup Location": "Baniyas Metro _ Parking area Metro Exit 2 near RTA building", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Temp)", "Pickup Location": "Salah Din Metro _ Near Needs n Wants Supermarket opposite Reef Mall", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Temp)", "Pickup Location": "Union Metro _ Alrigga Road First Parking area opposite Alghurair Mcdonald", "Pickup Time": "06:35 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Temp)", "Pickup Location": "Al Rigga Metro _ Near Barako Café / Citi Pharmacy", "Pickup Time": "06:38 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-04", "Plate No": "DXB-10104 (Temp)", "Pickup Location": "Al Ghubaiba _ Near City Palace Hotel / Sharaf DG Metro Exit 2", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-04", "Plate No": "DXB-10104 (Temp)", "Pickup Location": "Burjuman Metro _ Near Carrefour / ADCB Metro Service Road", "Pickup Time": "06:40 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-04", "Plate No": "DXB-10104 (Temp)", "Pickup Location": "Satwa _ Parking Near Chelsea Plaza / World Trade Centre / Financial Centre", "Pickup Time": "06:35 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-05", "Plate No": "DXB-10105 (Temp)", "Pickup Location": "Onpassive Metro / MOE Metro / Mashreq Metro / Internet City / Gardens Metro", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-06", "Plate No": "DXB-10106 (Temp)", "Pickup Location": "Dulsco Mens & Womens Camps (Al Quoz, Liwan, Al Rahaba) & EFS Camps (Jabel Ali, Al Quoz)", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-06", "Plate No": "DXB-10106 (Temp)", "Pickup Location": "Expo_Rove Hotel", "Pickup Time": "07:20 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},

    # DXB5 - NIGHT SHIFT (06:10 PM SOS) - Vendor: Mango Transport / Shahara Sky
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-07", "Plate No": "DXB-20201 (Temp)", "Pickup Location": "Sahara _ Before Foot Bridge / Near Sand area / Near ENOC Fuel Station", "Pickup Time": "04:20 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "0555309916, 0525539471"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-07", "Plate No": "DXB-20201 (Temp)", "Pickup Location": "DAFZA Metro (4:40 PM) / Etisalat Metro Sharjah Route (4:45 PM)", "Pickup Time": "04:40 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "0555309916, 0525539471"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-08", "Plate No": "DXB-20202 (Temp)", "Pickup Location": "Abuhail Metro (4:25 PM) / Abubacker Metro / Baniyas Metro / Salah Din Metro", "Pickup Time": "04:25 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "0555309916, 0525539471"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-08", "Plate No": "DXB-20202 (Temp)", "Pickup Location": "Union Metro (4:35 PM) / Al Rigga Metro Near Barako Café (4:37 PM)", "Pickup Time": "04:35 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "0555309916, 0525539471"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-09", "Plate No": "DXB-20203 (Temp)", "Pickup Location": "Rashidiya Metro (4:35 PM) / International City (4:50 PM) / DIP MS (5:15 PM)", "Pickup Time": "04:35 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "+971 58 588 7560"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-10", "Plate No": "DXB-20204 (Temp)", "Pickup Location": "Al Ghubaiba / Al Fahidi / Burjuman Metro / ADCB MS / Satwa", "Pickup Time": "04:30 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "+971 58 588 7560"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-11", "Plate No": "DXB-20205 (Temp)", "Pickup Location": "Financial Center (4:10 PM) / Noor Bank / MOE / Internet City / Discovery Gardens", "Pickup Time": "04:10 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "+971 58 588 7560"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-12", "Plate No": "DXB-20206 (Temp)", "Pickup Location": "Dulsco Village Alquoz / Livon / Al Rahaba & EFS Camps (Jabel Ali / Alquoz)", "Pickup Time": "04:55 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "+971 58 588 7560"},

    # AUH1 - DAY & NIGHT SHIFT ROUTES
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-01", "Plate No": "AUH-50101 (Temp)", "Pickup Location": "Dulsco ICAD-1 Bus Stop / Dulsco Camp", "Pickup Time": "06:15 AM", "Vendor": "Dulsco Transport", "Coordinator": "+971 50 000 0001"},
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-02", "Plate No": "AUH-50102 (Temp)", "Pickup Location": "Dulsco Al Razeen Camp Abu Dhabi", "Pickup Time": "06:00 AM", "Vendor": "Dulsco Transport", "Coordinator": "+971 50 000 0002"},
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-03", "Plate No": "AUH-50103 (Temp)", "Pickup Location": "Abu Dhabi Mall / Al Salama Hospital (Tourist Club Area)", "Pickup Time": "06:10 AM", "Vendor": "Fastlink Transport", "Coordinator": "+971 50 000 0003"},
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-04", "Plate No": "AUH-50104 (Temp)", "Pickup Location": "Shinning Tower (Khalidiyah) / LifeLine Hospital / Central Bus Station", "Pickup Time": "06:10 AM", "Vendor": "Fastlink Transport", "Coordinator": "+971 50 000 0004"},
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-05", "Plate No": "AUH-50105 (Temp)", "Pickup Location": "Shabiya 10 / 11 / 12 Bus Stop & Mussafah Workers Village", "Pickup Time": "06:20 AM", "Vendor": "Fastlink Transport", "Coordinator": "+971 50 000 0005"},
    {"Site": "AUH1", "Shift": "Night Shift", "Bus No": "AUH-06", "Plate No": "AUH-50201 (Temp)", "Pickup Location": "Dulsco ICAD-1 Bus Stop / Dulsco Al Razeen Camp", "Pickup Time": "04:15 PM", "Vendor": "Dulsco Transport", "Coordinator": "+971 50 000 0001"},
    {"Site": "AUH1", "Shift": "Night Shift", "Bus No": "AUH-07", "Plate No": "AUH-50202 (Temp)", "Pickup Location": "Abu Dhabi Mall / Al Salama Hospital / Shinning Tower / LifeLine Hospital", "Pickup Time": "04:10 PM", "Vendor": "Fastlink Transport", "Coordinator": "+971 50 000 0003"},

    # DXB3 - DAY & NIGHT SHIFT ROUTES
    {"Site": "DXB3", "Shift": "Day Shift", "Bus No": "DXB3-01", "Plate No": "DXB-30101 (Temp)", "Pickup Location": "Deira / BurJuman / Satwa / Sheikh Zayed Road Route", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471"},
    {"Site": "DXB3", "Shift": "Night Shift", "Bus No": "DXB3-02", "Plate No": "DXB-30201 (Temp)", "Pickup Location": "Deira / BurJuman / Satwa / Camps Route", "Pickup Time": "04:30 PM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471"},
]


# =============================================================================
# 2. CALCULATION & ROSTER ENGINE (FORMERLY dmd_engine.py)
# =============================================================================
@dataclass
class Roster:
    df: pd.DataFrame
    date: pd.Timestamp | None
    day_name: str | None
    warnings: list[str]


def load_roster(file) -> Roster:
    """Read the 'Roster' sheet and normalize column names across DMD and HR/Transport files."""
    xl = pd.ExcelFile(file)
    sheet_to_read = "Roster" if "Roster" in xl.sheet_names else xl.sheet_names[0]
    raw = pd.read_excel(xl, sheet_name=sheet_to_read, header=None, dtype=object)

    # Support 'Sr No', 'SR', or 'Sr. No.' in column A
    col0_clean = raw.iloc[:, 0].astype(str).str.strip().str.lower()
    hdr_rows = raw.index[col0_clean.isin(["sr no", "sr", "sr. no.", "s.no"])]
    if len(hdr_rows) == 0:
        raise ValueError("Could not find the header row (a cell reading 'Sr No' or 'SR' in column A) on the Roster sheet.")
    h = hdr_rows[0]

    date, day_name = None, None
    top = raw.iloc[:h]
    for _, row in top.iterrows():
        if str(row.iloc[0]).strip().lower() == "date":
            date = pd.to_datetime(row.iloc[1], errors="coerce")
            day_name = None if pd.isna(row.iloc[2]) else str(row.iloc[2])
            break

    df = raw.iloc[h + 1:].copy()
    df.columns = [str(c).strip() for c in raw.iloc[h]]
    df = df.dropna(how="all")

    # Standardize differing column names across AUH1 / DXB5 / DMD workbooks
    col_map = {
        "SR": "Sr No",
        "Sr. No.": "Sr No",
        "Psoft ID": "Psoft No",
        "AmazonID": "AMZ ID",
        "Amazon ID": "AMZ ID",
        "AMZID": "AMZ ID",
        "Employment Type": "Employee Type",
        "Pickup Point": "Pickup point",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns and v not in df.columns})

    if "Sr No" in df.columns:
        df = df[df["Sr No"].notna()].reset_index(drop=True)

    warnings: list[str] = []

    # Ensure mandatory columns exist so downstream tabs never crash
    for req_col, default_val in [
        ("Building", "DXB5"),
        ("Shift", "Day Shift"),
        ("Department", "Unknown"),
        ("Type", "Direct"),
        ("Employee Type", "Temporary"),
        ("Job Title", "Warehouse Associate"),
        ("Line Manager", "Unassigned"),
        ("3P", "Unknown"),
        ("OFF1", ""),
        ("OFF2", ""),
        ("Remarks", np.nan),
        ("DOJ", pd.NaT),
        ("Psoft No", np.nan),
        ("AMZ ID", ""),
        ("Employee Name", ""),
        ("Process Path", ""),
    ]:
        if req_col not in df.columns:
            df[req_col] = default_val
            warnings.append(f"Column '{req_col}' was missing in this file and defaulted to '{default_val}'.")

    for c in df.columns:
        if c in ("DOJ",):
            continue
        df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)

    for c in ("OFF1", "OFF2"):
        before = df[c].copy()
        df[c] = df[c].map(
            lambda v: v.capitalize() if isinstance(v, str) and v.upper() != "OT" else ("OT" if isinstance(v, str) else v)
        )
        n = int((before.fillna("") != df[c].fillna("")).sum())
        if n:
            warnings.append(f"{n} {c} value(s) had inconsistent capitalisation and were normalised.")

    df["Building"] = df["Building"].astype(str).str.upper()

    # Handle Attendance column (if missing in HR/Transport roster, default Direct staff to 'P')
    if "Attendance" not in df.columns:
        df["Attendance"] = "P"
        warnings.append(
            "Note: 'Attendance' column was not found in this workbook (e.g. HR/Transport Roster). Defaulted Attendance to 'P' so all tabs work."
        )

    att = df["Attendance"].map(
        lambda v: ""
        if pd.isna(v)
        else str(int(v))
        if isinstance(v, (int, float)) and float(v) == 0
        else str(v).strip().upper()
    )
    df["Att"] = att.replace({"ABWI": "AB"})
    df["DOJ"] = pd.to_datetime(df["DOJ"], errors="coerce")
    df["Psoft No"] = pd.to_numeric(df["Psoft No"], errors="coerce")
    df["Sr No"] = pd.to_numeric(df["Sr No"], errors="coerce")
    df["OT"] = (df["OFF1"] == "OT") | (df["OFF2"] == "OT")
    df["Is Direct"] = df["Type"].astype(str).str.lower().eq("direct")
    return Roster(df=df, date=date, day_name=day_name, warnings=warnings)


def _count(df: pd.DataFrame) -> dict:
    vc = df["Att"].value_counts()
    g = lambda k: int(vc.get(k, 0))  # noqa: E731
    total = len(df)
    unsched, off, pl, p, sl, ab = g("0"), g("OFF"), g("PL"), g("P"), g("SL"), g("AB")
    ot = int(df["OT"].sum())
    grid_total = unsched + off + pl + p + sl + ab
    scheduled = grid_total - off - unsched - ot
    upl = sl + ab
    present = scheduled - pl - upl
    return {
        "Total HC": total,
        "Unscheduled": off,
        "Schedule to Work": scheduled,
        "PL": pl,
        "OT": ot,
        "UPL": upl,
        "Present": present,
        "SL": sl,
        "AB/ABWI": ab,
        "P (incl. OT)": p,
        "Zero": unsched,
        "Grid Total": grid_total,
    }


def _pct(a, b):
    return np.nan if (b is None or b == 0 or pd.isna(b)) else a / b


def lookup_target(targets: pd.DataFrame, site, dept="All", shift="All", etype="All"):
    t = targets[
        (targets["Site"] == site)
        & (targets["Department"] == dept)
        & (targets["Shift"] == shift)
        & (targets["Employee Type"] == etype)
    ]
    return float(t["LM Target"].iloc[0]) if len(t) else np.nan


def site_frame(roster_df: pd.DataFrame, site: str) -> pd.DataFrame:
    buildings = SITES[site][0]
    return roster_df[roster_df["Building"].isin(buildings)]


def shift_summary(roster_df: pd.DataFrame, site: str, targets: pd.DataFrame) -> pd.DataFrame:
    d = site_frame(roster_df, site)
    d = d[d["Is Direct"]]
    rows = []
    for s in SHIFTS:
        c = _count(d[d["Shift"] == s])
        c["Shift"] = s
        c["LM Target"] = lookup_target(targets, site, "All", s)
        rows.append(c)
    gt = _count(d)
    gt["Shift"] = "Grand Total"
    if site == "DXB8":
        reg = lookup_target(targets, site, "All", "All", "Regular")
        tmp = lookup_target(targets, site, "All", "All", "Temporary")
        n_reg = int((d["Employee Type"] == "Regular").sum())
        n_tmp = int((d["Employee Type"] == "Temporary").sum())
        gt["LM Target"] = (reg * n_reg + tmp * n_tmp) / max(n_reg + n_tmp, 1)
    else:
        gt["LM Target"] = lookup_target(targets, site, "All", "All")
    rows.append(gt)
    out = pd.DataFrame(rows)
    out["Present %"] = [_pct(a, b) for a, b in zip(out["Present"], out["Schedule to Work"])]
    out["Target Achievement"] = [
        np.nan if (pd.isna(t) or t == 0) else _pct(p, t) for p, t in zip(out["Present %"], out["LM Target"])
    ]
    return out[
        [
            "Shift",
            "Total HC",
            "Unscheduled",
            "Schedule to Work",
            "PL",
            "OT",
            "UPL",
            "Present",
            "Present %",
            "LM Target",
            "Target Achievement",
        ]
    ]


def dept_shift_detail(roster_df: pd.DataFrame, site: str, targets: pd.DataFrame) -> pd.DataFrame:
    d = site_frame(roster_df, site)
    d = d[d["Is Direct"]]
    depts = SITES[site][1]
    rows = []
    for dept in depts:
        dd = d[d["Department"] == dept]
        for s in SHIFTS + ["Total"]:
            sub = dd if s == "Total" else dd[dd["Shift"] == s]
            c = _count(sub)
            target = lookup_target(targets, site, dept, "All" if s == "Total" else s)
            sched = c["Schedule to Work"]
            actual = _pct(c["P (incl. OT)"] - c["OT"], sched)
            rows.append(
                {
                    "Department": dept,
                    "Shift": s,
                    "0": c["Zero"],
                    "OFF": c["Unscheduled"],
                    "PL": c["PL"],
                    "Present (incl. OT)": c["P (incl. OT)"],
                    "OT": c["OT"],
                    "SL": c["SL"],
                    "AB/ABWI": c["AB/ABWI"],
                    "Grand Total": c["Grid Total"],
                    "Scheduled": sched,
                    "Target": target,
                    "Actual % (w/o OT)": actual,
                    "Expected HC": (target * sched) if pd.notna(target) else np.nan,
                    "Actual HC": c["P (incl. OT)"] - c["OT"],
                }
            )
    out = pd.DataFrame(rows)
    out["Delta HC"] = out["Actual HC"] - out["Expected HC"]
    return out


def type_summary(roster_df: pd.DataFrame, site: str, targets: pd.DataFrame) -> pd.DataFrame:
    d = site_frame(roster_df, site)
    d = d[d["Is Direct"]]
    rows = []
    for et in ["Regular", "Temporary"]:
        c = _count(d[d["Employee Type"] == et])
        c["Employee Type"] = et
        c["LM Target"] = lookup_target(targets, site, "All", "All", et)
        rows.append(c)
    out = pd.DataFrame(rows)
    out["Present %"] = [_pct(a, b) for a, b in zip(out["Present"], out["Schedule to Work"])]
    out["Target Achievement"] = [
        np.nan if pd.isna(t) or t == 0 else _pct(p, t) for p, t in zip(out["Present %"], out["LM Target"])
    ]
    return out[
        [
            "Employee Type",
            "Total HC",
            "Unscheduled",
            "Schedule to Work",
            "PL",
            "OT",
            "UPL",
            "Present",
            "Present %",
            "LM Target",
            "Target Achievement",
        ]
    ]


def headcount_block(roster_df: pd.DataFrame, site: str, prev_hc: int, hc_target: int | None = None) -> dict:
    d = site_frame(roster_df, site)
    d = d[d["Is Direct"]]
    fte = int((d["Employee Type"] == "Regular").sum())
    nfte = int((d["Employee Type"] == "Temporary").sum())
    today = fte + nfte
    sup_title = SUPERVISOR_TITLE.get(site, "FC Associate III").lower()
    sup = int((d["Job Title"].astype(str).str.lower() == sup_title).sum())
    target = today if hc_target is None else hc_target
    return {
        "Previous Day HC": prev_hc,
        "L3 Ops Supervisors": sup,
        "FTE HC": fte,
        "NFTE HC": nfte,
        "Today's HC": today,
        "HC LM Target": target,
        "Achievement %": _pct(today, target),
        "Change vs Prev Day": today - prev_hc,
    }


def all_sites_overview(roster_df: pd.DataFrame, targets: pd.DataFrame, prev_hc: dict) -> pd.DataFrame:
    rows = []
    for site, (_, _, label) in SITES.items():
        s = shift_summary(roster_df, site, targets).iloc[-1]
        h = headcount_block(roster_df, site, prev_hc.get(site, 0))
        if h["Today's HC"] == 0 and site in ("AUH1", "DXB3"):
            continue
        rows.append(
            {
                "Site": label,
                "Today's HC": h["Today's HC"],
                "Prev Day HC": h["Previous Day HC"],
                "Change": h["Change vs Prev Day"],
                "Schedule to Work": s["Schedule to Work"],
                "Present": s["Present"],
                "Present %": s["Present %"],
                "LM Target": s["LM Target"],
                "Target Achievement": s["Target Achievement"],
            }
        )
    out = pd.DataFrame(rows)
    if len(out) == 0:
        return pd.DataFrame(
            columns=[
                "Site",
                "Today's HC",
                "Prev Day HC",
                "Change",
                "Schedule to Work",
                "Present",
                "Present %",
                "LM Target",
                "Target Achievement",
            ]
        )
    tot = {
        "Site": "All sites",
        "Today's HC": out["Today's HC"].sum(),
        "Prev Day HC": out["Prev Day HC"].sum(),
        "Change": out["Change"].sum(),
        "Schedule to Work": out["Schedule to Work"].sum(),
        "Present": out["Present"].sum(),
    }
    tot["Present %"] = _pct(tot["Present"], tot["Schedule to Work"])
    w = out["Schedule to Work"]
    tot["LM Target"] = float((out["LM Target"].fillna(0) * w).sum() / w.sum()) if w.sum() else np.nan
    tot["Target Achievement"] = _pct(tot["Present %"], tot["LM Target"])
    return pd.concat([out, pd.DataFrame([tot])], ignore_index=True)


def quality_checks(roster: Roster) -> pd.DataFrame:
    df = roster.df
    checks = []

    def add(name, n, detail=""):
        checks.append({"Check": name, "Rows": int(n), "Status": "OK" if n == 0 else "Review", "Detail": detail})

    add(
        "Attendance not in 0 / OFF / PL / P / SL / AB / ABWI",
        (~df["Att"].isin(ATT_ORDER)).sum(),
        ", ".join(sorted(set(df.loc[~df["Att"].isin(ATT_ORDER), "Attendance"].astype(str)))[:8]),
    )
    add("Duplicate Psoft No", df["Psoft No"].dropna().duplicated(keep=False).sum())
    add("Duplicate AMZ ID", df["AMZ ID"].dropna().duplicated(keep=False).sum())
    add(
        "Duplicate Employee Name",
        df["Employee Name"].astype(str).str.lower().duplicated(keep=False).sum(),
        "may be legitimate (same name, different person)",
    )
    add("Missing Line Manager", df["Line Manager"].isna().sum())
    add(
        "Missing Department / Shift / Building",
        (df["Department"].isna() | df["Shift"].isna() | df["Building"].isna()).sum(),
    )
    add("OT marked but Attendance is not P", (df["OT"] & (df["Att"] != "P")).sum())
    add("Same weekday in OFF1 and OFF2", (df["OFF1"].eq(df["OFF2"]) & df["OFF1"].notna() & (df["OFF1"] != "")).sum())
    if "Pickup point" in df.columns:
        add("Missing Transport Pickup Point", df["Pickup point"].isna().sum(), "Employees without assigned bus stop")
    return pd.DataFrame(checks)


def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, frame in sheets.items():
            frame.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()


# =============================================================================
# 3. UI HELPERS
# =============================================================================
TODAY = "Today's HC"


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, width="stretch", **kwargs)
    except Exception:
        return fn(*args, use_container_width=True, **kwargs)


def show_df(df_in: pd.DataFrame, pct_cols=(), **kwargs):
    d = df_in.copy()
    cfg = dict(kwargs.pop("column_config", {}))
    for c in pct_cols:
        if c in d.columns:
            d[c] = d[c] * 100
            cfg[c] = st.column_config.NumberColumn(c, format="%.1f%%")
    for c in d.columns:
        if c not in cfg and pd.api.types.is_float_dtype(d[c]):
            cfg[c] = st.column_config.NumberColumn(c, format="%.1f")
    _call(st.dataframe, d, hide_index=True, column_config=cfg, **kwargs)


def show_chart(fig):
    _call(st.plotly_chart, fig)


def status(x) -> str:
    if x is None or pd.isna(x):
        return ""
    return "🟢" if x >= 1 else ("🟠" if x >= 0.95 else "🔴")


def pct(x, nd=1) -> str:
    return "–" if x is None or pd.isna(x) else f"{x * 100:.{nd}f}%"


def blank_zero_targets(df_in: pd.DataFrame, col="LM Target") -> pd.DataFrame:
    d = df_in.copy()
    if col in d.columns:
        d[col] = d[col].replace(0, np.nan)
    return d


def crosstab_att(d: pd.DataFrame, by: str) -> pd.DataFrame:
    if len(d) == 0 or by not in d.columns:
        return pd.DataFrame(columns

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Daily Manpower & Transport Dashboard", page_icon="📊", layout="wide")

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

BUS_SCHEDULES_DATA = [
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Pickup Location": "Sahara - ENOC Fuel Station / Foot Bridge", "Pickup Time": "06:25 AM", "Vendor": "Mango Transport", "Coordinator": "0525539471 / 0555309916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Pickup Location": "Stadium Metro / Al Nahda / DAFZA / Etisalat Metro", "Pickup Time": "06:35 AM", "Vendor": "Mango Transport", "Coordinator": "0525539471 / 0555309916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-02", "Plate No": "DXB-10102 (Temp)", "Pickup Location": "Rashidiya Metro / International City / DIP Metro", "Pickup Time": "06:35 AM", "Vendor": "Mango Transport", "Coordinator": "0525539471 / 0555309916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Temp)", "Pickup Location": "Abuhail / Abubacker / Baniyas / Salah Din / Union / Al Rigga", "Pickup Time": "06:25 AM", "Vendor": "Mango Transport", "Coordinator": "0525539471 / 0555309916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-04", "Plate No": "DXB-10104 (Temp)", "Pickup Location": "Al Ghubaiba / Sharaf DG / Burjuman / ADCB / Satwa / WTC", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "0525539471 / 0555309916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-05", "Plate No": "DXB-10105 (Temp)", "Pickup Location": "Onpassive / MOE / Mashreq / Internet City / Gardens / Expo", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "0525539471 / 0555309916"},
    {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-06", "Plate No": "DXB-10106 (Temp)", "Pickup Location": "Dulsco Camps (Al Quoz, Liwan, Rahaba) & EFS Camps", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "0525539471 / 0555309916"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-07", "Plate No": "DXB-20201 (Temp)", "Pickup Location": "Sahara Stops (4:20 PM) / DAFZA (4:40 PM) / Etisalat (4:45 PM)", "Pickup Time": "04:20 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "0555309916 / 0525539471"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-08", "Plate No": "DXB-20202 (Temp)", "Pickup Location": "Abuhail / Abubacker / Baniyas / Salah Din / Union / Al Rigga", "Pickup Time": "04:25 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "0555309916 / 0525539471"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-09", "Plate No": "DXB-20203 (Temp)", "Pickup Location": "Rashidiya (4:35 PM) / Intl City (4:50 PM) / DIP MS (5:15 PM)", "Pickup Time": "04:35 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "+971 58 588 7560"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-10", "Plate No": "DXB-20204 (Temp)", "Pickup Location": "Ghubaiba / Al Fahidi / Burjuman / ADCB / Financial Ctr / MOE", "Pickup Time": "04:10 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "+971 58 588 7560"},
    {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-11", "Plate No": "DXB-20205 (Temp)", "Pickup Location": "Internet City / Discovery Gardens / Satwa / Dulsco & EFS Camps", "Pickup Time": "04:30 PM", "Vendor": "Mango / Shahara Sky", "Coordinator": "+971 58 588 7560"},
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-01", "Plate No": "AUH-50101 (Temp)", "Pickup Location": "Dulsco ICAD-1 Bus Stop & Dulsco Camp", "Pickup Time": "06:15 AM", "Vendor": "Dulsco", "Coordinator": "AUH Transport Team"},
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-02", "Plate No": "AUH-50102 (Temp)", "Pickup Location": "Dulsco Al Razeen Camp Abu Dhabi", "Pickup Time": "06:00 AM", "Vendor": "Dulsco", "Coordinator": "AUH Transport Team"},
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-03", "Plate No": "AUH-50103 (Temp)", "Pickup Location": "Abu Dhabi Mall / Al Salama Hospital / Central Bus Station", "Pickup Time": "06:10 AM", "Vendor": "Fastlink", "Coordinator": "AUH Transport Team"},
    {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-04", "Plate No": "AUH-50104 (Temp)", "Pickup Location": "Shinning Tower / LifeLine Hospital / Shabiya 10-12 / Filli Cafe", "Pickup Time": "06:15 AM", "Vendor": "Fastlink", "Coordinator": "AUH Transport Team"},
    {"Site": "AUH1", "Shift": "Night Shift", "Bus No": "AUH-05", "Plate No": "AUH-50201 (Temp)", "Pickup Location": "ICAD-1 / Al Razeen / Abu Dhabi Mall / Al Salama / Shinning Tower", "Pickup Time": "04:15 PM", "Vendor": "Dulsco / Fastlink", "Coordinator": "AUH Transport Team"},
    {"Site": "DXB3", "Shift": "Day Shift", "Bus No": "DXB3-01", "Plate No": "DXB-30101 (Temp)", "Pickup Location": "Deira / BurJuman / Satwa / Camps Route", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "0525539471"},
    {"Site": "DXB3", "Shift": "Night Shift", "Bus No": "DXB3-02", "Plate No": "DXB-30201 (Temp)", "Pickup Location": "Deira / BurJuman / Satwa / Camps Route", "Pickup Time": "04:30 PM", "Vendor": "Mango Transport", "Coordinator": "0525539471"},
]


@dataclass
class Roster:
    df: pd.DataFrame
    date: pd.Timestamp | None
    day_name: str | None
    warnings: list[str]


def load_roster(file) -> Roster:
    xl = pd.ExcelFile(file)
    sheet_to_read = "Roster" if "Roster" in xl.sheet_names else xl.sheet_names[0]
    raw = pd.read_excel(xl, sheet_name=sheet_to_read, header=None, dtype=object)

    col0_clean = raw.iloc[:, 0].astype(str).str.strip().str.lower()
    hdr_rows = raw.index[col0_clean.isin(["sr no", "sr", "sr. no.", "s.no"])]
    if len(hdr_rows) == 0:
        raise ValueError("Could not find header row ('Sr No' or 'SR' in column A) on the Roster sheet.")
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
    defaults = [
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
    ]
    for req_col, default_val in defaults:
        if req_col not in df.columns:
            df[req_col] = default_val
            warnings.append(f"Column '{req_col}' was missing and defaulted to '{default_val}'.")

    for c in df.columns:
        if c != "DOJ":
            df[c] = df[c].map(lambda v: v.strip() if isinstance(v, str) else v)

    for c in ("OFF1", "OFF2"):
        df[c] = df[c].map(lambda v: v.capitalize() if isinstance(v, str) and v.upper() != "OT" else ("OT" if isinstance(v, str) else v))

    df["Building"] = df["Building"].astype(str).str.upper()

    if "Attendance" not in df.columns:
        df["Attendance"] = "P"
        warnings.append("No 'Attendance' column found in workbook; defaulted Direct rows to 'P'.")

    def clean_att(v):
        if pd.isna(v):
            return ""
        if isinstance(v, (int, float)) and float(v) == 0:
            return "0"
        return str(v).strip().upper()

    df["Att"] = df["Attendance"].map(clean_att).replace({"ABWI": "AB"})
    df["DOJ"] = pd.to_datetime(df["DOJ"], errors="coerce")
    df["Psoft No"] = pd.to_numeric(df["Psoft No"], errors="coerce")
    df["Sr No"] = pd.to_numeric(df["Sr No"], errors="coerce")
    df["OT"] = (df["OFF1"] == "OT") | (df["OFF2"] == "OT")
    df["Is Direct"] = df["Type"].astype(str).str.lower().eq("direct")
    return Roster(df=df, date=date, day_name=day_name, warnings=warnings)


def _count(df_sub: pd.DataFrame) -> dict:
    vc = df_sub["Att"].value_counts()
    g = lambda k: int(vc.get(k, 0))
    total = len(df_sub)
    unsched, off, pl, p, sl, ab = g("0"), g("OFF"), g("PL"), g("P"), g("SL"), g("AB")
    ot = int(df_sub["OT"].sum())
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
    cond = (targets["Site"] == site) & (targets["Department"] == dept) & (targets["Shift"] == shift) & (targets["Employee Type"] == etype)
    t = targets[cond]
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
    out["Target Achievement"] = [np.nan if (pd.isna(t) or t == 0) else _pct(p, t) for p, t in zip(out["Present %"], out["LM Target"])]
    cols = ["Shift", "Total HC", "Unscheduled", "Schedule to Work", "PL", "OT", "UPL", "Present", "Present %", "LM Target", "Target Achievement"]
    return out[cols]


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
            rows.append({
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
            })
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
    out["Target Achievement"] = [np.nan if pd.isna(t) or t == 0 else _pct(p, t) for p, t in zip(out["Present %"], out["LM Target"])]
    cols = ["Employee Type", "Total HC", "Unscheduled", "Schedule to Work", "PL", "OT", "UPL", "Present", "Present %", "LM Target", "Target Achievement"]
    return out[cols]


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
        rows.append({
            "Site": label,
            "Today's HC": h["Today's HC"],
            "Prev Day HC": h["Previous Day HC"],
            "Change": h["Change vs Prev Day"],
            "Schedule to Work": s["Schedule to Work"],
            "Present": s["Present"],
            "Present %": s["Present %"],
            "LM Target": s["LM Target"],
            "Target Achievement": s["Target Achievement"],
        })
    out = pd.DataFrame(rows)
    if len(out) == 0:
        cols = ["Site", "Today's HC", "Prev Day HC", "Change", "Schedule to Work", "Present", "Present %", "LM Target", "Target Achievement"]
        return pd.DataFrame(columns=cols)
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
    df_q = roster.df
    checks = []

    def add(name, n, detail=""):
        checks.append({"Check": name, "Rows": int(n), "Status": "OK" if n == 0 else "Review", "Detail": detail})

    bad_att = ~df_q["Att"].isin(ATT_ORDER)
    add("Attendance not in 0 / OFF / PL / P / SL / AB / ABWI", bad_att.sum(), ", ".join(sorted(set(df_q.loc[bad_att, "Attendance"].astype(str)))[:8]))
    add("Duplicate Psoft No", df_q["Psoft No"].dropna().duplicated(keep=False).sum())
    add("Duplicate AMZ ID", df_q["AMZ ID"].dropna().duplicated(keep=False).sum())
    add("Duplicate Employee Name", df_q["Employee Name"].astype(str).str.lower().duplicated(keep=False).sum(), "may be legitimate")
    add("Missing Line Manager", df_q["Line Manager"].isna().sum())
    add("Missing Department / Shift / Building", (df_q["Department"].isna() | df_q["Shift"].isna() | df_q["Building"].isna()).sum())
    add("OT marked but Attendance is not P", (df_q["OT"] & (df_q["Att"] != "P")).sum())
    add("Same weekday in OFF1 and OFF2", (df_q["OFF1"].eq(df_q["OFF2"]) & df_q["OFF1"].notna() & (df_q["OFF1"] != "")).sum())
    if "Pickup point" in df_q.columns:
        add("Missing Transport Pickup Point", df_q["Pickup point"].isna().sum(), "Employees without assigned bus stop")
    return pd.DataFrame(checks)


def to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, frame in sheets.items():
            frame.to_excel(xw, sheet_name=name[:31], index=False)
    return buf.getvalue()


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
    cols = [by, "Scheduled", "P", "PL", "SL", "AB", "UPL (SL+AB)", "UPL %", "OFF"]
    if len(d) == 0 or by not in d.columns:
        return pd.DataFrame(columns=cols)
    ct = pd.crosstab(d[by].fillna("Unassigned"), d["Att"])
    for c in ["P", "SL", "AB", "PL", "OFF"]:
        if c not in ct.columns:
            ct[c] = 0
    ct["Scheduled"] = ct[["P", "SL", "AB", "PL"]].sum(axis=1)
    ct["UPL (SL+AB)"] = ct["SL"] + ct["AB"]
    ct["UPL %"] = np.where(ct["Scheduled"] > 0, ct["UPL (SL+AB)"] / ct["Scheduled"].replace(0, np.nan), np.nan)
    return ct.reset_index()[cols]


st.sidebar.title("📊 DMD & Transport")
upload = st.sidebar.file_uploader("Upload Main Roster / DMD (.xlsx)", type=["xlsx", "xlsm"], key="main_upload")
trans_upload = st.sidebar.file_uploader("Optional: Upload Transport Roster (.xlsx)", type=["xlsx", "xlsm"], key="trans_upload")

default_files = sorted(Path(__file__).parent.glob("*.xlsx"))
if upload is not None:
    data_bytes, source_name = upload.getvalue(), upload.name
elif default_files:
    data_bytes, source_name = default_files[-1].read_bytes(), default_files[-1].name
else:
    st.title("Daily Manpower & Transport Dashboard")
    st.info("👈 Upload your **Daily DMD workbook** or **Site Roster (AUH1 / DXB5 / DXB3)** in the sidebar to get started.")
    st.stop()


@st.cache_data(show_spinner="Reading workbook…")
def read_roster_cached(b: bytes):
    return load_roster(io.BytesIO(b))


try:
    roster = read_roster_cached(data_bytes)
except Exception as exc:
    st.error(f"Could not read the Roster sheet: {exc}")
    st.stop()

df = roster.df

if trans_upload is not None:
    try:
        trans_roster_df = read_roster_cached(trans_upload.getvalue()).df
    except Exception as exc:
        st.sidebar.warning(f"Could not read Transport Roster: {exc}")
        trans_roster_df = df
else:
    trans_roster_df = df

st.sidebar.caption(f"Active File: **{source_name}**")
with st.sidebar.expander("Headcount inputs", expanded=False):
    prev_hc, remarks = {}, {}
    for s in SITES:
        prev_hc[s] = int(st.number_input(f"{s} – previous day HC", min_value=0, value=int(DEFAULT_PREV_HC.get(s, 100)), step=1, key=f"prev_{s}"))
        remarks[s] = st.text_input(f"{s} – remarks", value=DEFAULT_REMARKS.get(s, ""), key=f"rem_{s}")

with st.sidebar.expander("LM targets (editable)", expanded=False):
    targets = st.data_editor(
        DEFAULT_TARGETS,
        key="targets_editor",
        hide_index=True,
        num_rows="fixed",
        disabled=["Site", "Department", "Shift", "Employee Type"],
        column_config={"LM Target": st.column_config.NumberColumn("LM Target", min_value=0.0, max_value=1.0, step=0.0001, format="%.4f")},
    )

title_date = f"{roster.day_name or ''} {roster.date:%d %b %Y}".strip() if pd.notna(roster.date) else ""
st.title("Daily Manpower & Transport Dashboard")
st.caption(f"{title_date}  ·  {len(df):,} roster rows  ·  Direct headcount & Multi-Site Transport Tracking")

overview = all_sites_overview(df, targets, prev_hc)


def render_site(site: str):
    label = SITES[site][2]
    hc = headcount_block(df, site, prev_hc[site])
    shifts = shift_summary(df, site, targets)
    gt = shifts.iloc[-1]

    c = st.columns(6)
    today_hc = hc[TODAY]
    c[0].metric("Today's HC", f"{today_hc:,}", delta=f"{hc['Change vs Prev Day']:+d} vs prev day", delta_color="off")
    c[1].metric("FTE (Regular)", f"{hc['FTE HC']:,}")
    c[2].metric("NFTE (Temporary)", f"{hc['NFTE HC']:,}")
    c[3].metric("L3 Ops Supervisors", f"{hc['L3 Ops Supervisors']:,}")
    delta_txt = None if pd.isna(gt["LM Target"]) or gt["LM Target"] == 0 else f"{(gt['Present %'] - gt['LM Target']) * 100:+.1f} pts vs target"
    c[4].metric("Present %", pct(gt["Present %"]), delta=delta_txt)
    c[5].metric("Target achievement", pct(gt["Target Achievement"]))
    if remarks.get(site):
        st.caption(f"📝 {remarks[site]}")

    st.subheader(f"{label} – by shift")
    sh = blank_zero_targets(shifts)
    sh.insert(len(sh.columns), "Status", sh["Target Achievement"].map(status))
    show_df(sh, pct_cols=["Present %", "LM Target", "Target Achievement"])

    left, right = st.columns(2)
    with left:
        f = go.Figure()
        s_only = sh[sh["Shift"] != "Grand Total"]
        f.add_bar(x=s_only["Shift"], y=s_only["Present %"] * 100, name="Present %")
        f.add_scatter(x=s_only["Shift"], y=s_only["LM Target"] * 100, mode="markers", name="LM target", marker=dict(symbol="diamond", size=12, color="#d62728"))
        f.update_layout(title="Present % vs LM target", yaxis_title="%", yaxis_range=[0, 105], margin=dict(t=50, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.15))
        show_chart(f)
    with right:
        d = site_frame(df, site)
        d = d[d["Is Direct"]]
        mix = pd.crosstab(d["Shift"], d["Att"]).reindex(SHIFTS).fillna(0)
        names = {"P": "Present", "PL": "Planned leave", "SL": "Sick leave", "AB": "Absent", "OFF": "Weekly off", "0": "Unscheduled"}
        f2 = go.Figure()
        for code in ["P", "PL", "SL", "AB", "OFF", "0"]:
            if code in mix.columns:
                f2.add_bar(x=mix.index, y=mix[code], name=names[code])
        f2.update_layout(barmode="stack", title="Attendance mix by shift (HC)", margin=dict(t=50, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.15))
        show_chart(f2)

    st.subheader("Department × shift")
    det = dept_shift_detail(df, site, targets)
    hide_empty = st.checkbox("Hide empty rows", value=True, key=f"hide_{site}")
    if hide_empty:
        det = det[det["Grand Total"] > 0]
    det = blank_zero_targets(det, "Target")
    det["Status"] = [status(a / t) if pd.notna(a) and pd.notna(t) and t else "" for a, t in zip(det["Actual % (w/o OT)"], det["Target"])]
    keep = ["Department", "Shift", "OFF", "PL", "Present (incl. OT)", "OT", "SL", "AB/ABWI", "Grand Total", "Scheduled", "Target", "Actual % (w/o OT)", "Expected HC", "Actual HC", "Delta HC", "Status"]
    if det["0"].sum() > 0:
        keep.insert(2, "0")
    show_df(det[keep], pct_cols=["Target", "Actual % (w/o OT)"])

    if site == "DXB8":
        st.subheader("Regular vs Temporary")
        ts = blank_zero_targets(type_summary(df, site, targets))
        ts["Status"] = ts["Target Achievement"].map(status)
        show_df(ts, pct_cols=["Present %", "LM Target", "Target Achievement"])


tab_ov, tab_dxb5, tab_auh1, tab_dxb8, tab_dwc3, tab_trans, tab_abs, tab_roster, tab_dq = st.tabs([
    "Overview", "DXB5", "AUH1", "DXB8 (SC)", "DWC3", "🚌 Transport & Live Tracking", "Absence & exceptions", "Roster explorer", "Data checks"
])

with tab_ov:
    if len(overview):
        tot = overview.iloc[-1]
        k = st.columns(5)
        k[0].metric("Total HC (all sites)", f"{int(tot[TODAY]):,}", delta=f"{int(tot['Change']):+d} vs prev day", delta_color="off")
        k[1].metric("Scheduled to work", f"{int(tot['Schedule to Work']):,}")
        k[2].metric("Present (w/o OT)", f"{int(tot['Present']):,}")
        k[3].metric("Present %", pct(tot["Present %"]))
        k[4].metric("Target achievement", pct(tot["Target Achievement"]))

        ov = blank_zero_targets(overview)
        ov["Status"] = ov["Target Achievement"].map(status)
        show_df(ov, pct_cols=["Present %", "LM Target", "Target Achievement"])

with tab_dxb5:
    render_site("DXB5")
with tab_auh1:
    render_site("AUH1")
with tab_dxb8:
    render_site("DXB8")
with tab_dwc3:
    render_site("DWC3")

with tab_trans:
    st.subheader("🚌 Amazon Multi-Site Employee Transport & Live Bus Tracking")
    st.caption("Manage buses, plate numbers, pickup timings, WhatsApp live driver locations, and employee pickup manifests across **AUH1, DXB5, and DXB3**.")

    if "fleet_df" not in st.session_state:
        st.session_state.fleet_df = pd.DataFrame([
            {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Edit)", "Route": "Sahara / Al Nahda / DAFZA / Etisalat", "Capacity": 50, "Driver Name": "Driver 1", "Driver Phone": "971525539471", "Live Location / WhatsApp URL": "https://wa.me/971525539471", "Status": "🟢 On Route"},
            {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-02", "Plate No": "DXB-10102 (Edit)", "Route": "Rashidiya / Intl City / DIP Metro", "Capacity": 50, "Driver Name": "Driver 2", "Driver Phone": "971555309916", "Live Location / WhatsApp URL": "https://wa.me/971555309916", "Status": "🟢 On Route"},
            {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Edit)", "Route": "Abuhail / Baniyas / Salah Din / Union / Al Rigga", "Capacity": 50, "Driver Name": "Driver 3", "Driver Phone": "971525539471", "Live Location / WhatsApp URL": "https://wa.me/971525539471", "Status": "🟢 On Route"},
            {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-04", "Plate No": "DXB-10104 (Edit)", "Route": "Ghubaiba / Burjuman / Satwa / WTC / MOE", "Capacity": 50, "Driver Name": "Driver 4", "Driver Phone": "971555309916", "Live Location / WhatsApp URL": "https://wa.me/971555309916", "Status": "🟢 On Route"},
            {"Site": "DXB5", "Shift": "Day Shift", "Bus No": "DXB-05", "Plate No": "DXB-10105 (Edit)", "Route": "Dulsco & EFS Camps (Al Quoz, Jabel Ali, Rahaba)", "Capacity": 60, "Driver Name": "Driver 5", "Driver Phone": "971525539471", "Live Location / WhatsApp URL": "https://wa.me/971525539471", "Status": "🟢 On Route"},
            {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-07", "Plate No": "DXB-20201 (Edit)", "Route": "Sahara / DAFZA / Etisalat / Deira Metro Route", "Capacity": 50, "Driver Name": "Driver 6", "Driver Phone": "971585887560", "Live Location / WhatsApp URL": "https://wa.me/971585887560", "Status": "🟢 On Route"},
            {"Site": "DXB5", "Shift": "Night Shift", "Bus No": "DXB-08", "Plate No": "DXB-20202 (Edit)", "Route": "Burjuman / Financial Ctr / MOE / Camps Route", "Capacity": 60, "Driver Name": "Driver 7", "Driver Phone": "971585887560", "Live Location / WhatsApp URL": "https://wa.me/971585887560", "Status": "🟢 On Route"},
            {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-01", "Plate No": "AUH-50101 (Edit)", "Route": "Dulsco ICAD-1 Bus Stop & Dulsco Camp", "Capacity": 65, "Driver Name": "Driver 8", "Driver Phone": "971500000001", "Live Location / WhatsApp URL": "https://wa.me/971500000001", "Status": "🟢 On Route"},
            {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-02", "Plate No": "AUH-50102 (Edit)", "Route": "Dulsco Al Razeen Camp Abu Dhabi", "Capacity": 65, "Driver Name": "Driver 9", "Driver Phone": "971500000002", "Live Location / WhatsApp URL": "https://wa.me/971500000002", "Status": "🟢 On Route"},
            {"Site": "AUH1", "Shift": "Day Shift", "Bus No": "AUH-03", "Plate No": "AUH-50103 (Edit)", "Route": "Abu Dhabi Mall / Al Salama / Shinning Tower / LifeLine", "Capacity": 55, "Driver Name": "Driver 10", "Driver Phone": "971500000003", "Live Location / WhatsApp URL": "https://wa.me/971500000003", "Status": "🟢 On Route"},
            {"Site": "AUH1", "Shift": "Night Shift", "Bus No": "AUH-04", "Plate No": "AUH-50201 (Edit)", "Route": "ICAD-1 / Al Razeen / City Center / Shabiya 10-12", "Capacity": 65, "Driver Name": "Driver 11", "Driver Phone": "971500000004", "Live Location / WhatsApp URL": "https://wa.me/971500000004", "Status": "🟢 On Route"},
            {"Site": "DXB3", "Shift": "Day Shift", "Bus No": "DXB3-01", "Plate No": "DXB-30101 (Edit)", "Route": "DXB3 Main Metro & Accommodation Route", "Capacity": 50, "Driver Name": "Driver 12", "Driver Phone": "971525539471", "Live Location / WhatsApp URL": "https://wa.me/971525539471", "Status": "🟢 On Route"},
        ])

    fc1, fc2, fc3 = st.columns(3)
    sel_site = fc1.selectbox("Select Site", ["All Sites", "AUH1", "DXB5", "DXB3"], key="tr_site")
    sel_shift = fc2.selectbox("Select Shift", ["All Shifts", "Day Shift", "Night Shift", "Mid Shift"], key="tr_shift")
    search_emp = fc3.text_input("🔍 Search Employee Login / Name / Pickup Point", key="tr_search")

    tdf = trans_roster_df.copy()
    if sel_site != "All Sites":
        tdf = tdf[tdf["Building"] == sel_site]
    if sel_shift != "All Shifts":
        tdf = tdf[tdf["Shift"] == sel_shift]

    fleet_view = st.session_state.fleet_df.copy()
    if sel_site != "All Sites":
        fleet_view = fleet_view[fleet_view["Site"] == sel_site]
    if sel_shift != "All Shifts":
        fleet_view = fleet_view[fleet_view["Shift"] == sel_shift]

    has_pickup = "Pickup point" in tdf.columns
    assigned_count = int(tdf["Pickup point"].notna().sum()) if has_pickup else 0
    missing_count = int(tdf["Pickup point"].isna().sum()) if has_pickup else len(tdf)

    tm1, tm2, tm3, tm4 = st.columns(4)
    tm1.metric("Active Buses", f"{len(fleet_view)}")
    tm2.metric("Total Bus Capacity", f"{int(fleet_view['Capacity'].sum()):,} seats")
    tm3.metric("Employees w/ Pickup Point", f"{assigned_count:,}")
    tm4.metric("Pending / Missing Pickup", f"{missing_count:,}")

    st.markdown("### 📍 Live Bus Fleet, Plate Numbers & Driver WhatsApp Location")
    st.caption("Double-click any cell below to update **Original Plate Numbers**, **Driver Phone**, or paste a **WhatsApp / Google Maps Live Location link**.")
    edited_fleet = st.data_editor(
        fleet_view,
        hide_index=True,
        num_rows="dynamic",
        key="fleet_editor",
        column_config={
            "Live Location / WhatsApp URL": st.column_config.LinkColumn(
                "Live Location / WhatsApp",
                help="Paste WhatsApp wa.me link or Google Maps Live Location link",
                display_text="📍 Open Live Location / Chat",
            )
        },
    )

    st.markdown("### 🕒 Official Bus Pickup Timings & Routes (DXB5, AUH1, DXB3)")
    sched_df = pd.DataFrame(BUS_SCHEDULES_DATA)
    if sel_site != "All Sites":
        sched_df = sched_df[sched_df["Site"] == sel_site]
    if sel_shift != "All Shifts":
        sched_df = sched_df[sched_df["Shift"] == sel_shift]
    show_df(sched_df)

    st.markdown("### 👥 Pickup Point Summary & Employee Manifest (Logins & Locations)")
    if has_pickup:
        if search_emp:
            q_low = search_emp.lower()
            mask = (
                tdf["AMZ ID"].astype(str).str.lower().str.contains(q_low, regex=False)
                | tdf["Employee Name"].astype(str).str.lower().str.contains(q_low, regex=False)
                | tdf["Pickup point"].astype(str).str.lower().str.contains(q_low, regex=False)
            )
            tdf = tdf[mask]

        p_left, p_right = st.columns([1, 2])
        with p_left:
            st.markdown("**Headcount by Pickup Point**")
            pickup_counts = tdf.groupby(["Pickup point", "Shift"], dropna=False).size().reset_index(name="Employees").sort_values("Employees", ascending=False)
            pickup_counts["Pickup point"] = pickup_counts["Pickup point"].fillna("⚠️ Pending / Unassigned")
            show_df(pickup_counts)

        with p_right:
            st.markdown("**Employee Pickup Manifest (Logins & Stops)**")
            cand_cols = ["AMZ ID", "Employee Name", "Building", "Shift", "Department", "3P", "Pickup point", "As per Transport Tracker", "Phone number"]
            manifest_cols = [c for c in cand_cols if c in tdf.columns]
            manifest_df = tdf[manifest_cols].sort_values(by=["Pickup point", "Employee Name"], na_position="last")
            show_df(manifest_df)
            st.download_button(
                "⬇️ Download Filtered Bus Manifest (CSV)",
                manifest_df.to_csv(index=False).encode("utf-8"),
                file_name=f"Transport_Manifest_{sel_site}_{sel_shift}.csv",
                mime="text/csv",
            )
    else:
        st.info("Upload AUH1-14102026.xlsx in the sidebar ('Optional: Upload Transport Roster') to view employee pickup locations.")

with tab_abs:
    st.subheader("Absence & leave")
    f1, f2, f3 = st.columns(3)
    avail_buildings = sorted(df["Building"].dropna().unique())
    sel_b = f1.multiselect("Building", avail_buildings, default=avail_buildings, key="abs_b")
    sel_codes = f2.multiselect("Attendance", ["AB", "SL", "PL"], default=["AB", "SL"], key="abs_c")
    direct_only = f3.checkbox("Direct only", value=True, key="abs_direct")

    base = df[df["Building"].isin(sel_b)]
    if direct_only:
        base = base[base["Is Direct"]]

    m1, m2, m3 = st.columns(3)
    m1.metric("Absent (AB/ABWI)", int((base["Att"] == "AB").sum()))
    m2.metric("Sick leave (SL)", int((base["Att"] == "SL").sum()))
    m3.metric("Planned leave (PL)", int((base["Att"] == "PL").sum()))

    left, right = st.columns(2)
    with left:
        st.markdown("**By line manager** (top 15 by unplanned leave)")
        mt = crosstab_att(base, "Line Manager").sort_values(["UPL (SL+AB)", "Scheduled"], ascending=False).head(15)
        show_df(mt, pct_cols=["UPL %"])
    with right:
        st.markdown("**By 3P vendor**")
        show_df(crosstab_att(base, "3P").sort_values("UPL (SL+AB)", ascending=False), pct_cols=["UPL %"])

    st.markdown("**Employee list**")
    cand_abs = ["AMZ ID", "Employee Name", "Building", "Shift", "Department", "Process Path", "3P", "Line Manager", "Attendance", "Remarks"]
    abs_cols = [c for c in cand_abs if c in base.columns]
    lst = base[base["Att"].isin(sel_codes)][abs_cols].sort_values(["Building", "Department", "Employee Name"])
    show_df(lst)
    st.download_button("Download absence list (CSV)", lst.to_csv(index=False).encode("utf-8"), file_name="absence_list.csv", mime="text/csv")

with tab_roster:
    st.subheader("Roster explorer")
    c1, c2, c3, c4 = st.columns(4)
    b = c1.multiselect("Building", sorted(df["Building"].dropna().unique()), key="r_b")
    sft = c2.multiselect("Shift", sorted(df["Shift"].dropna().unique()), key="r_s")
    dep = c3.multiselect("Department", sorted(df["Department"].dropna().unique()), key="r_d")
    att = c4.multiselect("Attendance", sorted(df["Attendance"].dropna().unique()), key="r_a")
    q = st.text_input("Search Name / AMZ ID / Psoft No / Line Manager / Pickup Point", key="r_q")

    v = df.copy()
    for col, sel in [("Building", b), ("Shift", sft), ("Department", dep), ("Attendance", att)]:
        if sel and col in v.columns:
            v = v[v[col].isin(sel)]
    if q:
        ql = q.lower()
        mask = (
            v["Employee Name"].astype(str).str.lower().str.contains(ql, regex=False)
            | v["AMZ ID"].astype(str).str.lower().str.contains(ql, regex=False)
            | v["Psoft No"].astype(str).str.contains(ql, regex=False)
            | v["Line Manager"].astype(str).str.lower().str.contains(ql, regex=False)
        )
        if "Pickup point" in v.columns:
            mask = mask | v["Pickup point"].astype(str).str.lower().str.contains(ql, regex=False)
        v = v[mask]

    st.caption(f"Showing {len(v):,} of {len(df):,} rows")
    desired_cols = ["Sr No", "Psoft No", "AMZ ID", "Employee Name", "Employee Type", "Building", "Shift", "OFF1", "OFF2", "Job Title", "Department", "Type", "3P", "Line Manager", "Pickup point", "Attendance", "Remarks", "DOJ", "Process Path"]
    avail_cols = [c for c in desired_cols if c in v.columns]
    show_df(v[avail_cols])
    st.download_button("Download filtered roster (CSV)", v[avail_cols].to_csv(index=False).encode("utf-8"), file_name="roster_filtered.csv", mime="text/csv")

with tab_dq:
    st.subheader("Data checks")
    for w in roster.warnings:
        st.info(w)
    dq = quality_checks(roster)
    dq["Status"] = dq["Status"].map({"OK": "✅ OK", "Review": "⚠️ Review"})
    show_df(dq)

sheets = {"Overview": overview}
for s in SITES:
    if len(site_frame(df, s)) > 0:
        sheets[f"{s} shifts"] = shift_summary(df, s, targets)
        sheets[f"{s} departments"] = dept_shift_detail(df, s, targets)
if len(site_frame(df, "DXB8")) > 0:
    sheets["DXB8 reg-temp"] = type_summary(df, "DXB8", targets)

st.sidebar.download_button(
    "⬇️ Export summary (Excel)",
    to_excel_bytes(sheets),
    file_name=f"DMD_summary_{roster.date:%d%m%Y}.xlsx" if pd.notna(roster.date) else "DMD_summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

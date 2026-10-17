"""
Daily Manpower Dashboard (DMD) – Streamlit app
Run:  streamlit run app.py
Upload the daily DMD workbook (needs a 'Roster' sheet) or drop it next to this file as DMD*.xlsx.
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dmd_engine as E

st.set_page_config(page_title="Daily Manpower Dashboard", page_icon="📊", layout="wide")

# ----------------------------------------------------------------------------- helpers
TODAY = "Today's HC"


def _call(fn, *args, **kwargs):
    """Stretch-to-width across Streamlit versions (width='stretch' vs use_container_width)."""
    try:
        return fn(*args, width="stretch", **kwargs)
    except Exception:  # older Streamlit
        return fn(*args, use_container_width=True, **kwargs)


def show_df(df: pd.DataFrame, pct_cols=(), **kwargs):
    """Render a dataframe; fractions in `pct_cols` are shown as percentages."""
    d = df.copy()
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


def blank_zero_targets(df: pd.DataFrame, col="LM Target") -> pd.DataFrame:
    d = df.copy()
    d[col] = d[col].replace(0, np.nan)
    return d


def crosstab_att(d: pd.DataFrame, by: str) -> pd.DataFrame:
    ct = pd.crosstab(d[by], d["Att"])
    for c in ["P", "SL", "AB", "PL", "OFF"]:
        if c not in ct.columns:
            ct[c] = 0
    ct["Scheduled"] = ct[["P", "SL", "AB", "PL"]].sum(axis=1)
    ct["UPL (SL+AB)"] = ct["SL"] + ct["AB"]
    ct["UPL %"] = np.where(ct["Scheduled"] > 0, ct["UPL (SL+AB)"] / ct["Scheduled"].replace(0, np.nan), np.nan)
    return ct.reset_index()[[by, "Scheduled", "P", "PL", "SL", "AB", "UPL (SL+AB)", "UPL %", "OFF"]]


# ----------------------------------------------------------------------------- data source
st.sidebar.title("📊 DMD")
upload = st.sidebar.file_uploader("Daily DMD workbook (.xlsx)", type=["xlsx", "xlsm"])
default_files = sorted(Path(__file__).parent.glob("DMD*.xlsx"))
if upload is not None:
    data_bytes, source_name = upload.getvalue(), upload.name
elif default_files:
    data_bytes, source_name = default_files[-1].read_bytes(), default_files[-1].name
else:
    st.title("Daily Manpower Dashboard")
    st.info("Upload the daily DMD workbook in the sidebar to get started (it must contain a **Roster** sheet).")
    st.stop()


@st.cache_data(show_spinner="Reading roster…")
def read_roster(b: bytes):
    return E.load_roster(io.BytesIO(b))


try:
    roster = read_roster(data_bytes)
except Exception as exc:  # noqa: BLE001
    st.error(f"Could not read the Roster sheet: {exc}")
    st.stop()
df = roster.df

# ----------------------------------------------------------------------------- sidebar inputs
st.sidebar.caption(f"Source: {source_name}")
with st.sidebar.expander("Headcount inputs (hard-coded in the workbook)", expanded=False):
    prev_hc, remarks = {}, {}
    for s in E.SITES:
        prev_hc[s] = int(st.number_input(f"{s} – previous day HC", min_value=0,
                                         value=int(E.DEFAULT_PREV_HC[s]), step=1, key=f"prev_{s}"))
        remarks[s] = st.text_input(f"{s} – remarks", value=E.DEFAULT_REMARKS[s], key=f"rem_{s}")

with st.sidebar.expander("LM targets (editable)", expanded=False):
    st.caption("Targets are fractions, e.g. 0.8769 = 87.69%. A target of 0 means *no target*.")
    targets = st.data_editor(
        E.DEFAULT_TARGETS,
        key="targets_editor",
        hide_index=True,
        num_rows="fixed",
        disabled=["Site", "Department", "Shift", "Employee Type"],
        column_config={"LM Target": st.column_config.NumberColumn("LM Target", min_value=0.0, max_value=1.0,
                                                                  step=0.0001, format="%.4f")},
    )

# ----------------------------------------------------------------------------- header
title_date = f"{roster.day_name or ''} {roster.date:%d %b %Y}".strip() if roster.date is not None else ""
st.title("Daily Manpower Dashboard")
st.caption(f"{title_date}  ·  {len(df):,} roster rows  ·  Direct headcount only, same logic as the workbook's Dashboard sheet")

overview = E.all_sites_overview(df, targets, prev_hc)

# ----------------------------------------------------------------------------- site tab renderer
def render_site(site: str):
    label = E.SITES[site][2]
    hc = E.headcount_block(df, site, prev_hc[site])
    shifts = E.shift_summary(df, site, targets)
    gt = shifts.iloc[-1]

    c = st.columns(6)
    today_hc = hc[TODAY]
    c[0].metric("Today's HC", f"{today_hc:,}", delta=f"{hc['Change vs Prev Day']:+d} vs prev day",
                delta_color="off")
    c[1].metric("FTE (Regular)", f"{hc['FTE HC']:,}")
    c[2].metric("NFTE (Temporary)", f"{hc['NFTE HC']:,}")
    c[3].metric("L3 Ops Supervisors", f"{hc['L3 Ops Supervisors']:,}")
    c[4].metric("Present %", pct(gt["Present %"]),
                delta=None if pd.isna(gt["LM Target"]) or gt["LM Target"] == 0
                else f"{(gt['Present %'] - gt['LM Target']) * 100:+.1f} pts vs target")
    c[5].metric("Target achievement", pct(gt["Target Achievement"]))
    if remarks[site]:
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
        f.add_scatter(x=s_only["Shift"], y=s_only["LM Target"] * 100, mode="markers", name="LM target",
                      marker=dict(symbol="diamond", size=12, color="#d62728"))
        f.update_layout(title="Present % vs LM target", yaxis_title="%", yaxis_range=[0, 105],
                        margin=dict(t=50, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.15))
        show_chart(f)
    with right:
        d = E.site_frame(df, site)
        d = d[d["Is Direct"]]
        mix = pd.crosstab(d["Shift"], d["Att"]).reindex(E.SHIFTS).fillna(0)
        names = {"P": "Present", "PL": "Planned leave", "SL": "Sick leave", "AB": "Absent", "OFF": "Weekly off", "0": "Unscheduled"}
        f2 = go.Figure()
        for code in ["P", "PL", "SL", "AB", "OFF", "0"]:
            if code in mix.columns:
                f2.add_bar(x=mix.index, y=mix[code], name=names[code])
        f2.update_layout(barmode="stack", title="Attendance mix by shift (HC)",
                         margin=dict(t=50, b=10, l=10, r=10), legend=dict(orientation="h", y=-0.15))
        show_chart(f2)

    st.subheader("Department × shift")
    det = E.dept_shift_detail(df, site, targets)
    hide_empty = st.checkbox("Hide empty rows", value=True, key=f"hide_{site}")
    if hide_empty:
        det = det[det["Grand Total"] > 0]
    det = blank_zero_targets(det, "Target")
    det["Status"] = [status(a / t) if pd.notna(a) and pd.notna(t) and

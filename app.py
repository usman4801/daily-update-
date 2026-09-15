import os
from datetime import datetime, timedelta
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Amazon Leave Compliance Monitor", layout="wide")

# --- CUSTOM CSS (Clean White Light Theme Match) ---
st.markdown(
    """
    <style>
    .stApp { background-color: #f1f5f9; }
    .block-container { padding: 1rem 1.8rem !important; max-width: 100% !important; }
    .card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        margin-bottom: 12px;
    }
    .kpi-title { font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; }
    .kpi-val { font-size: 32px; font-weight: 900; color: #0f172a; margin-top: 4px; line-height: 1.1; }
    .kpi-sub { font-size: 11px; font-weight: 600; color: #64748b; margin-top: 4px; }
    .tag-high { background: #fee2e2; color: #dc2626; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    .tag-med { background: #ffedd5; color: #ea580c; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    .tag-valid { background: #dcfce7; color: #16a34a; font-weight: 700; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATE & FILTERS ---
if "view_upl_detail" not in st.session_state:
    st.session_state.view_upl_detail = False

# Top App Header
h_left, h_right = st.columns([7, 3])
with h_left:
    st.markdown(
        "<h3 style='margin:0; font-weight:900; color:#131921;'>amazon <span style='font-weight:400; color:#475569;'>| LEAVE COMPLIANCE & PATTERN MONITOR</span></h3>",
        unsafe_allow_html=True,
    )
with h_right:
    search_id = st.text_input(
        "🔍 Search Associate",
        placeholder="Enter ID or Name...",
        label_visibility="collapsed",
    )

# Filter Strip
f1, f2, f3, f4 = st.columns([2.5, 3, 2, 2.5])
with f1:
    site = st.selectbox(
        "Site", ["AUH1 (Abu Dhabi)", "DXB3", "DXB5"], label_visibility="collapsed"
    )
with f2:
    date_range = st.date_input(
        "Date Range",
        value=[datetime.now().date() - timedelta(days=7), datetime.now().date()],
        label_visibility="collapsed",
    )
with f3:
    shift_filter = st.selectbox(
        "Shift",
        ["All Shifts", "Front-Half Days", "Back-Half Nights"],
        label_visibility="collapsed",
    )
with f4:
    timeframe = st.radio(
        "History Range",
        ["Last 30 Days", "Last 90 Days"],
        horizontal=True,
        label_visibility="collapsed",
    )

st.markdown("<hr style='margin:10px 0; border:0.5px solid #cbd5e1;'>", unsafe_allow_html=True)


# --- CORE LEAVE PATTERN ALGORITHM (Consecutive 1-Day vs 2-Day Detection) ---
def analyze_leave_patterns(roster_records):
    """Calculates single-day and 2-day cluster patterns even when valid medical slips exist."""
    records = []
    for emp_id, group in roster_records.groupby("Psoft No"):
        group = group.sort_values("Date")
        leaves = group[group["Attendance"].isin(["SL", "PL"])].copy()

        if leaves.empty:
            continue

        leaves["Date"] = pd.to_datetime(leaves["Date"])
        leaves["Diff"] = leaves["Date"].diff().dt.days

        # Identify consecutive blocks
        leaves["Block"] = (leaves["Diff"] != 1).cumsum()
        block_sizes = leaves.groupby("Block").size()

        # Counts
        single_day_sl = sum(
            (block_sizes == 1)
            & (
                leaves.groupby("Block")["Attendance"].first() == "SL"
            )  # Isolated 1-day SL
        )
        two_day_sl = sum(
            (block_sizes == 2)
            & (leaves.groupby("Block")["Attendance"].first() == "SL")
        )

        single_day_pl = sum(
            (block_sizes == 1)
            & (leaves.groupby("Block")["Attendance"].first() == "PL")
        )
        two_day_pl = sum(
            (block_sizes == 2)
            & (leaves.groupby("Block")["Attendance"].first() == "PL")
        )

        # Disruption Score (Bradford index concept: Frequency impacts ops more than length)
        # B = S^2 * D where S is number of spells, D is total days
        total_spells = len(block_sizes)
        total_days = len(leaves)
        disruption_score = (total_spells**2) * total_days

        records.append(
            {
                "Psoft No": emp_id,
                "Employee Name": group["Name"].iloc[0],
                "SL 1-Day": single_day_sl,
                "SL 2-Day": two_day_sl,
                "PL 1-Day": single_day_pl,
                "PL 2-Day": two_day_pl,
                "Total Leaves": total_days,
                "Pattern Score": disruption_score,
                "MC Status": (
                    "VALIDATED (Doctor Slip)" if total_days > 2 else "JUSTIFIED"
                ),
            }
        )
    return pd.DataFrame(records)


# --- MOCK DATA FOR ENGINE PREVIEW ---
mock_data = pd.DataFrame(
    [
        {
            "Psoft No": "2030013",
            "Name": "Beran Name",
            "Date": "2026-09-15",
            "Attendance": "SL",
        },
        {
            "Psoft No": "2030013",
            "Name": "Beran Name",
            "Date": "2026-09-17",
            "Attendance": "SL",
        },
        {
            "Psoft No": "2030013",
            "Name": "Beran Name",
            "Date": "2026-09-20",
            "Attendance": "SL",
        },
        {
            "Psoft No": "2030005",
            "Name": "Team Namis",
            "Date": "2026-09-14",
            "Attendance": "SL",
        },
        {
            "Psoft No": "2030005",
            "Name": "Team Namis",
            "Date": "2026-09-15",
            "Attendance": "SL",
        },
        {
            "Psoft No": "2030007",
            "Name": "Athen Names",
            "Date": "2026-09-16",
            "Attendance": "PL",
        },
        {
            "Psoft No": "2030007",
            "Name": "Athen Names",
            "Date": "2026-09-19",
            "Attendance": "SL",
        },
    ]
)

pattern_df = analyze_leave_patterns(mock_data)

# --- MAIN DASHBOARD LAYOUT (Left = UPL Portal, Right = Patterns) ---
col_upl, col_pattern = st.columns([5, 7])

# ================= LEFT: UPL TILE & BREAKDOWN =================
with col_upl:
    st.markdown(
        """
        <div class='card' style='border-left: 5px solid #2563eb;'>
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <div class='kpi-title'>Unplanned Leave (UPL) Reporting</div>
                <span class='tag-high'>Live Shift</span>
            </div>
            <div style='display:flex; gap:30px; margin-top:10px;'>
                <div>
                    <div class='kpi-title'>Total Case Volume</div>
                    <div class='kpi-val'>1,450</div>
                    <div class='kpi-sub'>↑ 1.2% over target</div>
                </div>
                <div>
                    <div class='kpi-title'>Pending Cases</div>
                    <div class='kpi-val'>412</div>
                    <div class='kpi-sub'>Awaiting justification</div>
                </div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    # Clickable button to trigger full internal UPL report
    if not st.session_state.view_upl_detail:
        if st.button("📊 Open Detailed UPL Breakdown (Day/Agency/Week)", use_container_width=True):
            st.session_state.view_upl_detail = True
            st.rerun()
    else:
        if st.button("✖ Close Detailed UPL View", use_container_width=True):
            st.session_state.view_upl_detail = False
            st.rerun()

    # Detailed Sub-view (Day-wise, Agency-wise, Week-wise)
    if st.session_state.view_upl_detail:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(
            ["📅 Day Wise", "🏢 Agency Wise", "📈 Weekly Summary"]
        )

        with tab1:
            st.caption("Day-by-Day Roster Analysis (Target vs Actual)")
            st.dataframe(
                pd.DataFrame(
                    {
                        "Date": ["15-Sep-26", "16-Sep-26", "17-Sep-26"],
                        "HC": [420, 415, 410],
                        "SL": [12, 18, 9],
                        "UPL Trend": ["4.1%", "5.8%", "3.2%"],
                        "Status": ["Over Target", "Over Target", "Within Target"],
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )

        with tab2:
            st.caption("3P Vendor Leave Share & Count")
            st.dataframe(
                pd.DataFrame(
                    {
                        "Agency": ["Quesscorp", "Adecco", "Transguard"],
                        "SL": [14, 8, 11],
                        "Trend": ["6.2%", "3.1%", "4.5%"],
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )

        with tab3:
            st.caption("Sunday-to-Sunday Custom Amazon Weeks")
            st.write("Week 37 Actual: **4.85%** | Target: **3.50%**")
        st.markdown("</div>", unsafe_allow_html=True)

    # Absence Policy Breakdown Donut
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='kpi-title'>Absence Category Ratio</div>",
        unsafe_allow_html=True,
    )
    donut_df = pd.DataFrame(
        {
            "Category": [
                "Medical (Valid Doc)",
                "Single-Day Unannounced",
                "Personal",
                "Other",
            ],
            "Cases": [55, 25, 12, 8],
        }
    )
    donut = (
        alt.Chart(donut_df)
        .mark_arc(innerRadius=45)
        .encode(
            theta="Cases:Q",
            color=alt.Color("Category:N", scale=alt.Scale(scheme="category10")),
            tooltip=["Category", "Cases"],
        )
        .properties(height=170)
    )
    st.altair_chart(donut, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ================= RIGHT: LEAVE PATTERN ANALYSIS ENGINE =================
with col_pattern:
    # Top KPI Split
    p_kpi1, p_kpi2 = st.columns(2)
    with p_kpi1:
        st.markdown(
            """
            <div class='card'>
                <div class='kpi-title'>Single-Day Strategic Leaves</div>
                <div class='kpi-val'>72 <span style='font-size:14px; color:#ea580c;'>Associates</span></div>
                <div class='kpi-sub'>High-Frequency 1-Day pattern (with valid MC)</div>
            </div>
        """,
            unsafe_allow_html=True,
        )
    with p_kpi2:
        st.markdown(
            """
            <div class='card'>
                <div class='kpi-title'>2-Day Consecutive Clusters</div>
                <div class='kpi-val'>35 <span style='font-size:14px; color:#dc2626;'>Associates</span></div>
                <div class='kpi-sub'>Connected directly to Off-Days / Weekends</div>
            </div>
        """,
            unsafe_allow_html=True,
        )

    # Prevalence Day-Wise Stacked Bar Chart
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='kpi-title'>Weekly Pattern Prevalence (Sun - Sat Spike)</div>",
        unsafe_allow_html=True,
    )

    chart_data = pd.DataFrame(
        {
            "Day": [
                "Sun 15",
                "Mon 16",
                "Tue 17",
                "Wed 18",
                "Thu 19",
                "Fri 20",
                "Sat 21",
            ],
            "1-Day Pattern": [45, 65, 30, 25, 20, 58, 62],
            "2-Day Cluster": [35, 45, 15, 12, 10, 42, 50],
        }
    ).melt("Day", var_name="Pattern", value_name="Incidence")

    pattern_chart = (
        alt.Chart(chart_data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Day:N", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Incidence:Q"),
            color=alt.Color(
                "Pattern:N",
                scale=alt.Scale(
                    domain=["1-Day Pattern", "2-Day Cluster"],
                    range=["#0284c7", "#f97316"],
                ),
            ),
            tooltip=["Day", "Pattern", "Incidence"],
        )
        .properties(height=180)
    )

    st.altair_chart(pattern_chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Repeat Defaulter Table
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(
        "<div class='kpi-title'>High-Frequency Defaulters (Even with Approved Documents)</div>",
        unsafe_allow_html=True,
    )

    display_table = pattern_df[
        [
            "Psoft No",
            "Employee Name",
            "SL 1-Day",
            "SL 2-Day",
            "PL 1-Day",
            "PL 2-Day",
            "Pattern Score",
            "MC Status",
        ]
    ]

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pattern Score": st.column_config.ProgressColumn(
                "Disruption Index",
                help="Calculated by Spell frequency ^ 2 * Total Absence Days",
                format="%d",
                min_value=0,
                max_value=150,
            ),
            "MC Status": st.column_config.TextColumn("Compliance Tag"),
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)

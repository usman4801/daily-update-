"""
People Analytics — Sick Leave Pattern Dashboard
================================================
Replicates the reference dashboard UI in Streamlit.

ALL numbers on this dashboard are computed live from an uploaded Excel file.
Nothing is hardcoded. See the "Data format" expander in the sidebar (or
README.md) for the expected Excel schema, and use the "Download template"
button to get a ready-made file to fill in.
"""

import io
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="People Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------------
# THEME / CSS
# ----------------------------------------------------------------------------
CSS = """
<style>
:root{
    --navy-dark:#131a2c;
    --navy-darker:#0b0f1c;
    --bg-main:#f3f5fb;
    --card-bg:#ffffff;
    --text-dark:#1a1f36;
    --text-muted:#8a8fa3;
    --purple:#6a5cf0;
    --purple-light:#efeafe;
    --pink:#ff6b8a;
    --pink-light:#fdeaf0;
    --blue:#4f8ef7;
    --blue-light:#e8f1fe;
    --teal:#14b8a6;
    --teal-light:#e1faf5;
    --green:#1fae5b;
    --green-light:#e6f9ee;
    --amber:#db9a1f;
    --amber-light:#fff3dd;
    --red:#e14b4b;
    --red-light:#fdeaea;
    --radius:16px;
    --shadow:0 2px 10px rgba(20,25,50,0.06);
}

html, body, [class*="css"]{
    font-family:-apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.stApp{ background:var(--bg-main); }
#MainMenu, footer, header{visibility:hidden;}
.block-container{ padding-top:1.1rem; padding-bottom:2rem; max-width:1500px;}

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#151d33 0%, #0b0f1c 100%);
    min-width:255px !important;
}
section[data-testid="stSidebar"] .block-container{padding-top:1.4rem;}
.brand{display:flex;flex-direction:column;gap:0px;margin-bottom:22px;padding:0 4px;}
.brand-row{display:flex;align-items:center;gap:8px;}
.brand-amazon{color:#FF9900;font-weight:800;font-size:22px;letter-spacing:-0.5px;}
.brand-sub{color:#c7cbe0;font-size:12.5px;font-weight:600;line-height:1.2;margin-top:2px;}

div[role="radiogroup"]{gap:2px;}
div[role="radiogroup"] label{
    background:transparent;
    border-radius:10px;
    padding:9px 12px !important;
    margin-bottom:2px;
    color:#aeb3c9 !important;
    font-size:14.5px;
    width:100%;
    transition:background 0.15s;
}
div[role="radiogroup"] label:hover{background:rgba(255,255,255,0.06);}
div[role="radiogroup"] label[data-checked="true"], div[role="radiogroup"] label:has(input:checked){
    background:#2d5bff !important;
    color:#ffffff !important;
    font-weight:600;
}
div[role="radiogroup"] input{display:none;}
div[role="radiogroup"] svg{display:none;}

.promo-box{
    margin-top:28px;
    background:linear-gradient(160deg,#1a2340,#0e1424);
    border:1px solid rgba(255,255,255,0.06);
    border-radius:14px;
    padding:16px;
    color:#fff;
}
.promo-box h4{margin:0 0 6px 0;font-size:15px;font-weight:700;color:#fff;}
.promo-box p{margin:0;font-size:12.5px;color:#9aa0bd;line-height:1.4;}

/* ---------- TOP BAR ---------- */
.topbar{
    display:flex;align-items:center;justify-content:space-between;
    background:var(--card-bg);border-radius:14px;padding:10px 18px;
    box-shadow:var(--shadow);margin-bottom:18px;
}
.avatar-circle{
    width:38px;height:38px;border-radius:50%;
    background:linear-gradient(135deg,#6a5cf0,#4f8ef7);
    color:#fff;display:flex;align-items:center;justify-content:center;
    font-weight:700;font-size:13px;flex-shrink:0;
}
.user-name{font-weight:700;font-size:13.5px;color:var(--text-dark);line-height:1.1;}
.user-role{font-size:11.5px;color:var(--text-muted);}
.bell-wrap{position:relative;font-size:19px;color:#4a4f66;margin-right:6px;}
.bell-badge{
    position:absolute;top:-4px;right:-6px;background:#e14b4b;color:#fff;
    font-size:9.5px;font-weight:700;border-radius:50%;
    width:15px;height:15px;display:flex;align-items:center;justify-content:center;
}

/* ---------- HERO BANNER ---------- */
.hero{
    border-radius:20px;padding:34px 38px;margin-bottom:20px;position:relative;overflow:hidden;
    background:
      radial-gradient(circle at 85% 15%, rgba(255,153,0,0.35), transparent 45%),
      linear-gradient(120deg,#3a2a6b 0%, #5b3f8f 30%, #8b5aa8 55%, #d98a6a 80%, #f0a868 100%);
    color:#fff;
}
.hero-badge{
    display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.16);
    border-radius:20px;padding:5px 13px;font-size:12px;font-weight:600;margin-bottom:14px;
}
.hero h1{font-size:32px;font-weight:800;margin:0 0 10px 0;line-height:1.2;max-width:560px;}
.hero p{font-size:14.5px;color:rgba(255,255,255,0.88);max-width:520px;margin-bottom:22px;}
.hero-cards{display:flex;gap:14px;flex-wrap:wrap;}
.hero-card{
    background:rgba(255,255,255,0.14);backdrop-filter:blur(6px);
    border:1px solid rgba(255,255,255,0.18);
    border-radius:13px;padding:11px 16px;min-width:165px;flex:1;
}
.hero-card .ic{font-size:17px;margin-bottom:5px;}
.hero-card .t{font-size:13px;font-weight:700;color:#fff;}
.hero-card .s{font-size:11px;color:rgba(255,255,255,0.75);}

/* ---------- STAT CARDS ---------- */
.stat-card{
    background:var(--card-bg);border-radius:var(--radius);padding:18px 20px;
    box-shadow:var(--shadow);height:100%;
}
.stat-top{display:flex;align-items:center;gap:10px;margin-bottom:12px;}
.stat-icon{
    width:34px;height:34px;border-radius:10px;display:flex;align-items:center;
    justify-content:center;font-size:16px;flex-shrink:0;
}
.stat-label{font-size:12.5px;color:var(--text-muted);font-weight:600;}
.stat-value{font-size:26px;font-weight:800;color:var(--text-dark);display:flex;align-items:center;gap:9px;}
.stat-delta{font-size:11.5px;font-weight:700;padding:2px 7px;border-radius:8px;}
.delta-up{background:var(--green-light);color:var(--green);}
.delta-down{background:var(--red-light);color:var(--red);}
.stat-sub{font-size:11.5px;color:var(--text-muted);margin-top:4px;}

/* ---------- GENERIC CARD ---------- */
.card{
    background:var(--card-bg);border-radius:var(--radius);padding:20px 22px;
    box-shadow:var(--shadow);height:100%;
}
.card-title{font-size:15px;font-weight:700;color:var(--text-dark);display:flex;align-items:center;gap:8px;margin-bottom:2px;}
.card-title .dot{width:26px;height:26px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:13px;}

/* ---------- INSIGHT ROWS ---------- */
.insight-row{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #f0f1f7;}
.insight-row:last-child{border-bottom:none;}
.insight-ic{
    width:30px;height:30px;border-radius:9px;display:flex;align-items:center;
    justify-content:center;font-size:14px;flex-shrink:0;
}
.insight-title{font-size:13.5px;font-weight:700;color:var(--text-dark);}
.insight-sub{font-size:11.5px;color:var(--text-muted);}

/* ---------- LEGEND ROW (donut) ---------- */
.legend-row{display:flex;align-items:center;justify-content:space-between;font-size:12.5px;padding:5px 0;}
.legend-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;}

/* ---------- TABLE ---------- */
.dtable{width:100%;border-collapse:collapse;font-size:12.8px;}
.dtable th{
    text-align:left;color:var(--text-muted);font-weight:600;font-size:11.5px;
    padding:8px 10px;border-bottom:1px solid #eef0f6;text-transform:uppercase;letter-spacing:0.3px;
}
.dtable td{padding:11px 10px;border-bottom:1px solid #f5f6fa;color:var(--text-dark);vertical-align:middle;}
.emp-cell{display:flex;align-items:center;gap:9px;}
.emp-avatar{
    width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#6a5cf0,#4f8ef7);
    color:#fff;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;
}
.badge{font-size:11px;font-weight:700;padding:3px 9px;border-radius:8px;white-space:nowrap;}
.badge-high{background:var(--red-light);color:var(--red);}
.badge-medium{background:var(--amber-light);color:var(--amber);}
.badge-low{background:var(--green-light);color:var(--green);}
.badge-pattern1{background:var(--blue-light);color:var(--blue);}
.badge-pattern2{background:var(--purple-light);color:var(--purple);}

/* ---------- AI ASSISTANT PANEL ---------- */
.ai-panel{
    background:linear-gradient(160deg,#6a5cf0 0%, #4f6bf0 100%);
    border-radius:var(--radius);padding:18px 18px 16px 18px;color:#fff;
    box-shadow:var(--shadow);
}
.ai-head{display:flex;align-items:center;gap:9px;margin-bottom:12px;}
.ai-head .ic{width:34px;height:34px;background:rgba(255,255,255,0.18);border-radius:10px;
    display:flex;align-items:center;justify-content:center;font-size:17px;}
.ai-head .t{font-weight:700;font-size:14px;}
.ai-head .s{font-size:11px;color:rgba(255,255,255,0.8);}
.ai-bubble{
    background:rgba(255,255,255,0.14);border-radius:13px;padding:13px 14px;
    font-size:12.8px;line-height:1.5;margin-bottom:12px;color:#fff;
}
.ai-btn{
    background:#fff;color:#4f4ff0;font-weight:700;font-size:12.5px;
    padding:9px 0;border-radius:10px;text-align:center;
}

/* ---------- QUICK ACTION LIST ---------- */
.qa-item{
    background:var(--card-bg);border-radius:13px;padding:12px 14px;margin-bottom:10px;
    display:flex;align-items:center;gap:11px;box-shadow:var(--shadow);
}
.qa-ic{width:32px;height:32px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:15px;flex-shrink:0;}
.qa-t{font-size:13px;font-weight:700;color:var(--text-dark);}
.qa-s{font-size:11px;color:var(--text-muted);}
.qa-chev{margin-left:auto;color:#c4c8d8;font-size:15px;}

/* ---------- COACHING FEED ---------- */
.cf-item{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #f0f1f7;}
.cf-item:last-child{border-bottom:none;}
.cf-name{font-size:12.8px;font-weight:700;color:var(--text-dark);}
.cf-sub{font-size:11px;color:var(--text-muted);}

.quote-banner{
    background:linear-gradient(90deg,#14b8a6,#4f8ef7);border-radius:14px;
    padding:12px 16px;color:#fff;font-size:12.5px;font-weight:600;
    display:flex;justify-content:space-between;align-items:center;margin-top:14px;
}

.empty-state{
    text-align:center;color:var(--text-muted);font-size:12.5px;padding:26px 10px;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def initials(name: str) -> str:
    parts = str(name).split()
    return "".join(p[0].upper() for p in parts[:2]) if parts else "?"


def pct_change(curr: int, prev: int):
    if prev == 0:
        return None
    return round((curr - prev) / prev * 100, 1)


def risk_level(event_count: int) -> str:
    if event_count >= 5:
        return "High"
    if event_count >= 3:
        return "Medium"
    return "Low"


REQUIRED_LEAVE_COLS = {"EmployeeID", "EmployeeName", "Department", "LeaveDate", "DurationDays"}


@st.cache_data(show_spinner=False)
def load_workbook(file_bytes: bytes):
    sheets = pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)

    leaves = None
    employees = None
    coaching = None

    # find LeaveEvents-like sheet
    for name, sdf in sheets.items():
        if REQUIRED_LEAVE_COLS.issubset(set(sdf.columns)):
            leaves = sdf.copy()
            break
    if leaves is None:
        # fall back to first sheet if it has the columns under different case
        first = list(sheets.values())[0]
        leaves = first.copy()

    # find Employees roster sheet, else derive from leave events
    for name, sdf in sheets.items():
        cols = set(sdf.columns)
        if {"EmployeeID", "EmployeeName", "Department"}.issubset(cols) and "LeaveDate" not in cols:
            employees = sdf.copy()
            break
    if employees is None and leaves is not None:
        employees = leaves[["EmployeeID", "EmployeeName", "Department"]].drop_duplicates().reset_index(drop=True)

    # optional coaching sheet
    for name, sdf in sheets.items():
        cols = {c.lower() for c in sdf.columns}
        if "coaching" in name.lower() or {"employeename", "status"}.issubset(cols):
            coaching = sdf.copy()
            break

    if leaves is not None and "LeaveDate" in leaves.columns:
        leaves["LeaveDate"] = pd.to_datetime(leaves["LeaveDate"], errors="coerce")
        leaves = leaves.dropna(subset=["LeaveDate"])

    return employees, leaves, coaching


# ----------------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-row">
                <span class="brand-amazon">amazon</span>
            </div>
            <div class="brand-sub">People Analytics</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_options = [
        "🏠  Home",
        "📈  Attendance Insights",
        "➕  Sick Leave Tracker",
        "👤  Employee Profiles",
        "🤝  Coaching & Guidance",
        "📊  Reports & Analytics",
        "👥  Team Overview",
        "⚙️  Settings",
    ]
    st.radio("nav", nav_options, label_visibility="collapsed", key="nav")

    st.markdown(
        """
        <div class="promo-box">
            <h4>Healthy Teams Build a Stronger Tomorrow</h4>
            <p>Better insights. Better conversations. A healthier workplace.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("**Data source**")
    uploaded_file = st.file_uploader("Upload Excel workbook (.xlsx)", type=["xlsx"])

    with st.expander("Expected Excel format"):
        st.markdown(
            """
**Sheet `LeaveEvents`** (one row per sick-leave event) — required columns:
- `EmployeeID`
- `EmployeeName`
- `Department`
- `LeaveDate` (date)
- `DurationDays` (1 or 2)

**Sheet `Employees`** *(optional — derived from LeaveEvents if missing)*:
- `EmployeeID`, `EmployeeName`, `Department`

**Sheet `Coaching`** *(optional, powers the Recent Coaching Activity feed)*:
- `EmployeeName`, `PatternType` (e.g. `1-Day Pattern`), `Status`, `Date`
            """
        )

    def build_template() -> bytes:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            pd.DataFrame(
                {
                    "EmployeeID": ["E001", "E001", "E002"],
                    "EmployeeName": ["Emma Wilson", "Emma Wilson", "James Carter"],
                    "Department": ["Operations", "Operations", "Logistics"],
                    "LeaveDate": ["2025-04-10", "2025-05-12", "2025-05-02"],
                    "DurationDays": [1, 1, 2],
                }
            ).to_excel(writer, sheet_name="LeaveEvents", index=False)
            pd.DataFrame(
                {
                    "EmployeeID": ["E001", "E002"],
                    "EmployeeName": ["Emma Wilson", "James Carter"],
                    "Department": ["Operations", "Logistics"],
                }
            ).to_excel(writer, sheet_name="Employees", index=False)
            pd.DataFrame(
                {
                    "EmployeeName": ["Emma Wilson"],
                    "PatternType": ["1-Day Pattern"],
                    "Status": ["Completed"],
                    "Date": ["2025-06-10"],
                }
            ).to_excel(writer, sheet_name="Coaching", index=False)
        return buf.getvalue()

    st.download_button(
        "⬇ Download Excel template",
        data=build_template(),
        file_name="people_analytics_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

# ----------------------------------------------------------------------------
# TOP BAR
# ----------------------------------------------------------------------------
top_l, top_r = st.columns([3, 1])
with top_l:
    st.text_input("search", placeholder="🔎  Search by employee, department, or team...", label_visibility="collapsed")
with top_r:
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:flex-end;gap:16px;height:38px;">
            <div class="bell-wrap">🔔<span class="bell-badge">•</span></div>
            <div class="avatar-circle">SJ</div>
            <div>
                <div class="user-name">Sarah Johnson</div>
                <div class="user-role">HR Manager</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ----------------------------------------------------------------------------
# NO DATA YET → STOP HERE WITH A CLEAN EMPTY STATE
# ----------------------------------------------------------------------------
if uploaded_file is None:
    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">✨ AI Powered</div>
            <h1>Turn Attendance Patterns into Positive Conversations</h1>
            <p>We help you spot recurring sick leave patterns, understand the bigger picture,
            and coach your team with confidence.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(
        "📂 Upload your Excel workbook in the sidebar to populate this dashboard. "
        "No sample or placeholder numbers are shown — everything here is computed "
        "directly from your data. Use **Download Excel template** in the sidebar to "
        "get the expected format."
    )
    st.stop()

employees_df, leaves_df, coaching_df = load_workbook(uploaded_file.getvalue())

missing = REQUIRED_LEAVE_COLS - set(leaves_df.columns)
if missing:
    st.error(f"Your Excel file is missing required column(s): {', '.join(sorted(missing))}. "
             f"See 'Expected Excel format' in the sidebar.")
    st.stop()

# ----------------------------------------------------------------------------
# METRIC COMPUTATION (100% from uploaded data)
# ----------------------------------------------------------------------------
total_employees = employees_df["EmployeeID"].nunique()

leaves_df["MonthPeriod"] = leaves_df["LeaveDate"].dt.to_period("M")
latest_month = leaves_df["MonthPeriod"].max()
prev_month = latest_month - 1

this_month_df = leaves_df[leaves_df["MonthPeriod"] == latest_month]
prev_month_df = leaves_df[leaves_df["MonthPeriod"] == prev_month]

sick_leave_this_month = len(this_month_df)
sick_leave_prev_month = len(prev_month_df)
sick_leave_delta = pct_change(sick_leave_this_month, sick_leave_prev_month)

one_day_this = int((this_month_df["DurationDays"] == 1).sum())
two_day_this = int((this_month_df["DurationDays"] >= 2).sum())
one_day_prev = int((prev_month_df["DurationDays"] == 1).sum())
two_day_prev = int((prev_month_df["DurationDays"] >= 2).sum())
one_day_delta = pct_change(one_day_this, one_day_prev)
two_day_delta = pct_change(two_day_this, two_day_prev)

# last 6 months trend
last6 = pd.period_range(end=latest_month, periods=6, freq="M")
trend = leaves_df[leaves_df["MonthPeriod"].isin(last6)]
trend_grouped = (
    trend.groupby(["MonthPeriod"])
    .apply(lambda g: pd.Series({
        "OneDay": int((g["DurationDays"] == 1).sum()),
        "TwoDay": int((g["DurationDays"] >= 2).sum()),
    }))
    .reindex(last6, fill_value=0)
)
month_labels = [p.strftime("%b") for p in last6]

# key insights (computed, not fabricated)
first_m_1day = trend_grouped["OneDay"].iloc[0] if len(trend_grouped) else 0
last_m_1day = trend_grouped["OneDay"].iloc[-1] if len(trend_grouped) else 0
one_day_trend_pct = pct_change(last_m_1day, first_m_1day)

trend["Weekday"] = trend["LeaveDate"].dt.day_name()
weekday_counts = trend["Weekday"].value_counts()
mon_fri_count = weekday_counts.get("Monday", 0) + weekday_counts.get("Friday", 0)
other_days_avg = (
    (weekday_counts.drop(index=["Monday", "Friday"], errors="ignore").sum() / 5)
    if len(weekday_counts) else 0
)
mon_fri_ratio = round(mon_fri_count / other_days_avg, 1) if other_days_avg else None

pct_1day_mon_fri = (
    round(100 * trend[(trend["DurationDays"] == 1) & (trend["Weekday"].isin(["Monday", "Friday"]))].shape[0]
          / max(len(trend[trend["DurationDays"] == 1]), 1), 1)
)

is_increasing = last_m_1day > first_m_1day

# repeated sick leave (grouped by employee, over the 6-month trend window)
by_emp = (
    trend.groupby(["EmployeeID", "EmployeeName", "Department"])
    .agg(
        TotalEvents=("LeaveDate", "count"),
        OneDayEvents=("DurationDays", lambda s: int((s == 1).sum())),
        TwoDayEvents=("DurationDays", lambda s: int((s >= 2).sum())),
        LastEvent=("LeaveDate", "max"),
    )
    .reset_index()
)
by_emp = by_emp[by_emp["TotalEvents"] >= 2].sort_values("TotalEvents", ascending=False)
by_emp["Risk"] = by_emp["TotalEvents"].apply(risk_level)

at_risk_count = int((by_emp["Risk"].isin(["High", "Medium"])).sum())

# ----------------------------------------------------------------------------
# HERO
# ----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-badge">✨ AI Powered</div>
        <h1>Turn Attendance Patterns into Positive Conversations</h1>
        <p>We help you spot recurring sick leave patterns, understand the bigger picture,
        and coach your team with confidence.</p>
        <div class="hero-cards">
            <div class="hero-card"><div class="ic">🔍</div><div class="t">Detect Patterns</div><div class="s">Spot 1-day &amp; 2-day trends</div></div>
            <div class="hero-card"><div class="ic">💡</div><div class="t">Get AI Insights</div><div class="s">Understand the why</div></div>
            <div class="hero-card"><div class="ic">🤝</div><div class="t">Coach with Confidence</div><div class="s">Get suggested conversations</div></div>
            <div class="hero-card"><div class="ic">🌱</div><div class="t">Build Healthier Teams</div><div class="s">Support &amp; retain talent</div></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# LAYOUT: MAIN (left) + AI RAIL (right)
# ----------------------------------------------------------------------------
main_col, rail_col = st.columns([2.6, 1], gap="medium")

with main_col:
    # ---- STAT CARDS ----
    def delta_html(val):
        if val is None:
            return ""
        cls = "delta-up" if val >= 0 else "delta-down"
        arrow = "↑" if val >= 0 else "↓"
        return f'<span class="stat-delta {cls}">{arrow} {abs(val)}%</span>'

    s1, s2, s3, s4 = st.columns(4)
    stat_defs = [
        (s1, "👤", "var(--purple-light)", "Total Employees", f"{total_employees:,}", None, "as of latest upload"),
        (s2, "🩺", "var(--pink-light)", "Sick Leave (This Month)", f"{sick_leave_this_month:,}", sick_leave_delta, "vs last month"),
        (s3, "📅", "var(--blue-light)", "1-Day Sick Leave Events", f"{one_day_this:,}", one_day_delta, "vs last month"),
        (s4, "🗓️", "var(--teal-light)", "2-Day Sick Leave Events", f"{two_day_this:,}", two_day_delta, "vs last month"),
    ]
    for col, icon, bg, label, value, delta, sub in stat_defs:
        with col:
            st.markdown(
                f"""
                <div class="stat-card">
                    <div class="stat-top">
                        <div class="stat-icon" style="background:{bg};">{icon}</div>
                        <div class="stat-label">{label}</div>
                    </div>
                    <div class="stat-value">{value} {delta_html(delta)}</div>
                    <div class="stat-sub">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")

    # ---- CHART ROW ----
    c1, c2, c3 = st.columns([1.5, 1, 1], gap="medium")

    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-title"><span class="dot" style="background:var(--purple-light);">📈</span>'
            'Sick Leave Pattern Analysis</div>',
            unsafe_allow_html=True,
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=month_labels, y=trend_grouped["OneDay"].tolist(), name="1-Day Leave",
            mode="lines+markers", line=dict(color="#4f8ef7", width=3),
            marker=dict(size=6), fill="tozeroy", fillcolor="rgba(79,142,247,0.08)",
        ))
        fig.add_trace(go.Scatter(
            x=month_labels, y=trend_grouped["TwoDay"].tolist(), name="2-Day Leave",
            mode="lines+markers", line=dict(color="#6a5cf0", width=3),
            marker=dict(size=6), fill="tozeroy", fillcolor="rgba(106,92,240,0.08)",
        ))
        fig.update_layout(
            height=270, margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, font=dict(size=11)),
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#f0f1f7"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-title"><span class="dot" style="background:var(--green-light);">🔑</span>Key Insights</div><br>',
            unsafe_allow_html=True,
        )
        insight_html = ""
        if one_day_trend_pct is not None:
            arrow = "+" if one_day_trend_pct >= 0 else ""
            insight_html += f"""
            <div class="insight-row">
                <div class="insight-ic" style="background:var(--green-light);">📈</div>
                <div><div class="insight-title">{arrow}{one_day_trend_pct}%</div>
                <div class="insight-sub">Change in 1-day sick leave events (last 6 months)</div></div>
            </div>"""
        if mon_fri_ratio is not None:
            insight_html += f"""
            <div class="insight-row">
                <div class="insight-ic" style="background:var(--blue-light);">📆</div>
                <div><div class="insight-title">{mon_fri_ratio}x higher</div>
                <div class="insight-sub">Sick leave on Mondays and Fridays vs. other weekdays</div></div>
            </div>"""
        insight_html += f"""
        <div class="insight-row">
            <div class="insight-ic" style="background:var(--purple-light);">📊</div>
            <div><div class="insight-title">{pct_1day_mon_fri}%</div>
            <div class="insight-sub">Of 1-day leaves fall on a Monday or Friday</div></div>
        </div>
        <div class="insight-row">
            <div class="insight-ic" style="background:var(--amber-light);">📉</div>
            <div><div class="insight-title">Trend</div>
            <div class="insight-sub">{"Increasing" if is_increasing else "Decreasing / stable"} pattern over the last 6 months</div></div>
        </div>
        """
        st.markdown(insight_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="card-title"><span class="dot" style="background:var(--blue-light);">🍩</span>Leave Duration Breakdown</div>',
            unsafe_allow_html=True,
        )
        total_split = max(one_day_this + two_day_this, 1)
        fig2 = go.Figure(data=[go.Pie(
            labels=["1 Day", "2 Days"], values=[one_day_this, two_day_this], hole=0.72,
            marker=dict(colors=["#4f8ef7", "#6a5cf0"]), textinfo="none", sort=False,
        )])
        fig2.update_layout(
            height=190, margin=dict(l=0, r=0, t=10, b=0), showlegend=False,
            annotations=[dict(text=f"<b>{sick_leave_this_month}</b><br><span style='font-size:11px;color:#8a8fa3'>Total Sick Leave</span>",
                               x=0.5, y=0.5, font_size=18, showarrow=False)],
            paper_bgcolor="white",
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"""
            <div class="legend-row"><span><span class="legend-dot" style="background:#4f8ef7;"></span>1 Day</span>
                <b>{one_day_this} ({round(100*one_day_this/total_split)}%)</b></div>
            <div class="legend-row"><span><span class="legend-dot" style="background:#6a5cf0;"></span>2 Days</span>
                <b>{two_day_this} ({round(100*two_day_this/total_split)}%)</b></div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")

    # ---- REPEATED SICK LEAVE TABLE ----
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-title"><span class="dot" style="background:var(--purple-light);">👥</span>Employees with Repeated Sick Leave</div><br>',
        unsafe_allow_html=True,
    )
    if by_emp.empty:
        st.markdown('<div class="empty-state">No employees with repeated sick leave in the current data.</div>', unsafe_allow_html=True)
    else:
        rows_html = ""
        for _, r in by_emp.head(8).iterrows():
            pattern = []
            if r["OneDayEvents"]:
                pattern.append(f'{r["OneDayEvents"]} × 1 day')
            if r["TwoDayEvents"]:
                pattern.append(f'{r["TwoDayEvents"]} × 2 days')
            pattern_str = " + ".join(pattern)
            risk_cls = {"High": "badge-high", "Medium": "badge-medium", "Low": "badge-low"}[r["Risk"]]
            rows_html += f"""
            <tr>
                <td><div class="emp-cell"><div class="emp-avatar">{initials(r['EmployeeName'])}</div>{r['EmployeeName']}</div></td>
                <td>{r['Department']}</td>
                <td>{pattern_str}</td>
                <td>{r['TotalEvents']}</td>
                <td>{r['LastEvent'].strftime('%b %d, %Y')}</td>
                <td><span class="badge {risk_cls}">{r['Risk']}</span></td>
            </tr>"""
        st.markdown(
            f"""
            <table class="dtable">
                <tr><th>Employee</th><th>Department</th><th>Pattern</th><th>Total Events</th><th>Last Event</th><th>Risk Level</th></tr>
                {rows_html}
            </table>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# RIGHT RAIL
# ----------------------------------------------------------------------------
with rail_col:
    st.markdown(
        f"""
        <div class="ai-panel">
            <div class="ai-head">
                <div class="ic">🤖</div>
                <div><div class="t">AI Assistant</div><div class="s">Always here to help</div></div>
            </div>
            <div class="ai-bubble">
                Hi Sarah! 👋 I've found <b>{at_risk_count}</b> employee{"s" if at_risk_count != 1 else ""} with
                recurring 1-day and 2-day sick leave patterns based on your uploaded data.
                <br><br>Would you like to see the details and suggested coaching conversations?
            </div>
            <div class="ai-btn">View Insights →</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    top3 = by_emp.head(3)["EmployeeName"].tolist()
    top3_str = ", ".join(top3) if top3 else "No at-risk employees yet"
    st.markdown(
        f"""
        <div class="qa-item">
            <div class="qa-ic" style="background:var(--pink-light);">⚠️</div>
            <div><div class="qa-t">Top 3 At-Risk Employees</div><div class="qa-s">{top3_str}</div></div>
            <div class="qa-chev">›</div>
        </div>
        <div class="qa-item">
            <div class="qa-ic" style="background:var(--purple-light);">💬</div>
            <div><div class="qa-t">Generate Coaching Conversation</div><div class="qa-s">For selected employee</div></div>
            <div class="qa-chev">›</div>
        </div>
        <div class="qa-item">
            <div class="qa-ic" style="background:var(--teal-light);">📊</div>
            <div><div class="qa-t">View Team Trend</div><div class="qa-s">Sick leave patterns by department</div></div>
            <div class="qa-chev">›</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="card-title"><span class="dot" style="background:var(--green-light);">💬</span>Recent Coaching Activity</div><br>',
        unsafe_allow_html=True,
    )
    if coaching_df is None or coaching_df.empty:
        st.markdown(
            '<div class="empty-state">No coaching activity recorded yet.<br>Add a <b>Coaching</b> sheet to your '
            'Excel file to populate this feed.</div>',
            unsafe_allow_html=True,
        )
    else:
        rows = ""
        for _, r in coaching_df.head(5).iterrows():
            pat = str(r.get("PatternType", ""))
            badge_cls = "badge-pattern1" if "1" in pat else "badge-pattern2"
            date_str = r.get("Date", "")
            try:
                date_str = pd.to_datetime(date_str).strftime("%b %d, %Y")
            except Exception:
                pass
            rows += f"""
            <div class="cf-item">
                <div class="emp-avatar">{initials(r.get('EmployeeName',''))}</div>
                <div style="flex:1;">
                    <div class="cf-name">{r.get('EmployeeName','')} <span class="badge {badge_cls}">{pat}</span></div>
                    <div class="cf-sub">{r.get('Status','')} · {date_str}</div>
                </div>
            </div>"""
        st.markdown(rows, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="quote-banner">
            <span>"The best leaders don't just lead — they support people."</span>
            <span>♥</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

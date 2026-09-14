import datetime
import json
import os
import pytz
import streamlit as st
import pandas as pd

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="AUH1 Daily Updates Tracker",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------
# Custom Styling (Dark UI matching image)
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Main container background */
    .stApp {
        background: linear-gradient(180deg, #13172e 0%, #1a1e3b 50%, #202447 100%);
        color: #f1f3f9;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Header card styles */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 16px 20px;
        backdrop-filter: blur(8px);
    }
    
    .card-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #9aa3c2;
        margin-bottom: 12px;
        font-weight: 600;
    }
    
    .stat-row {
        display: flex;
        justify-content: space-between;
        text-align: center;
        gap: 8px;
    }
    
    .stat-box {
        flex: 1;
    }
    
    .stat-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .stat-label {
        font-size: 0.65rem;
        color: #8c97b8;
        font-weight: 600;
        margin-top: 2px;
        letter-spacing: 0.05em;
    }
    
    /* Center Date Header */
    .header-center {
        text-align: center;
    }
    
    .app-subtitle {
        font-size: 0.85rem;
        color: #9aa3c2;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    .current-date-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ffffff;
        margin: 2px 0 0 0;
    }
    
    .current-year {
        font-size: 0.9rem;
        color: #7b86ad;
        margin-bottom: 8px;
    }
    
    /* Custom Table Styling */
    .tracker-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 24px;
        border-radius: 12px;
        overflow: hidden;
        background: #eef1fc;
        color: #2b3149;
    }
    
    .tracker-table th {
        background-color: #dce3f8;
        padding: 14px 16px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #4b587a;
        text-align: center;
    }
    
    .tracker-table th:first-child, .tracker-table th:last-child {
        text-align: left;
    }
    
    .tracker-table td {
        padding: 14px 16px;
        font-size: 0.82rem;
        border-bottom: 1px solid #e2e7f6;
        text-align: center;
        color: #3b4256;
    }
    
    .tracker-table td:first-child {
        text-align: left;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .tracker-table td:last-child {
        text-align: left;
        font-size: 0.78rem;
        color: #515b74;
    }
    
    .avatar-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background-color: #5865f2;
        color: #ffffff;
        font-size: 0.75rem;
        font-weight: 700;
    }
    
    .counter-pill {
        display: inline-block;
        min-width: 22px;
        padding: 2px 6px;
        border-radius: 12px;
        background-color: #dee4f7;
        font-weight: 700;
        color: #384260;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Timezone & Session State Management
# ---------------------------------------------------------
AUH_TZ = pytz.timezone("Asia/Dubai") # UAE GMT+4
today_in_auh = datetime.datetime.now(AUH_TZ).date()

if "selected_date" not in st.session_state:
    st.session_state.selected_date = today_in_auh

def go_prev():
    st.session_state.selected_date -= datetime.timedelta(days=1)

def go_next():
    st.session_state.selected_date += datetime.timedelta(days=1)

def go_today():
    st.session_state.selected_date = today_in_auh

# ---------------------------------------------------------
# Dummy / Persistent Data Layer
# ---------------------------------------------------------
TEAM_MEMBERS = [
    {"name": "Allyza Ashley Saludo Dimafelix", "avatar": "AD"},
    {"name": "Amna Jamil", "avatar": "AJ"},
    {"name": "Anu Damodaran", "avatar": "AD"},
    {"name": "Anupriya Kalaiselvan", "avatar": "AK"},
    {"name": "Arathi Karichery", "avatar": "AK"},
]

def load_data_for_date(target_date):
    """
    Load data from DB/file or generate default values.
    """
    # Example sample entry for demonstration matching the screenshot
    if target_date == st.session_state.selected_date:
        return [
            {
                "name": "Allyza Ashley Saludo Dimafelix",
                "avatar": "AD",
                "updates": 1,
                "hr_gemba": 0,
                "myhr": 2,
                "engagement": 0,
                "wbc": 0,
                "tayseer": 0,
                "activities": "SOS briefing, Shared Absence bridge, Wellness check for SL AA, Assist AA in MyHR, Sick leave approval, Assisted for back to school packing"
            },
            {"name": "Amna Jamil", "avatar": "AJ", "updates": 0, "hr_gemba": 0, "myhr": 0, "engagement": 0, "wbc": 0, "tayseer": 0, "activities": "-"},
            {"name": "Anu Damodaran", "avatar": "AD", "updates": 0, "hr_gemba": 0, "myhr": 0, "engagement": 0, "wbc": 0, "tayseer": 0, "activities": "-"},
            {"name": "Anupriya Kalaiselvan", "avatar": "AK", "updates": 0, "hr_gemba": 0, "myhr": 0, "engagement": 0, "wbc": 0, "tayseer": 0, "activities": "-"},
            {"name": "Arathi Karichery", "avatar": "AK", "updates": 0, "hr_gemba": 0, "myhr": 0, "engagement": 0, "wbc": 0, "tayseer": 0, "activities": "-"},
        ]
    return []

# ---------------------------------------------------------
# Calculate Sun - Sat Weekly Range
# ---------------------------------------------------------
cur_date = st.session_state.selected_date
# In Python weekday(): Monday is 0, Sunday is 6
days_since_sunday = (cur_date.weekday() + 1) % 7
start_of_week = cur_date - datetime.timedelta(days=days_since_sunday)
end_of_week = start_of_week + datetime.timedelta(days=6)

daily_records = load_data_for_date(cur_date)

# Calculate Daily totals
daily_updates = sum(r["updates"] for r in daily_records)
daily_gemba = sum(r["hr_gemba"] for r in daily_records)
daily_myhr = sum(r["myhr"] for r in daily_records)
daily_wbc = sum(r["wbc"] for r in daily_records)
daily_tayseer = sum(r["tayseer"] for r in daily_records)

# ---------------------------------------------------------
# Layout Top Section (3 Columns)
# ---------------------------------------------------------
col_left, col_center, col_right = st.columns([1.2, 1.6, 1.2])

with col_left:
    st.markdown(f"""
    <div class="metric-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div class="card-title">WEEKLY TOTALS (SUN – SAT)</div>
            <div style="font-size:0.65rem; color:#8c97b8;">{start_of_week.strftime('%b %d')} – {end_of_week.strftime('%b %d, %Y')}</div>
        </div>
        <div class="stat-row">
            <div class="stat-box"><div class="stat-val">11</div><div class="stat-label">MEMBERS</div></div>
            <div class="stat-box"><div class="stat-val">19</div><div class="stat-label">UPDATES</div></div>
            <div class="stat-box"><div class="stat-val">22</div><div class="stat-label">GEMBA</div></div>
            <div class="stat-box"><div class="stat-val">25</div><div class="stat-label">MYHR</div></div>
            <div class="stat-box"><div class="stat-val">2</div><div class="stat-label">DAYS</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_center:
    st.markdown("""
    <div class="header-center">
        <div style="font-size: 1.2rem; font-weight: 700; display:flex; align-items:center; justify-content:center; gap:8px;">
            <span>📦</span> AUH1 Daily Updates
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Date navigation controls
    nav_c1, nav_c2, nav_c3 = st.columns([1, 2, 1])
    with nav_c1:
        st.button("◀ Prev Day", on_click=go_prev, use_container_width=True)
    with nav_c2:
        st.markdown(f"""
        <div class="header-center">
            <div class="app-subtitle">{cur_date.strftime('%A')}</div>
            <div class="current-date-title">{cur_date.strftime('%b %d')}</div>
            <div class="current-year">{cur_date.year}</div>
        </div>
        """, unsafe_allow_html=True)
    with nav_c3:
        st.button("Next Day ▶", on_click=go_next, use_container_width=True)
        
    btn_c1, btn_c2, btn_c3 = st.columns([1, 1, 1])
    with btn_c2:
        st.button("✨ TODAY", on_click=go_today, use_container_width=True)

with col_right:
    weekday_title = cur_date.strftime('%A, %b %d TOTALS').upper()
    st.markdown(f"""
    <div class="metric-card">
        <div class="card-title">{weekday_title}</div>
        <div class="stat-row">
            <div class="stat-box"><div class="stat-val">{daily_updates}</div><div class="stat-label">UPDATES</div></div>
            <div class="stat-box"><div class="stat-val">{daily_gemba}</div><div class="stat-label">GEMBA</div></div>
            <div class="stat-box"><div class="stat-val">{daily_myhr}</div><div class="stat-label">MYHR</div></div>
            <div class="stat-box"><div class="stat-val">112</div><div class="stat-label">WBC</div></div>
            <div class="stat-box"><div class="stat-val">{daily_tayseer}</div><div class="stat-label">TAYSEER</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Subheaders & Report Buttons
# ---------------------------------------------------------
now_str = datetime.datetime.now(AUH_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")
formatted_tz = f"{now_str[:-2]}:{now_str[-2:]}"

st.markdown(f"""
<div style="text-align:center; font-size: 0.75rem; color: #727e9f; margin-top: 15px;">
    Last updated: {formatted_tz}
</div>
""", unsafe_allow_html=True)

rep_col1, rep_col2, rep_col3, rep_col4 = st.columns([2, 1, 1, 2])
with rep_col2:
    st.button("📊 Daily Report", use_container_width=True)
with rep_col3:
    st.button("📈 Weekly Report", use_container_width=True)

# ---------------------------------------------------------
# Team Member Table View
# ---------------------------------------------------------
rows_html = ""
for member in daily_records:
    rows_html += f"""
    <tr>
        <td>
            <span class="avatar-badge">{member['avatar']}</span>
            <span>{member['name']}</span>
        </td>
        <td><span class="counter-pill">{member['updates']}</span></td>
        <td>{member['hr_gemba']}</td>
        <td><span class="counter-pill">{member['myhr']}</span></td>
        <td>{member['engagement']}</td>
        <td>{member['wbc']}</td>
        <td>{member['tayseer']}</td>
        <td>{member['activities']}</td>
    </tr>
    """

table_html = f"""
<table class="tracker-table">
    <thead>
        <tr>
            <th>TEAM MEMBER</th>
            <th>UPDATES</th>
            <th>HR GEMBA</th>
            <th>MYHR</th>
            <th>ENGAGEMENT</th>
            <th>WBC</th>
            <th>TAYSEER</th>
            <th>ACTIVITIES</th>
        </tr>
    </thead>
    <tbody>
        {rows_html}
    </tbody>
</table>
"""

st.markdown(table_html, unsafe_allow_html=True)

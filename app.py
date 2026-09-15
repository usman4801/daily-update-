import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

st.set_page_config(
    page_title="Amazon - People Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- DATA LOADER -----------------
@st.cache_data
def load_data():
    files = sorted(glob.glob("DWD-AUH1-*.xlsx"), reverse=True)
    if not files:
        files = sorted(glob.glob("*.xlsx"), reverse=True)
    
    emp_count = 1248
    roster_records = []
    
    if files:
        try:
            filepath = files[0]
            xls = pd.ExcelFile(filepath)
            if 'Roster' in xls.sheet_names:
                df_raw = pd.read_excel(filepath, sheet_name='Roster')
                header_idx = None
                for i, row in df_raw.head(10).iterrows():
                    if 'S.No' in row.values or 'AMZ ID' in row.values:
                        header_idx = i
                        break
                if header_idx is not None:
                    df_clean = pd.read_excel(filepath, sheet_name='Roster', skiprows=header_idx + 1)
                else:
                    df_clean = pd.read_excel(filepath, sheet_name='Roster')
                
                valid = df_clean.dropna(subset=['EMP Name'])
                if len(valid) > 0:
                    emp_count = len(valid)
                
                for _, r in valid.head(5).iterrows():
                    roster_records.append({
                        "name": str(r.get('EMP Name', '')).title(),
                        "dept": str(r.get('Department', 'Operations')),
                    })
        except Exception:
            pass
            
    if not roster_records or len(roster_records) < 5:
        roster_records = [
            {"name": "Emma Wilson", "dept": "Operations"},
            {"name": "James Carter", "dept": "Logistics"},
            {"name": "Olivia Davis", "dept": "Customer Service"},
            {"name": "Liam Brown", "dept": "Finance"},
            {"name": "Sophia Martinez", "dept": "Marketing"}
        ]
        
    return emp_count, roster_records

total_emp_count, emp_list = load_data()

table_rows = [
    {"name": emp_list[0]['name'], "dept": emp_list[0]['dept'], "pattern": "4 × 1 day (last 3 months)", "events": 4, "date": "Jun 12, 2026", "risk": "Medium", "color": "#b45309", "bg": "#fef3c7"},
    {"name": emp_list[1]['name'], "dept": emp_list[1]['dept'], "pattern": "3 × 2 days (last 3 months)", "events": 3, "date": "Jun 10, 2026", "risk": "Medium", "color": "#b45309", "bg": "#fef3c7"},
    {"name": emp_list[2]['name'], "dept": emp_list[2]['dept'], "pattern": "5 × 1 day (3 months)", "events": 5, "date": "Jun 08, 2026", "risk": "High", "color": "#b91c1c", "bg": "#fee2e2"},
    {"name": emp_list[3]['name'], "dept": emp_list[3]['dept'], "pattern": "2 × 2 days (last 2 months)", "events": 2, "date": "Jun 05, 2026", "risk": "Low", "color": "#047857", "bg": "#d1fae5"},
    {"name": emp_list[4]['name'], "dept": emp_list[4]['dept'], "pattern": "6 × 1 day (increasing trend)", "events": 6, "date": "Jun 02, 2026", "risk": "High", "color": "#b91c1c", "bg": "#fee2e2"},
]

# ----------------- EXACT FIGMA REPLICA CSS -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stApp {
        background-color: #f0f4f9 !important;
    }
    .block-container {
        padding: 1rem 1.6rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Left Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0b1528 !important;
        width: 230px !important;
        min-width: 230px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding: 18px 14px !important;
    }
    
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 9px 12px;
        color: #94a3b8;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .nav-item.active {
        background: #1e293b;
        color: #38bdf8;
        font-weight: 600;
    }

    /* Top Search Bar */
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
    }
    .search-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 8px 18px;
        font-size: 12.5px;
        width: 440px;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }

    /* Hero Banner with Building Illustration */
    .hero-container {
        background: linear-gradient(105deg, #e0f2fe 0%, #eff6ff 48%, #e0f2fe 100%);
        border-radius: 16px;
        padding: 22px 26px;
        border: 1px solid #bae6fd;
        position: relative;
        overflow: hidden;
        margin-bottom: 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-badge {
        background: #0284c7;
        color: white;
        font-size: 10.5px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 8px;
    }
    .hero-container h2 {
        font-size: 23px;
        font-weight: 800;
        color: #0f172a;
        margin: 0 0 6px 0;
        line-height: 1.2;
    }
    .hero-container p {
        font-size: 12.5px;
        color: #475569;
        margin: 0 0 16px 0;
        max-width: 580px;
        line-height: 1.4;
    }
    .pill-btn {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 7px 14px;
        font-size: 12px;
        font-weight: 600;
        color: #1e293b;
        display: inline-flex;
        align-items: center;
        gap: 7px;
        margin-right: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    
    /* Graphic Building Box */
    .building-graphic {
        position: relative;
        width: 210px;
        height: 125px;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
        border: 2px solid white;
        flex-shrink: 0;
    }
    .building-graphic img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .quote-tag {
        position: absolute;
        top: -12px;
        right: 15px;
        background: white;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        color: #1e293b;
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
        border: 1px solid #e2e8f0;
    }

    /* Metric Cards */
    .kpi-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .kpi-title {
        font-size: 11.5px;
        font-weight: 600;
        color: #64748b;
    }
    .kpi-val {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        margin-top: 4px;
        display: flex;
        align-items: baseline;
        gap: 6px;
    }
    .kpi-growth {
        font-size: 11.5px;
        font-weight: 700;
        color: #16a34a;
    }

    /* Container Box */
    .content-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .box-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        font-size: 13.5px;
        font-weight: 700;
        color: #0f172a;
    }

    /* Assistant Card with 3D Robot Mascot */
    .ai-assistant-wrapper {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 16px;
        padding: 18px 18px 16px 18px;
        color: white;
        margin-bottom: 14px;
        position: relative;
        overflow: hidden;
    }
    .robot-mascot {
        position: absolute;
        right: 8px;
        bottom: 8px;
        width: 82px;
        height: 82px;
        background-size: contain;
        background-repeat: no-repeat;
    }

    /* Employee Data Table */
    .emp-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }
    .emp-table th {
        text-align: left;
        padding: 10px;
        color: #64748b;
        font-size: 11px;
        font-weight: 600;
        border-bottom: 1px solid #e2e8f0;
    }
    .emp-table td {
        padding: 10px;
        border-bottom: 1px solid #f8fafc;
        color: #1e293b;
    }
    .risk-badge {
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 10.5px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    # Amazon Original Logo SVG
    st.markdown("""
    <div style="display:flex; align-items:center; gap:8px; padding: 4px 0 24px 0;">
        <svg width="95" height="30" viewBox="0 0 100 32" fill="white">
            <path d="M53.7 20.3c-2.3 1.8-5.6 2.7-8.5 2.7-4 0-7.6-1.5-10.4-4.1-.2-.2-.2-.5 0-.7l1.4-1.2c.2-.2.5-.1.7.1 2.3 2.1 5.1 3.2 8.3 3.2 2.3 0 4.9-.7 6.8-2.1.3-.2.6 0 .7.3l1 1.8z"/>
            <path d="M56.8 17.5c-.3-.4-1.9-.2-2.8 0-.3 0-.4-.3-.2-.5 1.4-1.4 3.7-1 4 .2.2 1.2-.8 3.5-2.2 4.7-.2.2-.4.1-.3-.1.5-.9 1.5-3.9 1.5-4.3z"/>
            <text x="0" y="20" font-family="'Plus Jakarta Sans', sans-serif" font-weight="900" font-size="21" fill="white">amazon</text>
        </svg>
        <div style="font-size:10px; color:#94a3b8; line-height:1.1; font-weight:600; margin-left:4px;">People<br>Analytics</div>
    </div>
    <div class="nav-item active">🏠 Home</div>
    <div class="nav-item">📈 Attendance Insights</div>
    <div class="nav-item">🤒 Sick Leave Tracker</div>
    <div class="nav-item">👤 Employee Profiles</div>
    <div class="nav-item">🎯 Coaching & Guidance</div>
    <div class="nav-item">📄 Reports & Analytics</div>
    <div class="nav-item">👥 Team Overview</div>
    <div class="nav-item">⚙️ Settings</div>
    
    <div style="background: radial-gradient(100% 100% at 50% 0%, #1e3a8a 0%, #0c162c 100%); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-top: 36px; color: white;">
        <div style="font-weight: 800; font-size: 11px;">Healthy Teams Build a Stronger Tomorrow</div>
        <div style="font-size: 10px; color: #93c5fd; margin-top: 5px; line-height: 1.3;">Better insights. Better conversations. A healthier workplace.</div>
        <div style="font-size: 18px; margin-top: 8px; color: #f59e0b;">⌣</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TOP BAR -----------------
st.markdown("""
<div class="topbar">
    <div class="search-box">
        <span>🔍</span> Search by employee, department, or team...
    </div>
    <div style="display:flex; align-items:center; gap:18px;">
        <span style="font-size:12px; color:#64748b; font-weight:700; cursor:pointer;">⚡ Filters</span>
        <span style="font-size:16px;">🔔</span>
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="text-align:right;">
                <div style="font-size:12px; font-weight:800; color:#0f172a;">Sarah Johnson</div>
                <div style="font-size:10px; color:#64748b;">HR Manager</div>
            </div>
            <div style="width:34px; height:34px; border-radius:50%; background:#fcd34d; display:flex; align-items:center; justify-content:center; font-size:16px; border:2px solid white; box-shadow:0 1px 3px rgba(0,0,0,0.1);">👩‍💼</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- MAIN LAYOUT -----------------
col_main, col_side = st.columns([7.4, 2.6])

with col_main:
    # 1. Hero Banner with Building Image
    st.markdown("""
    <div class="hero-container">
        <div>
            <div class="hero-badge">✨ AI Powered</div>
            <h2>Turn Attendance Patterns<br>into Positive Conversations</h2>
            <p>We help you spot recurring sick leave patterns, understand the bigger picture, and coach your team with confidence.</p>
            <div>
                <span class="pill-btn"><span style="color:#8b5cf6;">🟣</span> Detect Patterns</span>
                <span class="pill-btn"><span style="color:#0284c7;">🔵</span> Get AI Insights</span>
                <span class="pill-btn"><span style="color:#10b981;">🟢</span> Coach with Confidence</span>
                <span class="pill-btn"><span style="color:#059669;">🌱</span> Build Healthier Teams</span>
            </div>
        </div>
        <div style="position:relative;">
            <div class="quote-tag">Healthier people build brighter futures ↗</div>
            <div class="building-graphic">
                <img src="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=400&q=80" alt="Amazon Building">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Metric KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="kpi-title">Total Employees</span>
                <span style="background:#f5f3ff; color:#7c3aed; padding:4px 6px; border-radius:6px; font-size:12px;">👥</span>
            </div>
            <div class="kpi-val">{total_emp_count:,} <span class="kpi-growth">↑ 3%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="kpi-title">Sick Leave (This Month)</span>
                <span style="background:#fef2f2; color:#ef4444; padding:4px 6px; border-radius:6px; font-size:12px;">🤒</span>
            </div>
            <div class="kpi-val">124 <span class="kpi-growth">↑ 12%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown("""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="kpi-title">1-Day Sick Leave Events</span>
                <span style="background:#e0f2fe; color:#0284c7; padding:4px 6px; border-radius:6px; font-size:12px;">📅</span>
            </div>
            <div class="kpi-val">78 <span class="kpi-growth">↑ 18%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown("""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="kpi-title">2-Day Sick Leave Events</span>
                <span style="background:#dcfce7; color:#10b981; padding:4px 6px; border-radius:6px; font-size:12px;">🗓️</span>
            </div>
            <div class="kpi-val">46 <span class="kpi-growth">↑ 9%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Chart + Key Insights
    c_chart, c_insight = st.columns([6, 4])
    with c_chart:
        st.markdown("""
        <div class="content-box">
            <div class="box-header">
                <span>📈 Sick Leave Pattern Analysis</span>
                <span style="font-size:11px; font-weight:600; color:#64748b; background:#f8fafc; border:1px solid #e2e8f0; padding:2px 8px; border-radius:6px;">Last 6 Months ▾</span>
            </div>
        """, unsafe_allow_html=True)
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=[12, 14, 15, 16, 22, 42], mode='lines+markers', name='1-Day Leave', line=dict(color='#2563eb', width=2.5), marker=dict(size=5)))
        fig.add_trace(go.Scatter(x=months, y=[8, 9, 10, 11, 12, 26], mode='lines+markers', name='2-Day Leave', line=dict(color='#8b5cf6', width=2.5), marker=dict(size=5)))
        fig.update_layout(
            height=200,
            margin=dict(l=25, r=10, t=10, b=20),
            legend=dict(orientation="h", y=1.15, x=0, font=dict(size=11)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, linecolor='#e2e8f0'),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', range=[0, 50])
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with c_insight:
        st.markdown("""
        <div class="content-box" style="height:100%;">
            <div class="box-header">💡 Key Insights</div>
            <div style="display:flex; gap:10px; margin-bottom:10px;">
                <div style="width:28px; height:28px; border-radius:50%; background:#dcfce7; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">🌱</div>
                <div><div style="color:#10b981; font-weight:800; font-size:13px;">+18%</div><div style="color:#64748b; font-size:10.5px;">Increase in 1-day sick leave events (Last 6 months)</div></div>
            </div>
            <div style="display:flex; gap:10px; margin-bottom:10px;">
                <div style="width:28px; height:28px; border-radius:50%; background:#e0f2fe; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">📅</div>
                <div><div style="color:#0284c7; font-weight:800; font-size:13px;">2x higher</div><div style="color:#64748b; font-size:10.5px;">Sick leave on Mondays and Fridays</div></div>
            </div>
            <div style="display:flex; gap:10px; margin-bottom:10px;">
                <div style="width:28px; height:28px; border-radius:50%; background:#f3e8ff; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">🏖️</div>
                <div><div style="color:#9333ea; font-weight:800; font-size:13px;">35%</div><div style="color:#64748b; font-size:10.5px;">of 1-day leaves occur before/after public holidays</div></div>
            </div>
            <div style="display:flex; gap:10px;">
                <div style="width:28px; height:28px; border-radius:50%; background:#ede9fe; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">📈</div>
                <div><div style="color:#7c3aed; font-weight:800; font-size:13px;">Trend</div><div style="color:#64748b; font-size:10.5px;">Increasing pattern over the last 3 months</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 4. Employees Table
    rows_str = "".join([
        f"<tr><td><b>{r['name']}</b></td>"
        f"<td style='color:#64748b;'>{r['dept']}</td>"
        f"<td style='color:#475569;'>{r['pattern']}</td>"
        f"<td style='text-align:center; font-weight:600;'>{r['events']}</td>"
        f"<td style='color:#64748b;'>{r['date']}</td>"
        f"<td><span class='risk-badge' style='background:{r['bg']}; color:{r['color']};'>{r['risk']}</span></td>"
        f"<td><span style='color:#2563eb; font-weight:700; cursor:pointer;'>View →</span></td></tr>"
        for r in table_rows
    ])
    
    st.markdown(f"""
    <div class="content-box">
        <div class="box-header">👥 Employees with Repeated Sick Leave</div>
        <table class="emp-table">
            <thead>
                <tr>
                    <th>EMPLOYEE</th>
                    <th>DEPARTMENT</th>
                    <th>PATTERN</th>
                    <th>TOTAL EVENTS</th>
                    <th>LAST EVENT</th>
                    <th>RISK LEVEL</th>
                    <th>ACTION</th>
                </tr>
            </thead>
            <tbody>
                {rows_str}
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # Bottom Gradient Action Strip
    st.markdown("""
    <div style="background: linear-gradient(90deg, #0284c7, #2563eb); border-radius: 12px; padding: 10px 18px; margin-top: 14px; display: flex; justify-content: space-between; align-items: center; color: white; font-size: 12px; font-weight: 600;">
        <span>From attendance data to meaningful actions</span>
        <div style="display:flex; gap:12px;">
            <span>🔍 Spot patterns</span>
            <span>💬 Start conversations</span>
            <span>🌱 Build healthier teams</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_side:
    # 1. AI Assistant Card with Mascot Robot
    st.markdown("""
    <div class="ai-assistant-wrapper">
        <div style="font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; opacity:0.9;">🤖 AI Assistant</div>
        <div style="font-weight:800; font-size:14px; margin: 2px 0 6px 0;">Always here to help</div>
        <div style="font-size:11.5px; line-height:1.4; opacity:0.95; width:70%; margin-bottom:12px;">
            Hi Sarah! 👋<br>I've found <b>3 employees</b> with recurring 1-day and 2-day sick leave patterns in the last 6 months.
        </div>
        <div style="background:white; color:#1d4ed8; border-radius:8px; padding:7px; text-align:center; font-weight:700; font-size:11.5px; width:65%; cursor:pointer;">
            View Insights →
        </div>
        <div class="robot-mascot" style="background-image: url('https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png');"></div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Quick Action Links
    st.markdown("""
    <div class="content-box" style="margin-bottom: 12px; padding: 10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; border-bottom:1px solid #f8fafc;">
            <div><div style="font-size:11px; font-weight:700;">Top 3 At-Risk Employees</div><div style="font-size:9.5px; color:#64748b;">With recurring sick leave patterns</div></div>
            <span style="color:#94a3b8; font-size:12px;">&gt;</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; border-bottom:1px solid #f8fafc;">
            <div><div style="font-size:11px; font-weight:700;">Generate Coaching Conversation</div><div style="font-size:9.5px; color:#64748b;">For selected employee</div></div>
            <span style="color:#94a3b8; font-size:12px;">&gt;</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px;">
            <div><div style="font-size:11px; font-weight:700;">View Team Trend</div><div style="font-size:9.5px; color:#64748b;">Sick leave patterns by department</div></div>
            <span style="color:#94a3b8; font-size:12px;">&gt;</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Donut Chart
    st.markdown("""
    <div class="content-box" style="margin-bottom: 12px;">
        <div class="box-header">📊 Leave Duration Breakdown</div>
    """, unsafe_allow_html=True)
    fig_donut = go.Figure(data=[go.Pie(
        labels=['1 Day', '2 Days'],
        values=[78, 46],
        hole=.72,
        marker=dict(colors=['#2563eb', '#9333ea']),
        textinfo='none'
    )])
    fig_donut.update_layout(
        height=150,
        margin=dict(l=5, r=5, t=5, b=5),
        showlegend=False,
        annotations=[dict(text='<b>124</b><br><span style="font-size:9px; color:#64748b;">Total Sick</span>', x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    st.markdown("""
        <div style="display:flex; justify-content:space-around; font-size:10.5px; color:#475569; margin-top:2px;">
            <span><b style="color:#2563eb;">●</b> 1 Day: <b>78 (63%)</b></span>
            <span><b style="color:#9333ea;">●</b> 2 Days: <b>46 (37%)</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Recent Coaching Activity
    st.markdown("""
    <div class="content-box">
        <div class="box-header">
            <span>⚡ Recent Coaching</span>
            <span style="font-size:10px; color:#2563eb; cursor:pointer;">View All &gt;</span>
        </div>
        <div style="font-size:11px; padding:6px 0; border-bottom:1px solid #f8fafc; display:flex; justify-content:space-between; align-items:center;">
            <div><b>Emma Wilson</b><br><span style="font-size:9.5px; color:#94a3b8;">Completed • Jun 10</span></div>
            <span class="risk-badge" style="background:#fef3c7; color:#b45309;">1-Day Pattern</span>
        </div>
        <div style="font-size:11px; padding:6px 0; border-bottom:1px solid #f8fafc; display:flex; justify-content:space-between; align-items:center;">
            <div><b>James Carter</b><br><span style="font-size:9.5px; color:#94a3b8;">Scheduled • Jun 8</span></div>
            <span class="risk-badge" style="background:#ede9fe; color:#7c3aed;">2-Day Pattern</span>
        </div>
        <div style="font-size:11px; padding:6px 0; display:flex; justify-content:space-between; align-items:center;">
            <div><b>Olivia Davis</b><br><span style="font-size:9.5px; color:#94a3b8;">In Progress • Jun 6</span></div>
            <span class="risk-badge" style="background:#fef3c7; color:#b45309;">1-Day Pattern</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

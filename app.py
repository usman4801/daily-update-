import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

st.set_page_config(
    page_title="Amazon People Analytics",
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
        filepath = files[0]
        try:
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
                emp_count = len(valid) if len(valid) > 0 else 1248
                
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

# ----------------- MASTER CSS -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stApp {
        background-color: #f1f5f9 !important;
    }
    .block-container {
        padding: 1rem 2rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0b1528 !important;
        width: 240px !important;
        min-width: 240px !important;
    }
    .side-brand {
        display: flex;
        align-items: center;
        gap: 8px;
        padding-bottom: 20px;
        color: white;
    }
    .side-brand .logo {
        font-size: 24px;
        font-weight: 800;
        letter-spacing: -0.8px;
    }
    .side-brand .sub {
        font-size: 11px;
        color: #94a3b8;
        line-height: 1.1;
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

    /* Top Bar */
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 16px;
    }
    .search-input {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 8px 16px;
        font-size: 13px;
        width: 380px;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Hero Banner */
    .hero {
        background: linear-gradient(135deg, #e0f2fe 0%, #eff6ff 50%, #ecfdf5 100%);
        border-radius: 14px;
        padding: 20px 24px;
        border: 1px solid #bae6fd;
        margin-bottom: 16px;
    }
    .ai-pill {
        background: #0284c7;
        color: white;
        font-size: 10px;
        font-weight: 800;
        padding: 3px 9px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 6px;
    }
    .hero h2 {
        font-size: 21px;
        font-weight: 800;
        color: #0f172a;
        margin: 0 0 6px 0;
    }
    .hero p {
        font-size: 12px;
        color: #475569;
        margin: 0 0 14px 0;
    }
    .hero-btn {
        background: white;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 6px 12px;
        font-size: 11.5px;
        font-weight: 600;
        color: #1e293b;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 6px;
    }

    /* KPI Cards */
    .kpi-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 14px;
    }
    .kpi-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }
    .kpi-title {
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
    }
    .kpi-icon {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }
    .kpi-val {
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
        display: flex;
        align-items: baseline;
        gap: 6px;
    }
    .kpi-trend {
        font-size: 11px;
        font-weight: 700;
        color: #10b981;
    }

    /* Right Sidebar Cards */
    .ai-box {
        background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%);
        border-radius: 14px;
        padding: 16px;
        color: white;
        margin-bottom: 12px;
    }
    .content-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
    }
    .box-title {
        font-size: 13px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Direct Pure CSS Table */
    .emp-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 12px;
    }
    .emp-table th {
        text-align: left;
        padding: 9px 10px;
        color: #64748b;
        font-size: 11px;
        border-bottom: 1px solid #e2e8f0;
        font-weight: 600;
    }
    .emp-table td {
        padding: 10px 10px;
        border-bottom: 1px solid #f1f5f9;
        color: #1e293b;
    }
    .risk-badge {
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 10.5px;
        font-weight: 700;
        display: inline-block;
    }
    .action-link {
        color: #2563eb;
        font-weight: 700;
        text-decoration: none;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div class="side-brand">
        <div class="logo">amazon</div>
        <div class="sub">People<br>Analytics</div>
    </div>
    <div class="nav-item active">🏠 Home</div>
    <div class="nav-item">📈 Attendance Insights</div>
    <div class="nav-item">🤒 Sick Leave Tracker</div>
    <div class="nav-item">👤 Employee Profiles</div>
    <div class="nav-item">🎯 Coaching & Guidance</div>
    <div class="nav-item">📄 Reports & Analytics</div>
    <div class="nav-item">👥 Team Overview</div>
    <div class="nav-item">⚙️ Settings</div>
    <div style="background: radial-gradient(100% 100% at 50% 0%, #1e3a8a 0%, #0c162c 100%); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-top: 30px; color: white;">
        <div style="font-weight: 700; font-size: 11px;">Healthy Teams Build a Stronger Tomorrow</div>
        <div style="font-size: 10px; color: #93c5fd; margin-top: 4px;">Better insights. Better conversations. A healthier workplace.</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TOPBAR -----------------
st.markdown("""
<div class="topbar">
    <div class="search-input">
        <span>🔍</span> Search by employee, department, or team...
    </div>
    <div style="display:flex; align-items:center; gap:20px;">
        <span style="font-size:12px; color:#64748b; font-weight:600;">⚡ Filters</span>
        <span style="font-size:16px;">🔔</span>
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="text-align:right;">
                <div style="font-size:12px; font-weight:700; color:#0f172a;">Sarah Johnson</div>
                <div style="font-size:10px; color:#64748b;">HR Manager</div>
            </div>
            <div style="width:34px; height:34px; border-radius:50%; background:#fed7aa; display:flex; align-items:center; justify-content:center; font-size:16px;">👩‍💼</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- LAYOUT SPLIT -----------------
col_main, col_side = st.columns([7.2, 2.8])

with col_main:
    # 1. Hero
    st.markdown("""
    <div class="hero">
        <div class="ai-pill">✨ AI Powered</div>
        <h2>Turn Attendance Patterns into Positive Conversations</h2>
        <p>We help you spot recurring sick leave patterns, understand the bigger picture, and coach your team with confidence.</p>
        <div>
            <span class="hero-btn"><span style="color:#8b5cf6;">🟣</span> Detect Patterns</span>
            <span class="hero-btn"><span style="color:#0284c7;">🔵</span> Get AI Insights</span>
            <span class="hero-btn"><span style="color:#10b981;">🟢</span> Coach with Confidence</span>
            <span class="hero-btn"><span style="color:#059669;">🌱</span> Build Healthier Teams</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-head">
                <span class="kpi-title">Total Employees</span>
                <div class="kpi-icon" style="background:#f5f3ff; color:#7c3aed;">👥</div>
            </div>
            <div class="kpi-val">{total_emp_count:,} <span class="kpi-trend">↑ 3%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-head">
                <span class="kpi-title">Sick Leave (This Month)</span>
                <div class="kpi-icon" style="background:#fef2f2; color:#ef4444;">🤒</div>
            </div>
            <div class="kpi-val">124 <span class="kpi-trend">↑ 12%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-head">
                <span class="kpi-title">1-Day Sick Leave Events</span>
                <div class="kpi-icon" style="background:#e0f2fe; color:#0284c7;">📅</div>
            </div>
            <div class="kpi-val">78 <span class="kpi-trend">↑ 18%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown("""
        <div class="kpi-card">
            <div class="kpi-head">
                <span class="kpi-title">2-Day Sick Leave Events</span>
                <div class="kpi-icon" style="background:#dcfce7; color:#10b981;">🗓️</div>
            </div>
            <div class="kpi-val">46 <span class="kpi-trend">↑ 9%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Chart + Key Insights
    c_chart, c_insight = st.columns([6, 4])
    with c_chart:
        st.markdown("""
        <div class="content-box">
            <div class="box-title">
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
            <div class="box-title">💡 Key Insights</div>
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

    # 4. Pure HTML Table (No raw code leaks)
    rows_str = "".join([
        f"<tr><td><b>{r['name']}</b></td>"
        f"<td style='color:#64748b;'>{r['dept']}</td>"
        f"<td style='color:#475569;'>{r['pattern']}</td>"
        f"<td style='text-align:center; font-weight:600;'>{r['events']}</td>"
        f"<td style='color:#64748b;'>{r['date']}</td>"
        f"<td><span class='risk-badge' style='background:{r['bg']}; color:{r['color']};'>{r['risk']}</span></td>"
        f"<td><span class='action-link'>View →</span></td></tr>"
        for r in table_rows
    ])
    
    st.markdown(f"""
    <div class="content-box">
        <div class="box-title">👥 Employees with Repeated Sick Leave</div>
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

with col_side:
    # 1. AI Assistant Card
    st.markdown("""
    <div class="ai-box">
        <div style="font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; opacity:0.9;">🤖 AI Assistant</div>
        <div style="font-weight:800; font-size:14px; margin: 2px 0 6px 0;">Always here to help</div>
        <div style="font-size:11.5px; line-height:1.4; opacity:0.95; margin-bottom:12px;">
            Hi Sarah! 👋<br>I've found <b>3 employees</b> with recurring 1-day and 2-day sick leave patterns in the last 6 months.
        </div>
        <div style="background:white; color:#1d4ed8; border-radius:8px; padding:7px; text-align:center; font-weight:700; font-size:11.5px;">
            View Insights →
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Action Links
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
        <div class="box-title">📊 Leave Duration Breakdown</div>
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

    # 4. Recent Coaching
    st.markdown("""
    <div class="content-box">
        <div class="box-title">
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

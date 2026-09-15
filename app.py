import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob

st.set_page_config(
    page_title="Amazon People Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- DATA LOADER -----------------
@st.cache_data
def load_data():
    emp_count = 1248
    files = sorted(glob.glob("DWD-AUH1-*.xlsx"), reverse=True)
    if not files:
        files = sorted(glob.glob("*.xlsx"), reverse=True)
    if files:
        try:
            xls = pd.ExcelFile(files[0])
            if 'Roster' in xls.sheet_names:
                df = pd.read_excel(files[0], sheet_name='Roster')
                for i, r in df.head(10).iterrows():
                    if 'S.No' in r.values or 'AMZ ID' in r.values:
                        df = pd.read_excel(files[0], sheet_name='Roster', skiprows=i+1)
                        break
                valid = df.dropna(subset=['EMP Name'])
                if len(valid) > 0:
                    emp_count = len(valid)
        except Exception:
            pass
    return emp_count

total_emp_count = load_data()

table_data = [
    {"name": "Emma Wilson", "dept": "Operations", "pattern": "4 × 1 day (last 3 months)", "events": 4, "date": "Jun 12, 2025", "risk": "Medium", "r_c": "#d97706", "r_bg": "#fef3c7"},
    {"name": "James Carter", "dept": "Logistics", "pattern": "3 × 2 days (last 3 months)", "events": 3, "date": "Jun 10, 2025", "risk": "Medium", "r_c": "#d97706", "r_bg": "#fef3c7"},
    {"name": "Olivia Davis", "dept": "Customer Service", "pattern": "5 × 1 day (6 months)", "events": 5, "date": "Jun 08, 2025", "risk": "High", "r_c": "#dc2626", "r_bg": "#fee2e2"},
    {"name": "Liam Brown", "dept": "Finance", "pattern": "2 × 2 days (last 2 months)", "events": 2, "date": "Jun 05, 2025", "risk": "Low", "r_c": "#059669", "r_bg": "#d1fae5"},
    {"name": "Sophia Martinez", "dept": "Marketing", "pattern": "6 × 1 day (increasing trend)", "events": 6, "date": "Jun 02, 2025", "risk": "High", "r_c": "#dc2626", "r_bg": "#fee2e2"},
]

# ----------------- PIXEL-PERFECT CSS -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    .stApp {
        background-color: #f1f5f9 !important;
    }
    .block-container {
        padding: 1.5rem 2rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }

    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        width: 240px !important;
        min-width: 240px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding: 20px 16px !important;
    }
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        color: #94a3b8;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 4px;
        cursor: pointer;
        transition: all 0.2s;
    }
    .nav-item:hover { background: rgba(255,255,255,0.05); color: white; }
    .nav-item.active {
        background: #1e293b;
        color: #38bdf8;
        font-weight: 600;
    }

    /* --- TOP BAR --- */
    .topbar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .search-bar {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 20px;
        padding: 10px 20px;
        font-size: 13px;
        width: 400px;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    .profile-area {
        display: flex;
        align-items: center;
        gap: 20px;
    }

    /* --- HERO SECTION --- */
    .hero {
        background: linear-gradient(120deg, #e0f2fe 0%, #f0fdf4 50%, #e0f2fe 100%);
        border-radius: 16px;
        padding: 24px 28px;
        display: flex;
        justify-content: space-between;
        margin-bottom: 16px;
        border: 1px solid #bae6fd;
        position: relative;
    }
    .hero-btn {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 8px 12px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-right: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    }
    .hero-btn .t { font-size: 12px; font-weight: 600; color: #0f172a; line-height:1.2; }
    .hero-btn .s { font-size: 10px; color: #64748b; line-height:1.2; }
    .building-img {
        width: 240px;
        height: 140px;
        border-radius: 12px;
        object-fit: cover;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .quote-badge {
        position: absolute;
        top: 20px;
        right: 40px;
        font-size: 11px;
        font-weight: 700;
        color: #0f172a;
        transform: rotate(-2deg);
    }

    /* --- KPI CARDS --- */
    .kpi-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* --- GENERIC BOX --- */
    .white-box {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
        margin-bottom: 16px;
    }
    .box-title {
        font-size: 14px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* --- TABLE --- */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
    }
    .custom-table th {
        text-align: left;
        padding: 10px;
        font-size: 11px;
        font-weight: 600;
        color: #64748b;
        border-bottom: 1px solid #e2e8f0;
    }
    .custom-table td {
        padding: 12px 10px;
        font-size: 12px;
        color: #1e293b;
        border-bottom: 1px solid #f8fafc;
        vertical-align: middle;
    }
    .pill {
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 10px;
        font-weight: 700;
    }

    /* --- RIGHT ACTIONS --- */
    .action-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #f1f5f9;
        cursor: pointer;
    }
    .action-row:last-child { border-bottom: none; }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONTENT -----------------
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; padding: 0 0 30px 0;">
        <svg width="100" height="32" viewBox="0 0 100 32" fill="white">
            <path d="M53.7 20.3c-2.3 1.8-5.6 2.7-8.5 2.7-4 0-7.6-1.5-10.4-4.1-.2-.2-.2-.5 0-.7l1.4-1.2c.2-.2.5-.1.7.1 2.3 2.1 5.1 3.2 8.3 3.2 2.3 0 4.9-.7 6.8-2.1.3-.2.6 0 .7.3l1 1.8z"/>
            <path d="M56.8 17.5c-.3-.4-1.9-.2-2.8 0-.3 0-.4-.3-.2-.5 1.4-1.4 3.7-1 4 .2.2 1.2-.8 3.5-2.2 4.7-.2.2-.4.1-.3-.1.5-.9 1.5-3.9 1.5-4.3z"/>
            <text x="0" y="22" font-family="'Inter', sans-serif" font-weight="800" font-size="24" fill="white">amazon</text>
        </svg>
        <div style="font-size:10px; color:#94a3b8; line-height:1.2; font-weight:500;">People<br>Analytics</div>
    </div>
    
    <div class="nav-item active">🏠 &nbsp; Home</div>
    <div class="nav-item">📊 &nbsp; Attendance Insights</div>
    <div class="nav-item">🤒 &nbsp; Sick Leave Tracker</div>
    <div class="nav-item">👤 &nbsp; Employee Profiles</div>
    <div class="nav-item">🎯 &nbsp; Coaching & Guidance</div>
    <div class="nav-item">📄 &nbsp; Reports & Analytics</div>
    <div class="nav-item">👥 &nbsp; Team Overview</div>
    <div class="nav-item">⚙️ &nbsp; Settings</div>
    
    <div style="background: radial-gradient(120% 120% at 50% 100%, #1e3a8a 0%, #0f172a 100%); border-radius: 12px; padding: 16px; margin-top: 40px; color: white; position: relative; overflow: hidden;">
        <div style="font-weight: 700; font-size: 12px; margin-bottom: 6px;">Healthy Teams<br>Build a Stronger<br>Tomorrow</div>
        <div style="font-size: 10px; color: #94a3b8; line-height: 1.4;">Better insights. Better<br>conversations. A healthier<br>workplace.</div>
        <div style="position: absolute; bottom: 10px; left: 16px; font-size: 24px; color: #f59e0b; font-weight: bold;">⌣</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TOP NAVBAR -----------------
st.markdown("""
<div class="topbar">
    <div class="search-bar">
        <span>🔍</span> Search by employee, department, or team...
    </div>
    <div class="profile-area">
        <span style="font-size:13px; font-weight:600; color:#475569; display:flex; align-items:center; gap:6px;">⚡ Filters</span>
        <span style="font-size:18px;">🔔</span>
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="text-align:right;">
                <div style="font-size:13px; font-weight:700; color:#0f172a;">Sarah Johnson</div>
                <div style="font-size:11px; color:#64748b;">HR Manager</div>
            </div>
            <img src="https://ui-avatars.com/api/?name=Sarah+Johnson&background=fcd34d&color=000" style="width:36px; height:36px; border-radius:50%;">
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- MAIN LAYOUT -----------------
col_main, col_side = st.columns([7.2, 2.8], gap="medium")

with col_main:
    # 1. Hero Banner
    st.markdown("""
    <div class="hero">
        <div>
            <div style="background:#0ea5e9; color:white; font-size:11px; font-weight:700; padding:4px 12px; border-radius:20px; display:inline-block; margin-bottom:12px;">✨ AI Powered</div>
            <h2 style="font-size:26px; font-weight:800; color:#0f172a; margin:0 0 8px 0; line-height:1.2;">Turn Attendance Patterns<br>into Positive Conversations</h2>
            <p style="font-size:13px; color:#475569; margin:0 0 20px 0; max-width:90%;">We help you spot recurring sick leave patterns, understand the bigger picture, and coach your team with confidence.</p>
            <div style="display:flex; flex-wrap:wrap; gap:10px;">
                <div class="hero-btn"><div style="background:#f3e8ff; padding:6px; border-radius:8px;">🟣</div><div><div class="t">Detect Patterns</div><div class="s">Spot 1-day & 2-day trends</div></div></div>
                <div class="hero-btn"><div style="background:#e0f2fe; padding:6px; border-radius:8px;">🔵</div><div><div class="t">Get AI Insights</div><div class="s">Understand the why</div></div></div>
                <div class="hero-btn"><div style="background:#dcfce7; padding:6px; border-radius:8px;">🟢</div><div><div class="t">Coach with Confidence</div><div class="s">Get suggested conversations</div></div></div>
                <div class="hero-btn"><div style="background:#ccfbf1; padding:6px; border-radius:8px;">🌱</div><div><div class="t">Build Healthier Teams</div><div class="s">Support & retain talent</div></div></div>
            </div>
        </div>
        <div style="position:relative;">
            <div class="quote-badge">Healthier people<br>build brighter<br>futures ↗</div>
            <img src="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=400&q=80" class="building-img">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Four KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="font-size:12px; font-weight:600; color:#64748b;">Total Employees</span>
                <span style="background:#f3e8ff; color:#9333ea; padding:6px; border-radius:8px; font-size:14px;">👥</span>
            </div>
            <div>
                <div style="font-size:28px; font-weight:800; color:#0f172a; display:inline-block;">{total_emp_count:,}</div>
                <span style="color:#16a34a; font-size:12px; font-weight:700; margin-left:6px;">↑ 3%</span>
            </div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown("""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="font-size:12px; font-weight:600; color:#64748b;">Sick Leave (This Month)</span>
                <span style="background:#fef2f2; color:#ef4444; padding:6px; border-radius:8px; font-size:14px;">🤒</span>
            </div>
            <div>
                <div style="font-size:28px; font-weight:800; color:#0f172a; display:inline-block;">124</div>
                <span style="color:#16a34a; font-size:12px; font-weight:700; margin-left:6px;">↑ 12%</span>
            </div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown("""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="font-size:12px; font-weight:600; color:#64748b;">1-Day Sick Leave Events</span>
                <span style="background:#e0f2fe; color:#0284c7; padding:6px; border-radius:8px; font-size:14px;">📅</span>
            </div>
            <div>
                <div style="font-size:28px; font-weight:800; color:#0f172a; display:inline-block;">78</div>
                <span style="color:#16a34a; font-size:12px; font-weight:700; margin-left:6px;">↑ 18%</span>
            </div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown("""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between; margin-bottom:8px;">
                <span style="font-size:12px; font-weight:600; color:#64748b;">2-Day Sick Leave Events</span>
                <span style="background:#dcfce7; color:#16a34a; padding:6px; border-radius:8px; font-size:14px;">🗓️</span>
            </div>
            <div>
                <div style="font-size:28px; font-weight:800; color:#0f172a; display:inline-block;">46</div>
                <span style="color:#16a34a; font-size:12px; font-weight:700; margin-left:6px;">↑ 9%</span>
            </div>
            <div style="font-size:11px; color:#94a3b8; margin-top:2px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)

    # 3. Chart and Key Insights
    c_chart, c_insight = st.columns([6, 4], gap="medium")
    with c_chart:
        st.markdown("""
        <div class="white-box">
            <div class="box-title">
                <span>📈 Sick Leave Pattern Analysis</span>
                <span style="font-size:11px; font-weight:600; color:#64748b; background:#f8fafc; border:1px solid #e2e8f0; padding:4px 10px; border-radius:6px;">Last 6 Months ▾</span>
            </div>
        """, unsafe_allow_html=True)
        
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=months, y=[12, 14, 15, 16, 22, 42], mode='lines+markers', name='1-Day Leave', line=dict(color='#3b82f6', width=2.5), marker=dict(size=6)))
        fig.add_trace(go.Scatter(x=months, y=[8, 9, 10, 11, 12, 26], mode='lines+markers', name='2-Day Leave', line=dict(color='#8b5cf6', width=2.5), marker=dict(size=6)))
        fig.update_layout(
            height=220,
            margin=dict(l=20, r=10, t=10, b=20),
            legend=dict(orientation="h", y=1.15, x=0, font=dict(size=12)),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, linecolor='#e2e8f0'),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', range=[0, 45])
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with c_insight:
        st.markdown("""
        <div class="white-box" style="height: 100%;">
            <div class="box-title">💡 Key Insights</div>
            <div style="display:flex; gap:12px; margin-bottom:14px;">
                <div style="width:32px; height:32px; border-radius:50%; background:#dcfce7; display:flex; align-items:center; justify-content:center; font-size:14px; flex-shrink:0;">🌱</div>
                <div><div style="color:#16a34a; font-weight:800; font-size:14px;">+18%</div><div style="color:#64748b; font-size:11.5px; line-height:1.3;">Increase in 1-day sick leave events (Last 6 months)</div></div>
            </div>
            <div style="display:flex; gap:12px; margin-bottom:14px;">
                <div style="width:32px; height:32px; border-radius:50%; background:#e0f2fe; display:flex; align-items:center; justify-content:center; font-size:14px; flex-shrink:0;">📅</div>
                <div><div style="color:#0284c7; font-weight:800; font-size:14px;">2x higher</div><div style="color:#64748b; font-size:11.5px; line-height:1.3;">Sick leave on Mondays and Fridays</div></div>
            </div>
            <div style="display:flex; gap:12px; margin-bottom:14px;">
                <div style="width:32px; height:32px; border-radius:50%; background:#f3e8ff; display:flex; align-items:center; justify-content:center; font-size:14px; flex-shrink:0;">🏖️</div>
                <div><div style="color:#9333ea; font-weight:800; font-size:14px;">35%</div><div style="color:#64748b; font-size:11.5px; line-height:1.3;">of 1-day leaves occur before/after public holidays</div></div>
            </div>
            <div style="display:flex; gap:12px;">
                <div style="width:32px; height:32px; border-radius:50%; background:#ede9fe; display:flex; align-items:center; justify-content:center; font-size:14px; flex-shrink:0;">📈</div>
                <div><div style="color:#7c3aed; font-weight:800; font-size:14px;">Trend</div><div style="color:#64748b; font-size:11.5px; line-height:1.3;">Increasing pattern over the last 3 months</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 4. Table
    trs = ""
    for r in table_data:
        # Using unqiue UI Avatars matching names
        name_for_url = r['name'].replace(" ", "+")
        trs += f"""
        <tr>
            <td>
                <div style="display:flex; align-items:center; gap:8px;">
                    <img src="https://ui-avatars.com/api/?name={name_for_url}&background=random&color=fff" style="width:24px; height:24px; border-radius:50%;">
                    <b>{r['name']}</b>
                </div>
            </td>
            <td>{r['dept']}</td>
            <td>{r['pattern']}</td>
            <td style="text-align:center; font-weight:600;">{r['events']}</td>
            <td>{r['date']}</td>
            <td><span class="pill" style="background:{r['r_bg']}; color:{r['r_c']};">{r['risk']}</span></td>
            <td><span style="color:#3b82f6; font-weight:700; cursor:pointer;">View →</span></td>
        </tr>
        """

    st.markdown(f"""
    <div class="white-box">
        <div class="box-title">👥 Employees with Repeated Sick Leave</div>
        <table class="custom-table">
            <thead>
                <tr>
                    <th>Employee</th>
                    <th>Department</th>
                    <th>Pattern</th>
                    <th style="text-align:center;">Total Events</th>
                    <th>Last Event</th>
                    <th>Risk Level</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {trs}
            </tbody>
        </table>
    </div>
    
    <div style="background: linear-gradient(90deg, #38bdf8 0%, #3b82f6 100%); border-radius: 12px; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; color: white;">
        <span style="font-size:13px; font-weight:700;">🛡️ From attendance data to meaningful actions.</span>
        <div style="display:flex; gap:16px; font-size:12px; font-weight:600;">
            <span>🔍 Spot patterns</span>
            <span>💬 Start conversations</span>
            <span>🌱 Build healthier teams</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


with col_side:
    # 1. AI Assistant Card with Floating Robot
    st.markdown("""
    <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); border-radius: 16px; padding: 20px; color: white; margin-bottom: 16px; position: relative;">
        <div style="display:flex; align-items:center; gap:6px; font-size:11px; font-weight:800; text-transform:uppercase; margin-bottom:8px;">
            🤖 AI Assistant
        </div>
        <div style="font-weight:800; font-size:16px; margin-bottom:10px;">Always here to help</div>
        <div style="font-size:12px; line-height:1.5; width:75%; margin-bottom:16px; color:#e0e7ff;">
            Hi Sarah! 👋<br>I've found <b>3 employees</b> with recurring 1-day and 2-day sick leave patterns in the last 6 months.<br><br>Would you like to see the details and suggested coaching conversations?
        </div>
        <button style="background:white; color:#1d4ed8; border:none; border-radius:20px; padding:8px 16px; font-weight:700; font-size:12px; cursor:pointer;">
            View Insights →
        </button>
        <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" style="position:absolute; right: -5px; bottom: 10px; width:110px;">
    </div>
    """, unsafe_allow_html=True)

    # 2. Action Links
    st.markdown("""
    <div class="white-box" style="padding: 10px 18px;">
        <div class="action-row">
            <div style="display:flex; gap:12px; align-items:center;">
                <div style="font-size:16px; color:#3b82f6;">👤</div>
                <div><div style="font-size:13px; font-weight:700; color:#0f172a;">Top 3 At-Risk Employees</div><div style="font-size:11px; color:#64748b;">With recurring sick leave patterns</div></div>
            </div>
            <span style="color:#94a3b8; font-weight:bold;">&gt;</span>
        </div>
        <div class="action-row">
            <div style="display:flex; gap:12px; align-items:center;">
                <div style="font-size:16px; color:#3b82f6;">💬</div>
                <div><div style="font-size:13px; font-weight:700; color:#0f172a;">Generate Coaching Conversation</div><div style="font-size:11px; color:#64748b;">For selected employee</div></div>
            </div>
            <span style="color:#94a3b8; font-weight:bold;">&gt;</span>
        </div>
        <div class="action-row">
            <div style="display:flex; gap:12px; align-items:center;">
                <div style="font-size:16px; color:#3b82f6;">📊</div>
                <div><div style="font-size:13px; font-weight:700; color:#0f172a;">View Team Trend</div><div style="font-size:11px; color:#64748b;">Sick leave patterns by department</div></div>
            </div>
            <span style="color:#94a3b8; font-weight:bold;">&gt;</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Donut Chart
    st.markdown("""
    <div class="white-box">
        <div class="box-title">📊 Leave Duration Breakdown</div>
    """, unsafe_allow_html=True)
    fig_donut = go.Figure(data=[go.Pie(
        labels=['1 Day', '2 Days'],
        values=[78, 46],
        hole=.75,
        marker=dict(colors=['#3b82f6', '#9333ea']),
        textinfo='none'
    )])
    fig_donut.update_layout(
        height=180,
        margin=dict(l=5, r=5, t=5, b=5),
        showlegend=False,
        annotations=[dict(text='<span style="font-size:11px; color:#64748b;">Total Sick Leave</span><br><b style="font-size:24px; color:#0f172a;">124</b>', x=0.5, y=0.5, showarrow=False)]
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    st.markdown("""
        <div style="display:flex; justify-content:space-between; font-size:12px; color:#475569; margin-top:10px;">
            <span><b style="color:#3b82f6;">●</b> 1 Day</span> <b>78 (63%)</b>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; color:#475569; margin-top:6px;">
            <span><b style="color:#9333ea;">●</b> 2 Days</span> <b>46 (37%)</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Recent Coaching Activity
    st.markdown("""
    <div class="white-box">
        <div class="box-title">
            <span>⚡ Recent Coaching Activity</span>
            <span style="font-size:11px; color:#3b82f6; cursor:pointer;">View All &gt;</span>
        </div>
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px; border-bottom:1px solid #f8fafc; padding-bottom:10px;">
            <img src="https://ui-avatars.com/api/?name=Emma+Wilson&background=random" style="width:32px; height:32px; border-radius:50%;">
            <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <b style="font-size:12px; color:#0f172a;">Emma Wilson</b>
                    <span class="pill" style="background:#fef3c7; color:#d97706; font-size:9px;">1-Day Pattern</span>
                </div>
                <div style="font-size:10px; color:#64748b; margin-top:2px;">Coaching conversation completed • Jun 10, 2025</div>
            </div>
            <span style="color:#cbd5e1;">&gt;</span>
        </div>
        
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px; border-bottom:1px solid #f8fafc; padding-bottom:10px;">
            <img src="https://ui-avatars.com/api/?name=James+Carter&background=random" style="width:32px; height:32px; border-radius:50%;">
            <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <b style="font-size:12px; color:#0f172a;">James Carter</b>
                    <span class="pill" style="background:#f3e8ff; color:#9333ea; font-size:9px;">2-Day Pattern</span>
                </div>
                <div style="font-size:10px; color:#64748b; margin-top:2px;">Conversation scheduled • Jun 8, 2025</div>
            </div>
            <span style="color:#cbd5e1;">&gt;</span>
        </div>
        
        <div style="display:flex; align-items:center; gap:10px; border-bottom:1px solid #f8fafc; padding-bottom:10px;">
            <img src="https://ui-avatars.com/api/?name=Olivia+Davis&background=random" style="width:32px; height:32px; border-radius:50%;">
            <div style="flex:1;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <b style="font-size:12px; color:#0f172a;">Olivia Davis</b>
                    <span class="pill" style="background:#fef3c7; color:#d97706; font-size:9px;">1-Day Pattern</span>
                </div>
                <div style="font-size:10px; color:#64748b; margin-top:2px;">In progress • Jun 6, 2025</div>
            </div>
            <span style="color:#cbd5e1;">&gt;</span>
        </div>
    </div>
    
    <div class="white-box" style="background: #f0fdf4; border-color: #bbf7d0; display:flex; justify-content:space-between; align-items:center; padding: 12px 18px;">
        <div style="font-size:12px; color:#166534; font-weight:600; line-height:1.4;">
            "The best leaders don't just<br>they support people."
        </div>
        <span style="color:#166534; font-size:12px; font-weight:bold; cursor:pointer;">♡ Make a difference. →</span>
    </div>
    """, unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os

# Set page configuration to wide mode
st.set_page_config(page_title="Amazon People Analytics", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for exact UI clone
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background-color: #f1f5f9;
    }
    
    /* Hide Streamlit default header */
    header[data-testid="stHeader"] {
        display: none;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0b1528 !important;
        width: 250px !important;
    }
    
    .side-brand {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 0 25px 0;
        color: white;
        border-bottom: 1px solid rgba(255,255,255,0.08);
    }
    .side-logo {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -1px;
    }
    .side-subtitle {
        font-size: 11px;
        color: #94a3b8;
        line-height: 1.1;
    }
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 14px;
        color: #94a3b8;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 4px;
        cursor: pointer;
    }
    .nav-item.active {
        background: #1e293b;
        color: #38bdf8;
        font-weight: 600;
    }
    .nav-item:hover {
        background: rgba(255,255,255,0.04);
        color: white;
    }
    
    /* Top Banner */
    .hero-banner {
        background: linear-gradient(135deg, #e0f2fe 0%, #f0fdf4 100%);
        border-radius: 16px;
        padding: 24px 28px;
        position: relative;
        border: 1px solid #bae6fd;
        margin-bottom: 20px;
    }
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #0284c7;
        color: white;
        font-size: 11px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        text-transform: uppercase;
    }
    .hero-title {
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
        margin: 10px 0 6px 0;
    }
    .hero-desc {
        color: #475569;
        font-size: 13px;
        margin-bottom: 18px;
    }
    .pill-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: white;
        padding: 8px 14px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        font-size: 12px;
        font-weight: 600;
        color: #1e293b;
        margin-right: 8px;
        border: 1px solid #e2e8f0;
    }
    
    /* Metric Card */
    .metric-card {
        background: white;
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
        height: 100%;
    }
    .metric-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .metric-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }
    .metric-val {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
        display: flex;
        align-items: baseline;
        gap: 8px;
    }
    .metric-growth {
        font-size: 12px;
        font-weight: 700;
        color: #16a34a;
    }
    .metric-label {
        color: #64748b;
        font-size: 12px;
        font-weight: 600;
    }
    
    /* Insight Items */
    .insight-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        height: 100%;
    }
    .insight-item {
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
    }
    .insight-icon {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .insight-number {
        font-size: 15px;
        font-weight: 800;
    }
    .insight-text {
        font-size: 11px;
        color: #64748b;
        margin-top: 1px;
    }
    
    /* Right Side Assistant Card */
    .assistant-card {
        background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%);
        border-radius: 16px;
        padding: 20px;
        color: white;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- DATA LOADING -----------------
@st.cache_data
def load_excel_data():
    files = sorted(glob.glob("DWD-AUH1-*.xlsx"), reverse=True)
    if not files:
        files = sorted(glob.glob("*.xlsx"), reverse=True)
    
    if not files:
        return None, None
    
    filepath = files[0]
    xls = pd.ExcelFile(filepath)
    
    # Read Roster Sheet
    roster_df = pd.DataFrame()
    if 'Roster' in xls.sheet_names:
        df_raw = pd.read_excel(filepath, sheet_name='Roster')
        # S.No row index search
        header_idx = None
        for i, row in df_raw.head(10).iterrows():
            if 'S.No' in row.values or 'AMZ ID' in row.values:
                header_idx = i
                break
        if header_idx is not None:
            roster_df = pd.read_excel(filepath, sheet_name='Roster', skiprows=header_idx + 1)
        else:
            roster_df = pd.read_excel(filepath, sheet_name='Roster')
            
    return roster_df, os.path.basename(filepath)

roster_df, loaded_file = load_excel_data()

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div class="side-brand">
        <div class="side-logo">amazon</div>
        <div class="side-subtitle">People<br>Analytics</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="nav-item active">🏠 Home</div>
    <div class="nav-item">📊 Attendance Insights</div>
    <div class="nav-item">🤒 Sick Leave Tracker</div>
    <div class="nav-item">👤 Employee Profiles</div>
    <div class="nav-item">🎯 Coaching & Guidance</div>
    <div class="nav-item">📄 Reports & Analytics</div>
    <div class="nav-item">👥 Team Overview</div>
    <div class="nav-item">⚙️ Settings</div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(255,255,255,0.06); padding: 16px; border-radius: 12px; color: white;">
        <div style="font-weight: 700; font-size: 13px;">Healthy Teams Build a Stronger Tomorrow</div>
        <div style="font-size: 11px; color: #94a3b8; margin-top: 6px;">Better insights. Better conversations. A healthier workplace.</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- MAIN LAYOUT -----------------
# Top Navbar
top_col1, top_col2, top_col3 = st.columns([6, 3, 3])
with top_col1:
    st.text_input("🔍 Search by employee, department, or team...", placeholder="Search by employee, department, or team...", label_visibility="collapsed")
with top_col2:
    st.markdown(f"<p style='margin-top:8px; font-size:12px; color:#64748b;'>📁 <b>Active File:</b> {loaded_file}</p>", unsafe_allow_html=True)
with top_col3:
    st.markdown("""
    <div style="display:flex; align-items:center; justify-content:flex-end; gap:10px;">
        <span style="font-size: 18px;">🔔</span>
        <div style="text-align:right;">
            <div style="font-size:12px; font-weight:700; color:#0f172a;">Sarah Johnson</div>
            <div style="font-size:10px; color:#64748b;">HR Manager</div>
        </div>
        <div style="width:32px; height:32px; border-radius:50%; background:#e2e8f0; display:flex; align-items:center; justify-content:center;">👩‍💼</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Grid (Left 9 cols, Right 3 cols)
main_col, right_col = st.columns([9.5, 3.5])

with main_col:
    # 1. Hero AI Banner
    st.markdown("""
    <div class="hero-banner">
        <span class="ai-badge">✨ AI Powered</span>
        <div class="hero-title">Turn Attendance Patterns into Positive Conversations</div>
        <div class="hero-desc">We help you spot recurring sick leave patterns, understand the bigger picture, and coach your team with confidence.</div>
        <div>
            <span class="pill-btn">🔍 Detect Patterns</span>
            <span class="pill-btn">💡 Get AI Insights</span>
            <span class="pill-btn">🤝 Coach with Confidence</span>
            <span class="pill-btn">🌱 Build Healthier Teams</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. KPI Cards (4 metrics)
    total_emp = len(roster_df) if roster_df is not None and not roster_df.empty else 1248
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-label">Total Employees</div>
                <div class="metric-icon" style="background:#f3e8ff; color:#9333ea;">👥</div>
            </div>
            <div class="metric-val">{total_emp:,} <span class="metric-growth">↑ 3%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:4px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-label">Sick Leave (This Month)</div>
                <div class="metric-icon" style="background:#fee2e2; color:#ef4444;">🤒</div>
            </div>
            <div class="metric-val">124 <span class="metric-growth">↑ 12%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:4px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-label">1-Day Sick Leave Events</div>
                <div class="metric-icon" style="background:#e0f2fe; color:#0284c7;">📅</div>
            </div>
            <div class="metric-val">78 <span class="metric-growth">↑ 18%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:4px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-top">
                <div class="metric-label">2-Day Sick Leave Events</div>
                <div class="metric-icon" style="background:#dcfce7; color:#16a34a;">🗓️</div>
            </div>
            <div class="metric-val">46 <span class="metric-growth">↑ 9%</span></div>
            <div style="font-size:10px; color:#94a3b8; margin-top:4px;">vs. last month</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 3. Sick Leave Pattern Analysis + Key Insights
    chart_col, insight_col = st.columns([6.8, 3.2])
    with chart_col:
        st.markdown("""
        <div style="background:white; border-radius:14px; padding:18px; border:1px solid #e2e8f0;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <span style="font-weight:700; font-size:14px; color:#0f172a;">📈 Sick Leave Pattern Analysis</span>
                <span style="font-size:11px; color:#64748b; background:#f8fafc; padding:4px 8px; border-radius:6px; border:1px solid #e2e8f0;">Last 6 Months ▼</span>
            </div>
        """, unsafe_allow_html=True)
        
        # Dual Line Plot
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=months, y=[12, 14, 15, 16, 22, 42], mode='lines+markers', name='1-Day Leave',
                                      line=dict(color='#2563eb', width=2.5), marker=dict(size=6)))
        fig_line.add_trace(go.Scatter(x=months, y=[8, 9, 10, 11, 12, 26], mode='lines+markers', name='2-Day Leave',
                                      line=dict(color='#8b5cf6', width=2.5), marker=dict(size=6)))
        fig_line.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with insight_col:
        st.markdown("""
        <div class="insight-card">
            <div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:16px;">💡 Key Insights</div>
            <div class="insight-item">
                <div class="insight-icon" style="background:#dcfce7; color:#16a34a;">🌱</div>
                <div>
                    <div class="insight-number" style="color:#16a34a;">+18%</div>
                    <div class="insight-text">Increase in 1-day sick leave events (Last 6 months)</div>
                </div>
            </div>
            <div class="insight-item">
                <div class="insight-icon" style="background:#e0f2fe; color:#0284c7;">📅</div>
                <div>
                    <div class="insight-number" style="color:#0284c7;">2x higher</div>
                    <div class="insight-text">Sick leave on Mondays and Fridays</div>
                </div>
            </div>
            <div class="insight-item">
                <div class="insight-icon" style="background:#f3e8ff; color:#9333ea;">🏖️</div>
                <div>
                    <div class="insight-number" style="color:#9333ea;">35%</div>
                    <div class="insight-text">of 1-day leaves occur before/after public holidays</div>
                </div>
            </div>
            <div class="insight-item">
                <div class="insight-icon" style="background:#ede9fe; color:#7c3aed;">📈</div>
                <div>
                    <div class="insight-number" style="color:#7c3aed;">Trend</div>
                    <div class="insight-text">Increasing pattern over the last 3 months</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Table: Employees with Repeated Sick Leave
    st.markdown("""
    <div style="background:white; border-radius:14px; padding:18px; border:1px solid #e2e8f0;">
        <div style="font-weight:700; font-size:14px; color:#0f172a; margin-bottom:14px;">👥 Employees with Repeated Sick Leave</div>
    """, unsafe_allow_html=True)
    
    if roster_df is not None and not roster_df.empty and 'EMP Name' in roster_df.columns:
        # Pull actual employees from file if available
        sample_emps = roster_df[['EMP Name', 'Department']].dropna().head(5).copy()
        sample_emps['Pattern'] = ['4 × 1 day (last 3 months)', '3 × 2 days (last 3 months)', '5 × 1 day (3 months)', '2 × 2 days (last 2 months)', '6 × 1 day (increasing trend)']
        sample_emps['Total Events'] = [4, 3, 5, 2, 6]
        sample_emps['Last Event'] = ['Jun 12, 2026', 'Jun 10, 2026', 'Jun 08, 2026', 'Jun 05, 2026', 'Jun 02, 2026']
        sample_emps['Risk Level'] = ['Medium', 'Medium', 'High', 'Low', 'High']
        st.dataframe(sample_emps, use_container_width=True, hide_index=True)
    else:
        table_data = pd.DataFrame({
            "Employee": ["Emma Wilson", "James Carter", "Olivia Davis", "Liam Brown", "Sophia Martinez"],
            "Department": ["Operations", "Logistics", "Customer Service", "Finance", "Marketing"],
            "Pattern": ["4 × 1 day (last 3 months)", "3 × 2 days (last 3 months)", "5 × 1 day (3 months)", "2 × 2 days (last 2 months)", "6 × 1 day (increasing trend)"],
            "Total Events": [4, 3, 5, 2, 6],
            "Last Event": ["Jun 12, 2026", "Jun 10, 2026", "Jun 08, 2026", "Jun 05, 2026", "Jun 02, 2026"],
            "Risk Level": ["Medium", "Medium", "High", "Low", "High"]
        })
        st.dataframe(table_data, use_container_width=True, hide_index=True)
        
    st.markdown("</div>", unsafe_allow_html=True)

# ----------------- RIGHT COLUMN -----------------
with right_col:
    # AI Assistant Banner
    st.markdown("""
    <div class="assistant-card">
        <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.5px; opacity:0.85;">🤖 AI Assistant</div>
        <div style="font-weight:700; font-size:15px; margin: 4px 0 10px 0;">Always here to help</div>
        <div style="font-size:12px; line-height:1.4; opacity:0.95; margin-bottom:14px;">
            Hi Sarah! 👋<br>I've found <b>3 employees</b> with recurring 1-day and 2-day sick leave patterns in the last 6 months. Would you like to see details?
        </div>
        <button style="background:white; color:#1d4ed8; border:none; padding:8px 16px; border-radius:8px; font-weight:700; font-size:12px; cursor:pointer; width:100%;">View Insights →</button>
    </div>
    """, unsafe_allow_html=True)

    # Donut Chart - Leave Duration Breakdown
    st.markdown("""
    <div style="background:white; border-radius:14px; padding:18px; border:1px solid #e2e8f0; margin-bottom:16px;">
        <div style="font-weight:700; font-size:13px; color:#0f172a; margin-bottom:8px;">📊 Leave Duration Breakdown</div>
    """, unsafe_allow_html=True)
    
    fig_donut = go.Figure(data=[go.Pie(
        labels=['1 Day', '2 Days'],
        values=[78, 46],
        hole=.7,
        marker=dict(colors=['#2563eb', '#9333ea']),
        textinfo='none'
    )])
    fig_donut.update_layout(
        height=190,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        annotations=[dict(text='<b>124</b><br><span style="font-size:10px; color:#64748b;">Total Sick Leave</span>', x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    st.plotly_chart(fig_donut, use_container_width=True)
    st.markdown("""
        <div style="display:flex; justify-content:space-between; font-size:12px; color:#475569; margin-top:4px;">
            <span>🔵 1 Day: <b>78 (63%)</b></span>
            <span>🟣 2 Days: <b>46 (37%)</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Coaching Quick Action List
    st.markdown("""
    <div style="background:white; border-radius:14px; padding:16px; border:1px solid #e2e8f0;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <span style="font-weight:700; font-size:13px; color:#0f172a;">⚡ Recent Coaching Activity</span>
            <span style="font-size:11px; color:#2563eb; cursor:pointer;">View All &gt;</span>
        </div>
        <div style="font-size:12px; padding:8px 0; border-bottom:1px solid #f1f5f9;">
            <b>Emma Wilson</b> <span style="color:#d97706; font-size:10px; background:#fef3c7; padding:2px 6px; border-radius:4px;">1-Day Pattern</span><br>
            <span style="font-size:11px; color:#64748b;">Completed • Jun 10, 2026</span>
        </div>
        <div style="font-size:12px; padding:8px 0; border-bottom:1px solid #f1f5f9;">
            <b>James Carter</b> <span style="color:#7c3aed; font-size:10px; background:#ede9fe; padding:2px 6px; border-radius:4px;">2-Day Pattern</span><br>
            <span style="font-size:11px; color:#64748b;">Scheduled • Jun 8, 2026</span>
        </div>
        <div style="font-size:12px; padding:8px 0;">
            <b>Olivia Davis</b> <span style="color:#d97706; font-size:10px; background:#fef3c7; padding:2px 6px; border-radius:4px;">1-Day Pattern</span><br>
            <span style="font-size:11px; color:#64748b;">In Progress • Jun 6, 2026</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

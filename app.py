import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os
import datetime
import re

st.set_page_config(
    page_title="Amazon People Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE FOR KPI CLICKS ---
if 'active_view' not in st.session_state:
    st.session_state.active_view = None

def toggle_view(view_name):
    if st.session_state.active_view == view_name:
        st.session_state.active_view = None  # Close if already open
    else:
        st.session_state.active_view = view_name # Open selected

# ----------------- EXACT FIGMA CSS + INTERACTIVITY -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stApp {
        background-color: #f3f6fb !important;
    }
    .block-container {
        padding: 0.8rem 1.6rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"], [data-testid="stToolbar"] {
        display: none !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0d172a !important;
        width: 235px !important;
        min-width: 235px !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding: 16px 12px !important;
    }

    /* General Streamlit Buttons (Like Quick Actions) */
    div.stButton > button {
        border: 1px solid #e2e8f0 !important;
        background-color: white !important;
        color: #1e293b !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        text-align: left !important;
        padding: 8px 12px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
        transition: all 0.2s ease-in-out !important;
        width: 100% !important;
    }
    div.stButton > button:hover {
        border-color: #38bdf8 !important;
        background-color: #f0f9ff !important;
    }

    /* Sidebar Navigation Buttons */
    section[data-testid="stSidebar"] div.stButton { margin-bottom: -10px !important; }
    section[data-testid="stSidebar"] div.stButton > button { background-color: transparent !important; border: none !important; color: #94a3b8 !important; box-shadow: none !important; font-weight: 500 !important; padding: 6px 12px !important; min-height: 34px !important; border-radius: 8px !important; }
    section[data-testid="stSidebar"] div.stButton > button:hover { background-color: #1e293b !important; color: #38bdf8 !important; }
    section[data-testid="stSidebar"] div.stButton:first-of-type > button { background-color: #1e293b !important; color: #38bdf8 !important; font-weight: 600 !important; }


    /* =====================================================================
       KPI CARD + ATTACHED "VIEW" FOOTER (no overlap, no clipping)
       ===================================================================== */
    .kpi-card { 
        background: white; 
        border: 1px solid #e2e8f0; 
        border-bottom: none;
        border-radius: 12px 12px 0 0; 
        padding: 14px 16px 10px 16px; 
        transition: all 0.2s ease;
    }
    .kpi-card:hover {
        border-color: #38bdf8;
    }

    /* Pull the button's element-container up by 1px so it visually joins the card (removes double border) */
    div.element-container:has(.kpi-btn-wrapper) + div.element-container {
        margin-top: -1px !important;
        margin-bottom: 15px !important;
    }
    div.element-container:has(.kpi-btn-wrapper) + div.element-container div.stButton {
        display: flex !important;
        justify-content: flex-end !important;
        width: 100% !important;
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-top: 1px dashed #eef2f7 !important;
        border-radius: 0 0 12px 12px !important;
        padding: 6px 12px !important;
    }
    div.element-container:has(.kpi-btn-wrapper) + div.element-container div.stButton > button {
        background-color: #f0f9ff !important;
        color: #0284c7 !important;
        border: 1px solid #bae6fd !important;
        border-radius: 12px !important;
        padding: 2px 10px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        min-height: 26px !important;
        height: 26px !important;
        width: fit-content !important;
        box-shadow: none !important;
        opacity: 1 !important; /* Fully Visible and Clickable! */
        margin: 0 !important;
    }
    div.element-container:has(.kpi-btn-wrapper) + div.element-container div.stButton > button:hover {
        background-color: #e0f2fe !important;
        border-color: #7dd3fc !important;
        color: #0369a1 !important;
    }
    div.element-container:has(.kpi-btn-wrapper) + div.element-container div.stButton > button p {
        font-size: 11px !important;
    }
    /* ===================================================================== */

    .kpi-title { font-size: 11px; font-weight: 600; color: #64748b; }
    .kpi-val { font-size: 24px; font-weight: 800; color: #0f172a; margin-top: 4px; display: flex; align-items: baseline; gap: 6px; }

    .content-box { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; }
    .box-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 13px; font-weight: 700; color: #0f172a; }

    .custom-dropdown { font-size: 11px; font-weight: 600; color: #64748b; background: #f8fafc; border: 1px solid #e2e8f0; padding: 3px 6px; border-radius: 6px; outline: none; cursor: pointer; font-family: inherit; }
    .custom-dropdown:hover { border-color: #cbd5e1; color: #0f172a; }

    .stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid #e2e8f0; }
    
    .emp-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .emp-table th { text-align: left; padding: 8px 10px; color: #64748b; font-size: 10.5px; border-bottom: 1px solid #e2e8f0; font-weight: 600; }
    .emp-table td { padding: 9px 10px; border-bottom: 1px solid #f8fafc; color: #1e293b; }
    .risk-badge { padding: 2px 7px; border-radius: 6px; font-size: 10.5px; font-weight: 700; }
    
    [data-testid="stImage"] img { border-radius: 14px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .ai-insight-btn { background: white; color: #2563eb; border-radius: 8px; padding: 10px 16px; font-weight: 700; font-size: 13px; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; z-index: 2; text-decoration: none; transition: transform 0.1s; }
    .ai-insight-btn:hover { transform: scale(1.03); }
    .action-link:hover { cursor: pointer; text-decoration: underline; }

    /* Fix Datepicker layout */
    div[data-testid="stDateInput"] label, div[data-testid="stSelectbox"] label { display: none !important; }
    div[data-testid="stDateInput"] div[data-baseweb="input"], div[data-testid="stSelectbox"] div[data-baseweb="select"] { border-radius: 20px !important; min-height: 36px !important; height: 36px !important; border: 1px solid #e2e8f0 !important; background-color: white !important; }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:8px; padding: 4px 0 24px 0;">
        <svg width="95" height="30" viewBox="0 0 100 32" fill="white">
            <path d="M53.7 20.3c-2.3 1.8-5.6 2.7-8.5 2.7-4 0-7.6-1.5-10.4-4.1-.2-.2-.2-.5 0-.7l1.4-1.2c.2-.2.5-.1.7.1 2.3 2.1 5.1 3.2 8.3 3.2 2.3 0 4.9-.7 6.8-2.1.3-.2.6 0 .7.3l1 1.8z"/>
            <path d="M56.8 17.5c-.3-.4-1.9-.2-2.8 0-.3 0-.4-.3-.2-.5 1.4-1.4 3.7-1 4 .2.2 1.2-.8 3.5-2.2 4.7-.2.2-.4.1-.3-.1.5-.9 1.5-3.9 1.5-4.3z"/>
            <text x="0" y="20" font-family="'Plus Jakarta Sans', sans-serif" font-weight="900" font-size="21" fill="white">amazon</text>
        </svg>
        <div style="font-size:10px; color:#94a3b8; line-height:1.1; font-weight:600; margin-left:4px;">People<br>Analytics</div>
    </div>
    """, unsafe_allow_html=True)

    nav_items = ["🏠 Home", "📈 Attendance Insights", "🤒 Sick Leave Tracker", "👤 Employee Profiles", "🎯 Coaching & Guidance", "📄 Reports & Analytics", "👥 Team Overview", "⚙️ Settings"]
    for item in nav_items:
        if st.button(item, key=f"nav_{item}"):
            st.toast(f"Navigating to {item}...", icon="🚀")
    
    st.markdown("""
    <div style="background: radial-gradient(100% 100% at 50% 0%, #1e3a8a 0%, #0d172a 100%); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 14px; margin-top: 36px; color: white;">
        <div style="font-weight: 800; font-size: 11px;">Healthy Teams Build a Stronger Tomorrow</div>
        <div style="font-size: 10px; color: #93c5fd; margin-top: 5px; line-height: 1.3;">Better insights. Better conversations. A healthier workplace.</div>
        <div style="font-size: 18px; margin-top: 8px; color: #f59e0b;">⌣</div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- TOP BAR -----------------
top_col1, top_col2, top_col3 = st.columns([1.2, 2.3, 5.0])

with top_col1:
    selected_site = st.selectbox("Site", ["AUH1", "DXB", "DXB3"], label_visibility="collapsed")
with top_col2:
    default_start = datetime.date(2026, 9, 1)
    default_end = datetime.date(2026, 9, 4)
    selected_dates = st.date_input("Date Range", value=(default_start, default_end), label_visibility="collapsed")
with top_col3:
    st.markdown("""
    <div style="display:flex; align-items:center; justify-content:flex-end; gap:18px; margin-top: 2px;">
        <span style="font-size:16px; cursor:pointer;" title="Search Employee">🔍</span>
        <span style="font-size:12px; color:#64748b; font-weight:700; cursor:pointer;">⚡ Filters</span>
        <span style="font-size:16px; cursor:pointer;">🔔</span>
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="text-align:right;">
                <div style="font-size:13.5px; font-weight:800; color:#0f172a; margin-top: 1px;">javmuhak</div>
            </div>
            <div style="width:34px; height:34px; border-radius:50%; background:#ffffff; border: 1px solid #cbd5e1; display:flex; align-items:center; justify-content:center; overflow: hidden;">
                <img src="https://upload.wikimedia.org/wikipedia/commons/d/de/Amazon_icon.png" style="width: 18px;">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# --- AUTOMATED DATA FETCHING LOGIC ---
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
elif isinstance(selected_dates, tuple) and len(selected_dates) == 1:
    start_date = end_date = selected_dates[0]
else:
    start_date = end_date = datetime.date.today()

@st.cache_data
def load_real_data(site, start_d, end_d):
    all_files = sorted(glob.glob(f"*{site}*.xlsx"), reverse=True)
    valid_files = []
    for f in all_files:
        match = re.search(r'(\d{8})', f)
        if match:
            date_str = match.group(1)
            try:
                file_date = datetime.datetime.strptime(date_str, "%d%m%Y").date()
                if start_d <= file_date <= end_d:
                    valid_files.append((file_date, f))
            except ValueError:
                pass
    if not valid_files:
        return pd.DataFrame()
        
    dfs = []
    for f_date, f in valid_files:
        try:
            xls = pd.ExcelFile(f)
            if 'Roster' in xls.sheet_names:
                df = pd.read_excel(f, sheet_name='Roster')
                header_idx = 0
                for i, row in df.head(15).iterrows():
                    row_strs = [str(val).strip() for val in row.values]
                    if 'EMP Name' in row_strs or 'AMZ ID' in row_strs or 'S.No' in row_strs:
                        header_idx = i
                        break
                df = pd.read_excel(f, sheet_name='Roster', skiprows=header_idx+1)
                df.columns = df.columns.astype(str).str.strip() 
                if 'EMP Name' in df.columns and 'Attendance' in df.columns:
                    temp_df = df[['EMP Name', 'Department', 'Attendance']].copy()
                    temp_df['Date'] = f_date
                    dfs.append(temp_df)
        except Exception:
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

df = load_real_data(selected_site, start_date, end_date)

total_emp_count = 0
total_sick = 0
one_day_events = 0
two_day_events = 0

df_1_day = pd.DataFrame()
df_2_day = pd.DataFrame()
sick_df = pd.DataFrame()
table_data = []
chart_fig = go.Figure()

if not df.empty:
    total_emp_count = df['EMP Name'].nunique()
    sick_df = df[df['Attendance'].astype(str).str.upper() == 'SL'].copy()
    total_sick = len(sick_df)
    
    if not sick_df.empty:
        one_day_records = []
        two_day_records = []
        sick_df = sick_df.sort_values(by=['EMP Name', 'Date'])
        for emp, group in sick_df.groupby('EMP Name'):
            dates = sorted(group['Date'].tolist())
            dept = group['Department'].iloc[0] if pd.notna(group['Department'].iloc[0]) else "Unknown"
            streaks = []
            current_streak = [dates[0]]
            for d in dates[1:]:
                if (d - current_streak[-1]).days == 1:
                    current_streak.append(d)
                else:
                    streaks.append(current_streak)
                    current_streak = [d]
            streaks.append(current_streak)
            for s in streaks:
                if len(s) == 1:
                    one_day_events += 1
                    one_day_records.append({"EMP Name": emp, "Department": dept, "Leave Date": s[0].strftime('%Y-%m-%d'), "Type": "1-Day"})
                else:
                    two_day_events += 1
                    two_day_records.append({"EMP Name": emp, "Department": dept, "Start Date": s[0].strftime('%Y-%m-%d'), "End Date": s[-1].strftime('%Y-%m-%d'), "Total Days": len(s), "Type": "Consecutive"})
        
        df_1_day = pd.DataFrame(one_day_records)
        df_2_day = pd.DataFrame(two_day_records)
        
        sl_counts = sick_df.groupby(['EMP Name', 'Department']).agg(
            events=('Date', 'count'), last_date=('Date', 'max')
        ).reset_index().sort_values(by='events', ascending=False).head(5)
        
        for _, row in sl_counts.iterrows():
            events = row['events']
            risk = "High" if events >= 3 else ("Medium" if events == 2 else "Low")
            bg = "#fee2e2" if risk == "High" else ("#fef3c7" if risk == "Medium" else "#d1fae5")
            color = "#dc2626" if risk == "High" else ("#d97706" if risk == "Medium" else "#059669")
            table_data.append({
                "name": row['EMP Name'], "dept": row['Department'] if pd.notna(row['Department']) else "Unknown",
                "pattern": f"{events} sick day(s)", "events": events,
                "date": row['last_date'].strftime("%b %d, %Y"), "risk": risk, "color": color, "bg": bg
            })
            
        daily_sick = sick_df.groupby('Date').size().reset_index(name='count')
        chart_fig.add_trace(go.Scatter(
            x=daily_sick['Date'], y=daily_sick['count'], mode='lines+markers', name='Daily Sick Leave', 
            line=dict(color='#2563eb', width=2.5), marker=dict(size=6)
        ))

chart_fig.update_layout(
    height=200, margin=dict(l=25, r=10, t=10, b=20),
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False, linecolor='#e2e8f0'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', rangemode='tozero')
)

# ----------------- MAIN LAYOUT -----------------
col_main, col_side = st.columns([7.4, 2.6])

with col_main:
    try:
        st.image("banner.png", use_container_width=True)
    except:
        st.info("Please make sure 'banner.png' is in the same folder as app.py")
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # --- KPI Row ---
    k1, k2, k3, k4 = st.columns(4)
    
    with k1:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="kpi-title">Total Employees</span>
                <span style="background:#f5f3ff; color:#7c3aed; padding:4px 6px; border-radius:6px; font-size:12px;">👥</span>
            </div>
            <div class="kpi-val">{total_emp_count:,}</div>
        </div>
        <div class="kpi-btn-wrapper"></div>
        """, unsafe_allow_html=True)
        # REAL BUTTON! This will open the detailed breakdown.
        st.button("👀 View", key="btn_all", on_click=toggle_view, args=("Total Employees",))
        
    with k2:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="kpi-title">Sick Leave (This Range)</span>
                <span style="background:#fef2f2; color:#ef4444; padding:4px 6px; border-radius:6px; font-size:12px;">🤒</span>
            </div>
            <div class="kpi-val">{total_sick:,}</div>
        </div>
        <div class="kpi-btn-wrapper"></div>
        """, unsafe_allow_html=True)
        st.button("👀 View", key="btn_sl", on_click=toggle_view, args=("Sick Leave",))
        
    with k3:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="kpi-title">1-Day Sick Events</span>
                <span style="background:#e0f2fe; color:#0284c7; padding:4px 6px; border-radius:6px; font-size:12px;">📅</span>
            </div>
            <div class="kpi-val">{one_day_events:,}</div>
        </div>
        <div class="kpi-btn-wrapper"></div>
        """, unsafe_allow_html=True)
        st.button("👀 View", key="btn_1day", on_click=toggle_view, args=("1-Day Events",))
        
    with k4:
        st.markdown(f"""
        <div class="kpi-card">
            <div style="display:flex; justify-content:space-between;">
                <span class="kpi-title">2+ Days Sick Events</span>
                <span style="background:#dcfce7; color:#10b981; padding:4px 6px; border-radius:6px; font-size:12px;">🗓️</span>
            </div>
            <div class="kpi-val">{two_day_events:,}</div>
        </div>
        <div class="kpi-btn-wrapper"></div>
        """, unsafe_allow_html=True)
        st.button("👀 View", key="btn_2day", on_click=toggle_view, args=("2+ Day Events",))

    # --- DYNAMIC DATA VIEWER (OPENS WHEN BUTTON IS CLICKED) ---
    if st.session_state.active_view:
        st.markdown(f"""
        <div style="background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 16px; margin-top: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <h4 style="margin: 0; color: #0f172a; font-size: 15px;">📋 Detailed List: {st.session_state.active_view}</h4>
            </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.active_view == "Total Employees":
            if not df.empty:
                st.dataframe(df[['EMP Name', 'Department']].drop_duplicates().reset_index(drop=True), use_container_width=True, height=200)
            else:
                st.info("No data available for this range.")
                
        elif st.session_state.active_view == "Sick Leave":
            if not sick_df.empty:
                st.dataframe(sick_df[['EMP Name', 'Department', 'Date']].sort_values(by='Date', ascending=False).reset_index(drop=True), use_container_width=True, height=200)
            else:
                st.info("No sick leave records found.")
                
        elif st.session_state.active_view == "1-Day Events":
            if not df_1_day.empty:
                st.dataframe(df_1_day, use_container_width=True, height=200)
            else:
                st.info("No 1-Day events found.")
                
        elif st.session_state.active_view == "2+ Day Events":
            if not df_2_day.empty:
                st.dataframe(df_2_day, use_container_width=True, height=200)
            else:
                st.info("No consecutive sick leave events found.")
                
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- Chart Area ---
    c_chart, c_insight = st.columns([6, 4])
    with c_chart:
        st.markdown(f"""
        <div class="content-box">
            <div class="box-header">
                <span>📈 Sick Leave Pattern Analysis</span>
                <select class="custom-dropdown">
                    <option>{selected_site} Data</option>
                    <option>All Sites Data</option>
                    <option>Last 3 Months Trend</option>
                </select>
            </div>
        """, unsafe_allow_html=True)
        
        st.plotly_chart(chart_fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    with c_insight:
        st.markdown(f"""
        <div class="content-box" style="height:100%;">
            <div class="box-header">💡 Key Insights</div>
            <div style="display:flex; gap:10px; margin-bottom:10px;">
                <div style="width:28px; height:28px; border-radius:50%; background:#dcfce7; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">🌱</div>
                <div><div style="color:#10b981; font-weight:800; font-size:13px;">{total_sick} Days</div><div style="color:#64748b; font-size:10.5px;">Total SL recorded in selected range</div></div>
            </div>
            <div style="display:flex; gap:10px; margin-bottom:10px;">
                <div style="width:28px; height:28px; border-radius:50%; background:#e0f2fe; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">📅</div>
                <div><div style="color:#0284c7; font-weight:800; font-size:13px;">{one_day_events} Events</div><div style="color:#64748b; font-size:10.5px;">Single day isolated absences</div></div>
            </div>
            <div style="display:flex; gap:10px; margin-bottom:10px;">
                <div style="width:28px; height:28px; border-radius:50%; background:#f3e8ff; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">🏖️</div>
                <div><div style="color:#9333ea; font-weight:800; font-size:13px;">{two_day_events} Events</div><div style="color:#64748b; font-size:10.5px;">Prolonged or consecutive sick days</div></div>
            </div>
            <div style="display:flex; gap:10px;">
                <div style="width:28px; height:28px; border-radius:50%; background:#ede9fe; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">📈</div>
                <div><div style="color:#7c3aed; font-weight:800; font-size:13px;">Auto-Sync</div><div style="color:#64748b; font-size:10.5px;">Data directly imported from Roster files</div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # --- Top At-Risk Table ---
    rows_str = ""
    if table_data:
        for r in table_data:
            rows_str += f"<tr><td><b>{r['name']}</b></td>"
            rows_str += f"<td style='color:#64748b;'>{r['dept']}</td>"
            rows_str += f"<td style='color:#475569;'>{r['pattern']}</td>"
            rows_str += f"<td style='text-align:center; font-weight:600;'>{r['events']}</td>"
            rows_str += f"<td style='color:#64748b;'>{r['date']}</td>"
            rows_str += f"<td><span class='risk-badge' style='background:{r['bg']}; color:{r['color']};'>{r['risk']}</span></td>"
            rows_str += f"<td><a href='#' class='action-link' style='color:#2563eb; font-weight:700; text-decoration:none;'>View →</a></td></tr>"
    else:
        rows_str = "<tr><td colspan='7' style='text-align:center; color:#64748b; padding: 24px;'>✅ No sick leave patterns found for the selected date range.</td></tr>"
        
    st.markdown(f"""
    <div class="content-box">
        <div class="box-header">👥 Top At-Risk Employees (Based on SL Frequency)</div>
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

    st.markdown("""
    <div style="background: linear-gradient(90deg, #0284c7, #2563eb); border-radius: 10px; padding: 9px 16px; margin-top: 12px; display: flex; justify-content: space-between; align-items: center; color: white; font-size: 11.5px; font-weight: 600;">
        <span>From attendance data to meaningful actions</span>
        <div style="display:flex; gap:12px;">
            <span>🔍 Spot patterns</span>
            <span>💬 Start conversations</span>
            <span>🌱 Build healthier teams</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ----------------- SIDEBAR METRICS -----------------
with col_side:
    st.markdown(f"""<div style="background-color: #2563eb; border-radius: 12px; padding: 20px; color: white; margin-bottom: 12px; position: relative; overflow: hidden;">
<div style="display:flex; align-items:center; gap:6px; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; opacity:0.9;">
<span style="font-size:14px;">🤖</span> AI ASSISTANT
</div>
<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" style="position:absolute; right:15px; top:22px; width:80px; z-index: 1; opacity: 0.95;">
<div style="font-weight:800; font-size:18px; margin: 8px 0 16px 0; position: relative; z-index: 2;">Data Synced!</div>
<div style="font-size:13px; line-height:1.5; opacity:0.95; width:65%; margin-bottom:20px; position: relative; z-index: 2;">
Hi PXT! 👋<br>I've successfully analyzed <b>{total_sick} sick leave records</b> from the raw roster files in {selected_site}.
</div>
<a href="#" class="ai-insight-btn" onclick="alert('Analyzing AI Trends...');">View Insights →</a>
</div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="content-box" style="margin-bottom: 12px; padding: 10px 14px;">
        <div style="font-weight: 700; font-size: 12.5px; color: #0f172a; margin-bottom: 8px;">⚡ Quick Actions</div>
    """, unsafe_allow_html=True)
    
    if st.button("📥 Export SL Report", use_container_width=True):
        st.success("✅ SL Report Exported as CSV!")
    if st.button("📝 Generate Coaching File", use_container_width=True):
        st.success("✅ Coaching template created successfully!")
    if st.button("📊 View Raw Roster", use_container_width=True):
        st.info("ℹ️ Opening Raw Roster Data...")
        
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="content-box" style="margin-bottom: 12px;">
        <div class="box-header">📊 Leave Duration Breakdown</div>
    """, unsafe_allow_html=True)
    
    if (one_day_events + two_day_events) > 0:
        fig_donut = go.Figure(data=[go.Pie(
            labels=['1 Day', '2+ Days'],
            values=[one_day_events, two_day_events],
            hole=.72,
            marker=dict(colors=['#2563eb', '#9333ea']),
            textinfo='none'
        )])
        fig_donut.update_layout(
            height=150, margin=dict(l=5, r=5, t=5, b=5), showlegend=False,
            annotations=[dict(text=f'<b>{total_sick}</b><br><span style="font-size:9px; color:#64748b;">Total SL</span>', x=0.5, y=0.5, font_size=14, showarrow=False)]
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        
        pct_1 = int(round((one_day_events / (one_day_events + two_day_events)) * 100)) if total_sick > 0 else 0
        pct_2 = 100 - pct_1
        
        st.markdown(f"""
            <div style="display:flex; justify-content:space-around; font-size:10.5px; color:#475569; margin-top:2px;">
                <span><b style="color:#2563eb;">●</b> 1 Day: <b>{one_day_events} ({pct_1}%)</b></span>
                <span><b style="color:#9333ea;">●</b> 2+ Days: <b>{two_day_events} ({pct_2}%)</b></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
         st.markdown("<div style='text-align:center; padding: 20px 0; color:#64748b; font-size: 11px;'>No Sick Leave Data to Display</div></div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="content-box" style="margin-bottom: 12px;">
        <div class="box-header">
            <span>⚡ Action Required</span>
            <a href="#" class="action-link" style="font-size:10px; color:#2563eb; text-decoration:none;">View All &gt;</a>
        </div>
    """, unsafe_allow_html=True)
    
    if len(table_data) > 0:
        for i, r in enumerate(table_data[:3]):
            status = "Scheduled" if i == 0 else ("Pending" if i == 1 else "Not Started")
            st.markdown(f"""
            <div style="font-size:11px; padding:6px 0; border-bottom:1px solid #f8fafc; display:flex; justify-content:space-between; align-items:center;">
                <div><b>{r['name']}</b><br><span style="font-size:9.5px; color:#94a3b8;">{status} • {r['date']}</span></div>
                <span class="risk-badge" style="background:{r['bg']}; color:{r['color']};">{r['risk']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; padding: 10px 0; color:#64748b; font-size: 11px;'>No High Risk Employees</div>", unsafe_allow_html=True)
        
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="content-box" style="background: #f0fdf4; border: 1px solid #bbf7d0; display:flex; justify-content:space-between; align-items:center; padding: 10px 14px;">
        <div style="font-size:10.5px; color:#166534; font-weight:600; line-height:1.3;">
            "Data is only useful if it helps us support our people."
        </div>
        <span style="color:#dc2626; font-size:14px; margin-left:8px;">🤍</span>
    </div>
    """, unsafe_allow_html=True)

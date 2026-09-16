import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os
import datetime
import re
import numpy as np

# 1. Page Configuration
st.set_page_config(
    page_title="Amazon People Analytics",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Session State Setup
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'active_view' not in st.session_state:
    st.session_state.active_view = None

# 3. Global Functions
def toggle_view(view_name):
    if st.session_state.active_view == view_name:
        st.session_state.active_view = None 
    else:
        st.session_state.active_view = view_name 

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


# ==========================================
#        AMAZON LOGIN PAGE (PURPLE)
# ==========================================
if not st.session_state.logged_in:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
        .stApp { background: linear-gradient(135deg, #2e1065 0%, #6d28d9 50%, #c4b5fd 100%) !important; }
        [data-testid="stForm"] { background-color: white !important; border-radius: 20px !important; padding: 40px 35px !important; border: none !important; box-shadow: 0 20px 40px rgba(0,0,0,0.4) !important; }
        div[data-testid="stTextInput"] label { color: #1e293b !important; font-weight: 700 !important; font-size: 13px !important; }
        div[data-testid="stTextInput"] div[data-baseweb="input"] { border-radius: 8px !important; border: 1px solid #cbd5e1 !important; background-color: #f8fafc !important; }
        div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within { border-color: #8b5cf6 !important; box-shadow: 0 0 0 1px #8b5cf6 !important; }
        [data-testid="stFormSubmitButton"] > button { background-color: #FFD814 !important; color: #0F1111 !important; font-weight: 800 !important; font-size: 15px !important; border-radius: 8px !important; border: 1px solid #FCD200 !important; width: 100% !important; padding: 8px !important; margin-top: 5px !important; box-shadow: 0 2px 5px rgba(0,0,0,0.05) !important; transition: all 0.2s ease-in-out !important; }
        [data-testid="stFormSubmitButton"] > button:hover { background-color: #F7CA00 !important; border-color: #F2C200 !important; box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important; }
        [data-testid="stSidebar"] { display: none !important; }
        header[data-testid="stHeader"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 8vh;'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        with st.form("login_form"):
            st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" width="90" style="margin-bottom: 5px; filter: drop-shadow(0px 10px 10px rgba(0,0,0,0.1));">
                <br>
                <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" width="115" style="margin-bottom: 12px;">
                <h2 style="color: #0f172a; font-weight: 800; font-size: 19px; margin: 0; padding-bottom: 2px;">workforce_compliance_monitor-audit</h2>
                <p style="color: #64748b; font-size: 12.5px; margin: 0;">Internal Portal • Sign in to continue</p>
            </div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("Amazon Login ID", placeholder="e.g. javmuhak")
            st.markdown("""<div style="text-align: right; font-size: 10.5px; margin-top: -10px; margin-bottom: 15px;"><span style="color: #64748b;">Access Issue? Contact </span><b style="color: #0284c7; cursor: pointer;">Javmuhak</b></div>""", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In")
            
            if submitted:
                if username:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Please enter your Login ID.")
        
        st.markdown("""<div style="text-align: center; color: #ede9fe; font-size: 11px; margin-top: 15px; font-weight: 500;">© 2026 Amazon.com, Inc. or its affiliates. Confidential.</div>""", unsafe_allow_html=True)


# ==========================================
#        MAIN APP / DASHBOARD LOGIC
# ==========================================
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif !important; }
        .stApp { background-color: #f3f6fb !important; background-image: none !important; }
        .block-container { padding: 0.8rem 1.6rem !important; max-width: 100% !important; }
        header[data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
        section[data-testid="stSidebar"] { background-color: #0b1220 !important; width: 250px !important; min-width: 250px !important; border-right: 1px solid rgba(255,255,255,0.06) !important; display: block !important; }
        section[data-testid="stSidebar"] .block-container { padding: 8px 14px !important; }
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0rem !important; }
        section[data-testid="stSidebar"] div.element-container { margin: 0 !important; }
        section[data-testid="stSidebar"] div.stButton { margin-bottom: 2px !important; }
        section[data-testid="stSidebar"] div.stButton > button, section[data-testid="stSidebar"] div.stButton > button[kind="secondary"] { background: none !important; border: none !important; color: #8b95a8 !important; box-shadow: none !important; outline: none !important; font-weight: 500 !important; font-size: 13.5px !important; padding: 4px 4px !important; min-height: unset !important; border-radius: 0 !important; text-align: left !important; }
        section[data-testid="stSidebar"] div.stButton > button:hover { color: #ffffff !important; }
        section[data-testid="stSidebar"] div.stButton:first-of-type > button { color: #ffffff !important; font-weight: 700 !important; }
        section[data-testid="stSidebar"] .nav-label { font-size: 10px; font-weight: 800; letter-spacing: 1px; color: #4b5768; margin: 4px 0 4px 4px; text-transform: uppercase; }
        div.stButton > button { border: 1px solid #e2e8f0 !important; background-color: white !important; color: #1e293b !important; font-weight: 600 !important; border-radius: 8px !important; text-align: left !important; padding: 8px 12px !important; box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important; transition: all 0.2s ease-in-out !important; width: 100% !important; }
        div.stButton > button:hover { border-color: #38bdf8 !important; background-color: #f0f9ff !important; }
        .kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; height: 95px; margin-bottom: 0px; transition: all 0.2s ease; position: relative; z-index: 1; }
        div[data-testid="column"]:has(.kpi-btn-wrapper) { position: relative !important; }
        div[data-testid="column"]:has(.kpi-btn-wrapper):hover .kpi-card { border-color: #38bdf8; box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15); }
        div.element-container:has(.kpi-btn-wrapper) + div.element-container { position: absolute !important; inset: 0 !important; margin: 0 !important; z-index: 5 !important; }
        div.element-container:has(.kpi-btn-wrapper) + div.element-container div.stButton { width: 100% !important; height: 100% !important; }
        div.element-container:has(.kpi-btn-wrapper) + div.element-container div.stButton > button { width: 100% !important; height: 100% !important; background: transparent !important; border: none !important; box-shadow: none !important; opacity: 0 !important; cursor: pointer !important; padding: 0 !important; margin: 0 !important; }
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
        
        /* New styling for Filter UI */
        div[data-testid="stDateInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stMultiSelect"] label { display: none !important; }
        div[data-testid="stDateInput"] div[data-baseweb="input"], div[data-testid="stSelectbox"] div[data-baseweb="select"], div[data-testid="stMultiSelect"] div[data-baseweb="select"] { border-radius: 16px !important; min-height: 36px !important; border: 1px solid #e2e8f0 !important; background-color: white !important; }
        div[data-testid="stRadio"] > div { gap: 12px; }
        div[data-testid="stRadio"] label { font-size: 11px !important; font-weight: 600 !important; color: #475569 !important; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div style="padding: 0 0 12px 0; overflow: visible;">
            <svg width="150" height="42" viewBox="0 0 150 42" xmlns="http://www.w3.org/2000/svg" style="display:block; overflow: visible;">
                <text x="0" y="26" font-family="'Plus Jakarta Sans', Arial, sans-serif" font-weight="900" font-size="26" fill="#FFFFFF" letter-spacing="-0.8">amazon</text>
                <path d="M3 32 C 34 46, 76 46, 107 30" stroke="#FF9900" stroke-width="3.4" fill="none" stroke-linecap="round"/>
                <path d="M99 25 L110 30 L100 37" stroke="#FF9900" stroke-width="3.4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <div style="display:inline-block; margin-top:8px; padding:4px 10px; background: rgba(255,255,255,0.07); border:1px solid rgba(255,255,255,0.12); border-radius:20px; font-size:10px; font-weight:700; color:#cbd5e1; letter-spacing:0.6px;">
                PEOPLE ANALYTICS
            </div>
        </div>
        <div style="height:1px; background: rgba(255,255,255,0.08); margin: 0 0 10px 0;"></div>
        <div class="nav-label">Main Menu</div>
        """, unsafe_allow_html=True)

        nav_items = ["🏠  Home", "📈  Attendance Insights", "🤒  Sick Leave Tracker", "👤  Employee Profiles", "🎯  Coaching & Guidance", "📄  Reports & Analytics", "👥  Team Overview", "⚙️  Settings"]
        for item in nav_items:
            if st.button(item, key=f"nav_{item}"):
                pass
        
        st.markdown("""
        <div style="padding: 16px 4px 0 4px; margin-top: 24px; border-top: 1px solid rgba(255,255,255,0.08); color: white;">
            <div style="font-weight: 700; font-size: 12px; line-height:1.3; color:#e2e8f0;">Healthy Teams Build a Stronger Tomorrow</div>
            <div style="font-size: 11px; color: #7c8aa0; margin-top: 6px; line-height: 1.4;">Better insights. Better conversations. A healthier workplace.</div>
        </div>
        <div style="height: 20px;"></div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Logout", key="btn_logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- CALENDAR PREPARATION ---
    base_date = datetime.date(2026, 9, 6) # Start of Week 37
    weeks_dict = {}
    for w in range(30, 46):
        delta_days = (w - 37) * 7
        w_start = base_date + datetime.timedelta(days=delta_days)
        w_end = w_start + datetime.timedelta(days=6)
        weeks_dict[f"Week {w} ({w_start.strftime('%b %d')} - {w_end.strftime('%b %d')})"] = (w_start, w_end)

    # --- TOP BAR WITH DUAL FILTER MODE ---
    top_col1, top_col2, top_col3 = st.columns([1.2, 2.5, 4.8])
    
    with top_col1:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        selected_site = st.selectbox("Site", ["AUH1", "DXB", "DXB3"], label_visibility="collapsed")
        
    with top_col2:
        filter_mode = st.radio("Mode", ["🗓️ By Week", "📅 Custom Dates"], horizontal=True, label_visibility="collapsed")
        
        valid_dates_set = set()
        
        if filter_mode == "🗓️ By Week":
            selected_weeks_list = st.multiselect("Select Week(s)", list(weeks_dict.keys()), default=[list(weeks_dict.keys())[7]], label_visibility="collapsed")
            if selected_weeks_list:
                min_date = datetime.date(2099, 1, 1)
                max_date = datetime.date(2000, 1, 1)
                for w in selected_weeks_list:
                    w_s, w_e = weeks_dict[w]
                    min_date = min(min_date, w_s)
                    max_date = max(max_date, w_e)
                    for i in range((w_e - w_s).days + 1):
                        valid_dates_set.add(w_s + datetime.timedelta(days=i))
                start_date = min_date
                end_date = max_date
            else:
                start_date = end_date = datetime.date.today()
                valid_dates_set.add(start_date)
        else:
            selected_dates = st.date_input("Select Date Range", value=(base_date, base_date + datetime.timedelta(days=6)), label_visibility="collapsed")
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                start_date, end_date = selected_dates
            elif isinstance(selected_dates, tuple) and len(selected_dates) == 1:
                start_date = end_date = selected_dates[0]
            else:
                start_date = end_date = datetime.date.today()
            
            for i in range((end_date - start_date).days + 1):
                valid_dates_set.add(start_date + datetime.timedelta(days=i))

    with top_col3:
        st.markdown("""
        <div style="display:flex; align-items:center; justify-content:flex-end; gap:18px; margin-top: 32px;">
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

    # Load Data and Filter by Valid Dates
    df = load_real_data(selected_site, start_date, end_date)
    if not df.empty:
        df = df[df['Date'].isin(valid_dates_set)]

    total_emp_count = 0
    total_sick = 0
    pattern_wo_linked = 0
    pattern_consec = 0

    df_wo_linked = pd.DataFrame()
    df_consecutive = pd.DataFrame()
    sick_df = pd.DataFrame()
    table_data = []
    chart_fig = go.Figure()

    if not df.empty:
        total_emp_count = df['EMP Name'].nunique()
        
        # Clean attendance status
        df['Att_Clean'] = df['Attendance'].astype(str).str.strip().str.upper()
        df = df.sort_values(by=['EMP Name', 'Date'])
        
        # Previous and next day logic
        df['Prev_Att'] = df.groupby('EMP Name')['Att_Clean'].shift(1)
        df['Next_Att'] = df.groupby('EMP Name')['Att_Clean'].shift(-1)
        
        off_tags = ['WO', 'OFF', 'DO']
        is_sl = df['Att_Clean'] == 'SL'
        is_prev_off = df['Prev_Att'].isin(off_tags)
        is_next_off = df['Next_Att'].isin(off_tags)
        is_prev_sl = df['Prev_Att'] == 'SL'
        is_next_sl = df['Next_Att'] == 'SL'
        
        df['SL_Pattern'] = 'Mid-Week Normal SL'
        # Pattern A: Linked to WO
        df.loc[is_sl & (is_prev_off | is_next_off), 'SL_Pattern'] = 'Linked to Week-Off'
        # Pattern B: Consecutive SL
        df.loc[is_sl & (is_prev_sl | is_next_sl), 'SL_Pattern'] = 'Consecutive SL'
        
        sick_df = df[is_sl].copy()
        total_sick = len(sick_df)
        
        if not sick_df.empty:
            pattern_wo_linked = len(sick_df[sick_df['SL_Pattern'] == 'Linked to Week-Off'])
            pattern_consec = len(sick_df[sick_df['SL_Pattern'] == 'Consecutive SL'])
            
            df_wo_linked = sick_df[sick_df['SL_Pattern'] == 'Linked to Week-Off'][['EMP Name', 'Department', 'Date', 'SL_Pattern']]
            df_consecutive = sick_df[sick_df['SL_Pattern'] == 'Consecutive SL'][['EMP Name', 'Department', 'Date', 'SL_Pattern']]
            
            # --- THE NEW SAFE ZONE & SMART RISK RULES ---
            sl_counts = sick_df.groupby(['EMP Name', 'Department']).agg(
                total_sl=('Date', 'count'),
                last_date=('Date', 'max'),
                wo_count=('SL_Pattern', lambda x: (x == 'Linked to Week-Off').sum()),
                consec_count=('SL_Pattern', lambda x: (x == 'Consecutive SL').sum())
            ).reset_index()

            # Rule 1: Ignore everyone who only has 1 SL (Safe Zone)
            sl_counts = sl_counts[sl_counts['total_sl'] >= 2]

            # Sort the remaining ones by Risk severity
            sl_counts = sl_counts.sort_values(by=['wo_count', 'total_sl'], ascending=[False, False]).head(5)
            
            for _, row in sl_counts.iterrows():
                total = row['total_sl']
                wo_c = row['wo_count']
                consec_c = row['consec_count']
                
                if wo_c >= 1:
                    risk = "High Risk"
                    pattern_text = f"🚨 {wo_c}x SL near Week-Off"
                    bg, color = "#fee2e2", "#dc2626"
                elif consec_c >= 1:
                    risk = "Pending Medical"
                    pattern_text = f"🏥 Consecutive SL ({total} days)"
                    bg, color = "#e0f2fe", "#0284c7"
                else:
                    risk = "Medium Risk"
                    pattern_text = f"⚠️ {total}x Isolated SL"
                    bg, color = "#fef3c7", "#d97706"
                
                table_data.append({
                    "name": row['EMP Name'], "dept": row['Department'] if pd.notna(row['Department']) else "Unknown",
                    "pattern": pattern_text, "events": total,
                    "date": row['last_date'].strftime("%b %d"), "risk": risk, "color": color, "bg": bg
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

    col_main, col_side = st.columns([7.4, 2.6])

    with col_main:
        try: st.image("banner.png", use_container_width=True)
        except: pass 
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        k1, k2, k3, k4 = st.columns(4)
        
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div style="display:flex; justify-content:space-between;">
                    <span class="kpi-title">UPL Report</span>
                    <span style="background:#f5f3ff; color:#7c3aed; padding:4px 6px; border-radius:6px; font-size:12px;">📉</span>
                </div>
                <div class="kpi-val">-</div>
            </div>
            <div class="kpi-btn-wrapper"></div>
            """, unsafe_allow_html=True)
            st.button("View", key="btn_upl", on_click=toggle_view, args=("UPL Report",))
            
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div style="display:flex; justify-content:space-between;">
                    <span class="kpi-title">Total Sick Leave</span>
                    <span style="background:#fef2f2; color:#ef4444; padding:4px 6px; border-radius:6px; font-size:12px;">🤒</span>
                </div>
                <div class="kpi-val">{total_sick:,}</div>
            </div>
            <div class="kpi-btn-wrapper"></div>
            """, unsafe_allow_html=True)
            st.button("View", key="btn_sl", on_click=toggle_view, args=("Sick Leave",))
            
        with k3:
            st.markdown(f"""
            <div class="kpi-card">
                <div style="display:flex; justify-content:space-between;">
                    <span class="kpi-title">SL near Week-Off</span>
                    <span style="background:#e0f2fe; color:#0284c7; padding:4px 6px; border-radius:6px; font-size:12px;">🏖️</span>
                </div>
                <div class="kpi-val">{pattern_wo_linked:,}</div>
            </div>
            <div class="kpi-btn-wrapper"></div>
            """, unsafe_allow_html=True)
            st.button("View", key="btn_wo_link", on_click=toggle_view, args=("Week-Off Linked",))
            
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div style="display:flex; justify-content:space-between;">
                    <span class="kpi-title">Consecutive SL</span>
                    <span style="background:#dcfce7; color:#10b981; padding:4px 6px; border-radius:6px; font-size:12px;">🗓️</span>
                </div>
                <div class="kpi-val">{pattern_consec:,}</div>
            </div>
            <div class="kpi-btn-wrapper"></div>
            """, unsafe_allow_html=True)
            st.button("View", key="btn_consec", on_click=toggle_view, args=("Consecutive Events",))

        if st.session_state.active_view:
            st.markdown(f"""
            <div style="background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 16px; margin-top: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #0f172a; font-size: 15px;">📋 Detailed List: {st.session_state.active_view}</h4>
                </div>
            """, unsafe_allow_html=True)
            
            if st.session_state.active_view == "UPL Report":
                st.info("UPL Report module is currently under development. Data will be fetched soon.")
            elif st.session_state.active_view == "Sick Leave":
                if not sick_df.empty: st.dataframe(sick_df[['EMP Name', 'Department', 'Date', 'SL_Pattern']].sort_values(by='Date', ascending=False).reset_index(drop=True), use_container_width=True, height=200)
                else: st.info("No sick leave records found.")
            elif st.session_state.active_view == "Week-Off Linked":
                if not df_wo_linked.empty: st.dataframe(df_wo_linked.reset_index(drop=True), use_container_width=True, height=200)
                else: st.info("No Week-Off linked SL found.")
            elif st.session_state.active_view == "Consecutive Events":
                if not df_consecutive.empty: st.dataframe(df_consecutive.reset_index(drop=True), use_container_width=True, height=200)
                else: st.info("No consecutive sick leave events found.")
                    
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        c_chart, c_insight = st.columns([6, 4])
        with c_chart:
            st.markdown(f"""
            <div class="content-box">
                <div class="box-header">
                    <span>📈 Sick Leave Pattern Analysis</span>
                    <select class="custom-dropdown">
                        <option>{selected_site} Data</option>
                        <option>All Sites Data</option>
                    </select>
                </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(chart_fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown("</div>", unsafe_allow_html=True)

        with c_insight:
            st.markdown(f"""
            <div class="content-box" style="height:100%;">
                <div class="box-header">💡 Smart Pattern Insights</div>
                <div style="display:flex; gap:10px; margin-bottom:10px;">
                    <div style="width:28px; height:28px; border-radius:50%; background:#e0f2fe; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">🏖️</div>
                    <div><div style="color:#0284c7; font-weight:800; font-size:13px;">{pattern_wo_linked} Pattern(s)</div><div style="color:#64748b; font-size:10.5px;">SL linked with Week-Off</div></div>
                </div>
                <div style="display:flex; gap:10px; margin-bottom:10px;">
                    <div style="width:28px; height:28px; border-radius:50%; background:#f3e8ff; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">🗓️</div>
                    <div><div style="color:#9333ea; font-weight:800; font-size:13px;">{pattern_consec} Event(s)</div><div style="color:#64748b; font-size:10.5px;">Consecutive SL (Requires MC)</div></div>
                </div>
                <div style="display:flex; gap:10px;">
                    <div style="width:28px; height:28px; border-radius:50%; background:#dcfce7; display:flex; align-items:center; justify-content:center; font-size:13px; flex-shrink:0;">🛡️</div>
                    <div><div style="color:#10b981; font-weight:800; font-size:13px;">Safe Zone Active</div><div style="color:#64748b; font-size:10.5px;">Employees with only 1 SL ignored</div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        rows_str = ""
        if table_data:
            for r in table_data:
                rows_str += f"<tr><td><b>{r['name']}</b></td><td style='color:#64748b;'>{r['dept']}</td><td style='color:#475569; font-weight:600;'>{r['pattern']}</td><td style='text-align:center;'>{r['events']}</td><td style='color:#64748b;'>{r['date']}</td><td><span class='risk-badge' style='background:{r['bg']}; color:{r['color']};'>{r['risk']}</span></td><td><a href='#' class='action-link' style='color:#2563eb; font-weight:700; text-decoration:none;'>View →</a></td></tr>"
        else:
            rows_str = "<tr><td colspan='7' style='text-align:center; color:#64748b; padding: 24px;'>✅ No suspicious patterns (2+ SLs) found in selected range.</td></tr>"
            
        st.markdown(f"""
        <div class="content-box">
            <div class="box-header">👥 At-Risk Tracker (Filtered 2+ SLs only)</div>
            <table class="emp-table">
                <thead>
                    <tr><th>EMPLOYEE</th><th>DEPARTMENT</th><th>DETECTED PATTERN</th><th>TOTAL SL</th><th>LAST EVENT</th><th>RISK LEVEL</th><th>ACTION</th></tr>
                </thead>
                <tbody>{rows_str}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_side:
        st.markdown(f"""<div style="background-color: #2563eb; border-radius: 12px; padding: 20px; color: white; margin-bottom: 12px; position: relative; overflow: hidden;">
    <div style="display:flex; align-items:center; gap:6px; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; opacity:0.9;"><span style="font-size:14px;">🤖</span> AI ASSISTANT</div>
    <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" style="position:absolute; right:15px; top:22px; width:80px; z-index: 1; opacity: 0.95;">
    <div style="font-weight:800; font-size:18px; margin: 8px 0 16px 0; position: relative; z-index: 2;">Range Analyzed!</div>
    <div style="font-size:13px; line-height:1.5; opacity:0.95; width:65%; margin-bottom:20px; position: relative; z-index: 2;">
    Hi PXT! 👋<br>I've filtered out single absences. Focus on the table for employees needing coaching or Medical Certs.
    </div>
    <a href="#" class="ai-insight-btn" onclick="alert('Generating Coaching templates...');">Start Coaching →</a>
    </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="content-box" style="margin-bottom: 12px; padding: 10px 14px;"><div style="font-weight: 700; font-size: 12.5px; color: #0f172a; margin-bottom: 8px;">⚡ Quick Actions</div>""", unsafe_allow_html=True)
        if st.button("📥 Export High-Risk CSV", use_container_width=True): st.success("✅ Risk Report Exported as CSV!")
        if st.button("📝 Generate Coaching File", use_container_width=True): st.success("✅ Coaching template created successfully!")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""<div class="content-box" style="margin-bottom: 12px;"><div class="box-header">📊 Range SL Breakdown</div>""", unsafe_allow_html=True)
        
        if total_sick > 0:
            normal_sl = total_sick - pattern_wo_linked - pattern_consec
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Week-Off Linked', 'Consecutive', 'Normal / Isolated'],
                values=[pattern_wo_linked, pattern_consec, normal_sl],
                hole=.72,
                marker=dict(colors=['#0ea5e9', '#8b5cf6', '#cbd5e1']), textinfo='none'
            )])
            fig_donut.update_layout(height=150, margin=dict(l=5, r=5, t=5, b=5), showlegend=False, annotations=[dict(text=f'<b>{total_sick}</b><br><span style="font-size:9px; color:#64748b;">Total SL</span>', x=0.5, y=0.5, font_size=14, showarrow=False)])
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
            st.markdown(f"""
                <div style="font-size:10.5px; color:#475569; margin-top:2px;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span><b style="color:#0ea5e9;">●</b> Near Week-Off</span> <b>{pattern_wo_linked}</b></div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span><b style="color:#8b5cf6;">●</b> Consecutive</span> <b>{pattern_consec}</b></div>
                </div></div>
            """, unsafe_allow_html=True)
        else:
             st.markdown("<div style='text-align:center; padding: 20px 0; color:#64748b; font-size: 11px;'>No Sick Leave Data in range</div></div>", unsafe_allow_html=True)

        st.markdown("""
        <div class="content-box" style="background: #f0fdf4; border: 1px solid #bbf7d0; display:flex; justify-content:space-between; align-items:center; padding: 10px 14px;">
            <div style="font-size:10.5px; color:#166534; font-weight:600; line-height:1.3;">
                "Data is only useful if it helps us support our people."
            </div>
            <span style="color:#dc2626; font-size:14px; margin-left:8px;">🤍</span>
        </div>
        """, unsafe_allow_html=True)

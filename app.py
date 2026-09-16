import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import glob
import os
import datetime
import re
import numpy as np
import base64
import altair as alt
from datetime import timedelta

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
if 'username' not in st.session_state:
    st.session_state.username = "javmuhak"

# 3. Global Functions & Helpers
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

# --- UPL/DWD Report Helper Functions ---
WEEK_ANCHOR_DATE = datetime.date(2026, 8, 2)
WEEK_ANCHOR_NUM = 32

def get_week(d):
    if hasattr(d, 'date'): d = d.date()
    delta = (d - WEEK_ANCHOR_DATE).days
    return WEEK_ANCHOR_NUM + delta // 7

def clean_id(val):
    try: return str(int(float(val))).strip()
    except Exception: return str(val).strip().lower()

def normalize_col(c):
    return (str(c).strip().lower().replace("_", " ").replace("-", " ").replace(".", " "))

def safe_cell(df, row, col):
    try:
        val = df.iloc[row, col]
        if pd.isna(val): return None
        return val
    except Exception: return None

def parse_target_pct(val, default):
    if val is None: return default, False
    try:
        s = str(val).strip().replace('%', '')
        if s == '' or s.lower() in ['nan', 'none']: return default, False
        return round(float(s), 2), True
    except Exception: return default, False

def parse_roster_target_pct(val, default):
    if val is None: return default, False
    try:
        s = str(val).strip().replace('%', '')
        if s == '' or s.lower() in ['nan', 'none']: return default, False
        f = float(s)
        if abs(f) < 1: f *= 100
        return round(f, 2), True
    except Exception: return default, False

def find_column(df, keywords):
    if df.empty: return None
    for col in df.columns:
        nc = normalize_col(col)
        for keyword in keywords:
            if keyword in nc: return col
    return None

def classify_shift_series(shift_series):
    day_tokens = ('ds', 'day', 'morning', '1st', 'am shift', 'general')
    night_tokens = ('ns', 'night', 'evening', '2nd', 'pm shift', 'graveyard')
    def _classify(v):
        s = str(v).strip().lower()
        if not s or s == 'nan': return ''
        if s in ('d', 'am'): return 'DS'
        if s in ('n', 'pm'): return 'NS'
        for tok in day_tokens:
            if tok in s: return 'DS'
        for tok in night_tokens:
            if tok in s: return 'NS'
        return ''
    return shift_series.apply(_classify)

@st.cache_data(show_spinner=False)
def load_permanent_roster():
    roster = pd.DataFrame()
    possible_files = [os.path.join("AUH1", "HC.xlsx"), os.path.join("AUH1", "hc.xlsx"), "HC.xlsx", "hc.xlsx", "HC.XLSX", "hc.XLSX"]
    for filename in possible_files:
        if os.path.exists(filename):
            try:
                roster = pd.read_excel(filename, dtype=str)
                break
            except Exception: continue
    if roster.empty: return roster
    roster.columns = [str(c).strip() for c in roster.columns]
    id_col = None
    for c in roster.columns:
        nc = normalize_col(c)
        if nc in ["id", "employee id", "employee no", "employee number", "psoft id", "psoft", "emp id", "emp no"] or "employee id" in nc or "psoft" in nc:
            id_col = c
            break
    if id_col is None: id_col = roster.columns[0]
    roster["_Clean_ID"] = roster[id_col].apply(clean_id)
    return roster

def get_roster_master(roster):
    if roster.empty: return pd.DataFrame()
    result = roster.copy()
    id_col = None
    for col in result.columns:
        nc = normalize_col(col)
        if "employee id" in nc or "psoft" in nc or nc in ["id", "emp id", "employee no", "employee number"]:
            id_col = col
            break
    if id_col is None: id_col = result.columns[0]
    result["_Clean_ID"] = result[id_col].apply(clean_id)
    return result

roster_df = load_permanent_roster()
roster_master = get_roster_master(roster_df)

@st.cache_data(show_spinner=False)
def process_upl_files(dates_tuple, warehouse, exclude_str, master_roster):
    start_d, end_d = dates_tuple
    exclude_list = [clean_id(x) for x in exclude_str.split(",") if str(x).strip()] if exclude_str else []
    date_list = [start_d + timedelta(days=i) for i in range((end_d - start_d).days + 1)]
    
    upl_files_found, upl_missing_dates, upl_error_dates, upl_shift_fallback_dates = [], [], [], []
    day_wise_data, all_roster_scheduled = [], []
    target_fallback_used = False

    for d in date_list:
        d_str_tag = d.strftime('%d%m%Y')
        possible_upl_names = [
            os.path.join(warehouse, f"DWD-{warehouse}-{d_str_tag}.xlsx"),
            f"DWD-{warehouse}-{d_str_tag}.xlsx",
            os.path.join(warehouse, f"DWD-{warehouse}-{d.strftime('%Y-%m-%d')}.xlsx"),
            f"DWD-{warehouse}-{d.strftime('%Y-%m-%d')}.xlsx"
        ]
        file_path = next((p for p in possible_upl_names if os.path.exists(p)), None)
        if not file_path:
            upl_missing_dates.append(d.strftime("%d-%b-%y"))
            continue
        try:
            with pd.ExcelFile(file_path) as xl:
                dash = xl.parse('Dashboard', dtype=str, header=None)
                rdf = xl.parse('Roster', dtype=str, header=None)

            hc_ds, hc_ns, total_hc = int(dash.iloc[5, 3]), int(dash.iloc[7, 3]), int(dash.iloc[8, 3])
            sl, ab_abwi = int(dash.iloc[27, 7]), int(dash.iloc[27, 8])
            upl_total, pl_total = int(dash.iloc[8, 6]), int(dash.iloc[8, 4])

            upl_target_val, upl_target_found = parse_target_pct(safe_cell(dash, 2, 13), 3.50)
            pl_target_val, pl_target_found = parse_target_pct(safe_cell(dash, 2, 14), 9.67)

            roster_pl_target_val, roster_pl_target_found = parse_roster_target_pct(safe_cell(rdf, 0, 6), pl_target_val)
            if roster_pl_target_found:
                pl_target_val = roster_pl_target_val
                pl_target_found = True

            if not upl_target_found or not pl_target_found:
                target_fallback_used = True

            roster = rdf.iloc[6:].copy()
            roster.columns = [str(c).strip() for c in rdf.iloc[5].tolist()]
            roster['_Clean_ID'] = roster['Psoft No'].apply(clean_id)

            if 'Building' in roster.columns: roster = roster[roster['Building'] == warehouse]
            if exclude_list: roster = roster[~roster['_Clean_ID'].isin(exclude_list)]
            if 'Type' in roster.columns: roster = roster[roster['Type'] == 'Direct']
            if '3P' in roster.columns: roster['3P'] = roster['3P'].replace('QuessCorp', 'Quesscorp')

            scheduled = roster[(roster['Attendance'] != 'OFF') & (roster['Attendance'].notna()) & (roster['Attendance'].astype(str).str.strip() != '')].copy()

            abwi_count = len(scheduled[scheduled['Attendance'] == 'ABWI'])
            ab_count = len(scheduled[scheduled['Attendance'] == 'AB'])
            sl_from_roster = len(scheduled[scheduled['Attendance'] == 'SL'])
            pl_from_roster = len(scheduled[scheduled['Attendance'] == 'PL'])
            upl_from_roster = sl_from_roster + ab_count + abwi_count
            hc_from_roster = len(scheduled)

            shift_col = find_column(scheduled, ['shift', 'schedule', 'work shift', 'shift code'])
            hc_ds_roster = hc_ns_roster = None
            if shift_col:
                shift_class = classify_shift_series(scheduled[shift_col])
                unclassified = int((shift_class == '').sum())
                if unclassified == 0:
                    hc_ds_roster = int((shift_class == 'DS').sum())
                    hc_ns_roster = int((shift_class == 'NS').sum())

            if hc_ds_roster is not None and hc_ds_roster + hc_ns_roster == hc_from_roster:
                day_hc_ds, day_hc_ns, day_shift_source = hc_ds_roster, hc_ns_roster, 'roster'
            else:
                day_hc_ds, day_hc_ns, day_shift_source = hc_ds, hc_ns, 'dashboard'

            if day_shift_source == 'dashboard' and hc_from_roster != total_hc:
                upl_shift_fallback_dates.append(d.strftime('%d-%b-%y'))

            scheduled['_date'] = d.strftime('%d-%b-%y')
            all_roster_scheduled.append(scheduled)

            upl_trend = round((upl_from_roster / hc_from_roster) * 100, 2) if hc_from_roster > 0 else 0
            pl_trend = round((pl_from_roster / hc_from_roster) * 100, 2) if hc_from_roster > 0 else 0

            day_wise_data.append({
                'Date': d.strftime('%d-%b-%y'), 'HC DS': day_hc_ds, 'HC NS': day_hc_ns, 'Total HC': hc_from_roster,
                'SL': sl_from_roster, 'AB': ab_count, 'ABWI': abwi_count, 'Total UPLs': upl_from_roster,
                'Target': f'{upl_target_val:.2f}%', 'Trend': f'{upl_trend:.2f}%', 'Total PLs': pl_from_roster,
                'Target ': f'{pl_target_val:.2f}%', 'Trend ': f'{pl_trend:.2f}%',
                '_UPLTargetNum': upl_target_val, '_PLTargetNum': pl_target_val, '_UPLTrendNum': upl_trend, '_PLTrendNum': pl_trend,
            })
            upl_files_found.append((d, file_path))
        except Exception:
            upl_error_dates.append(d.strftime('%d-%b-%y'))

    return (day_wise_data, all_roster_scheduled, upl_files_found, upl_missing_dates, upl_error_dates, upl_shift_fallback_dates, target_fallback_used)


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
                    st.session_state.username = username
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
        
        /* REDUCED SPACING & PADDING ACROSS THE BOARD */
        .block-container { padding: 0.4rem 1rem !important; max-width: 100% !important; }
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
        
        /* Modern Visible Buttons */
        .btn-view-details button { 
            border: 1px solid #e2e8f0 !important; 
            background-color: white !important; 
            color: #2563eb !important; 
            font-weight: 700 !important; 
            border-radius: 8px !important; 
            text-align: center !important; 
            padding: 4px 12px !important;
            min-height: 28px !important;
            height: 28px !important;
            width: 100% !important;
            font-size: 11.5px !important;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important; 
            transition: all 0.2s ease-in-out !important; 
            margin-top: -6px !important;
        }
        .btn-view-details button:hover { 
            background-color: #f0f9ff !important; 
            border-color: #bfdbfe !important; 
        }
        
        /* Perfectly Aligned Tiny Home Button Style */
        .tiny-home button {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            font-size: 18px !important;
            padding: 0 !important;
            margin-top: 4px !important;
            color: #475569 !important;
            display: flex !important;
        }
        .tiny-home button:hover { background: transparent !important; transform: scale(1.1); color: #2563eb !important; }

        /* KPI Cards */
        .kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; height: 90px; margin-bottom: 4px; position: relative; z-index: 1; }
        .kpi-title { font-size: 11px; font-weight: 600; color: #64748b; }
        .kpi-val { font-size: 22px; font-weight: 800; color: #0f172a; margin-top: 4px; display: flex; align-items: baseline; gap: 6px; }
        
        .content-box { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 14px; }
        .box-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 13px; font-weight: 700; color: #0f172a; }
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
        
        /* Squeezed Filter UI for single line */
        div[data-testid="stDateInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stMultiSelect"] label { display: none !important; }
        div[data-testid="stDateInput"] div[data-baseweb="input"], div[data-testid="stSelectbox"] div[data-baseweb="select"], div[data-testid="stMultiSelect"] div[data-baseweb="select"] { 
            border-radius: 10px !important; 
            min-height: 32px !important; 
            height: 32px !important; 
            border: 1px solid #e2e8f0 !important; 
            background-color: white !important; 
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
            margin-top: 2px !important;
            margin-bottom: 2px !important;
            padding: 2px 6px !important;
            font-size: 11px !important;
        }
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
        
        if st.sidebar.button("🚪 Logout", key="btn_logout"):
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

    # --- PERFECTLY ALIGNED SINGLE-LINE TOP BAR ---
    top_col1, top_col2, top_col3, top_col4 = st.columns([1, 1.2, 3.5, 3])
    
    with top_col1:
        selected_site = st.selectbox("Site", ["AUH1", "DXB", "DXB3"], label_visibility="collapsed")
        
    with top_col2:
        filter_mode = st.selectbox("Mode", ["🗓️ By Week", "📅 Custom Dates"], label_visibility="collapsed")
        
    with top_col3:
        valid_dates_set = set()
        if filter_mode == "🗓️ By Week":
            selected_weeks_list = st.multiselect("Weeks", list(weeks_dict.keys()), default=[list(weeks_dict.keys())[7]], label_visibility="collapsed")
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
            selected_dates = st.date_input("Dates", value=(base_date, base_date + datetime.timedelta(days=6)), label_visibility="collapsed")
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                start_date, end_date = selected_dates
            elif isinstance(selected_dates, tuple) and len(selected_dates) == 1:
                start_date = end_date = selected_dates[0]
            else:
                start_date = end_date = datetime.date.today()
            
            for i in range((end_date - start_date).days + 1):
                valid_dates_set.add(start_date + datetime.timedelta(days=i))

    with top_col4:
        c_home, c_user = st.columns([1.5, 8.5])
        with c_home:
            st.markdown("<div class='tiny-home'>", unsafe_allow_html=True)
            if st.button("🏠", key="home_btn", help="Back to Dashboard"):
                st.session_state.active_view = None
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_user:
            username_display = st.session_state.get('username', 'javmuhak')
            st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:flex-end; gap:8px; height: 32px; margin-top:2px;">
                <div style="font-size:13px; font-weight:800; color:#0f172a; white-space:nowrap;">{username_display}</div>
                <div style="width:26px; height:26px; border-radius:50%; background:#ffffff; border: 1px solid #cbd5e1; display:flex; align-items:center; justify-content:center; overflow: hidden; flex-shrink:0;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/d/de/Amazon_icon.png" style="width: 13px;">
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

    # Load Data and Filter by Valid Dates
    df = load_real_data(selected_site, start_date, end_date)
    if not df.empty:
        df = df[df['Date'].isin(valid_dates_set)]

    # --- PROCESS UPL/DWD DATA GLOBALLY ---
    with st.spinner("Processing Data Metrics..."):
        (
            day_wise_data,
            all_roster_scheduled,
            upl_files_found,
            upl_missing_dates,
            upl_error_dates,
            upl_shift_fallback_dates,
            target_fallback_used
        ) = process_upl_files((start_date, end_date), selected_site, "", roster_master)

    total_upl_metric = sum([r['Total UPLs'] for r in day_wise_data]) if day_wise_data else 0
    total_emp_count = 0
    total_sick = 0
    pattern_wo_linked = 0
    pattern_consec = 0

    df_wo_linked = pd.DataFrame()
    df_consecutive = pd.DataFrame()
    sick_df = pd.DataFrame()
    table_data = []
    chart_fig = go.Figure()

    # --- SHIFT PERFORMANCE CALCULATION (3RD BOX LOGIC) ---
    day_shift_hc = 0
    night_shift_hc = 0
    day_shift_present = 0
    night_shift_present = 0

    if day_wise_data:
        for r in day_wise_data:
            day_shift_hc += r.get('HC DS', 0)
            night_shift_hc += r.get('HC NS', 0)
            
    if all_roster_scheduled:
        combined_sched = pd.concat(all_roster_scheduled, ignore_index=True)
        shift_col_found = find_column(combined_sched, ['shift', 'schedule', 'work shift'])
        if shift_col_found:
            combined_sched['Shift_Class'] = classify_shift_series(combined_sched[shift_col_found])
            ds_df = combined_sched[combined_sched['Shift_Class'] == 'DS']
            ns_df = combined_sched[combined_sched['Shift_Class'] == 'NS']
            
            day_shift_present = len(ds_df[ds_df['Attendance'] == 'P'])
            night_shift_present = len(ns_df[ns_df['Attendance'] == 'P'])

    day_perf_pct = round((day_shift_present / day_shift_hc) * 100, 1) if day_shift_hc > 0 else 0.0
    night_perf_pct = round((night_shift_present / night_shift_hc) * 100, 1) if night_shift_hc > 0 else 0.0
    shift_perf_display = f"DS: {day_perf_pct}% | NS: {night_perf_pct}%"

    if not df.empty:
        total_emp_count = df['EMP Name'].nunique()
        df['Att_Clean'] = df['Attendance'].astype(str).str.strip().str.upper()
        df = df.sort_values(by=['EMP Name', 'Date'])
        
        df['Prev_Att'] = df.groupby('EMP Name')['Att_Clean'].shift(1)
        df['Next_Att'] = df.groupby('EMP Name')['Att_Clean'].shift(-1)
        
        off_tags = ['WO', 'OFF', 'DO']
        is_sl = df['Att_Clean'].isin(['SL', 'ABWI', 'AB', 'NCNS'])
        
        is_prev_off = df['Prev_Att'].isin(off_tags)
        is_next_off = df['Next_Att'].isin(off_tags)
        is_prev_sl = df['Prev_Att'].isin(['SL', 'ABWI', 'AB', 'NCNS'])
        is_next_sl = df['Next_Att'].isin(['SL', 'ABWI', 'AB', 'NCNS'])
        
        df['SL_Pattern'] = 'Mid-Week Normal SL'
        df.loc[is_sl & (is_prev_off | is_next_off), 'SL_Pattern'] = 'Linked to Week-Off'
        df.loc[is_sl & (is_prev_sl | is_next_sl), 'SL_Pattern'] = 'Consecutive SL'
        
        sick_df = df[is_sl].copy()
        total_sick = len(sick_df)
        
        if not sick_df.empty:
            pattern_wo_linked = len(sick_df[sick_df['SL_Pattern'] == 'Linked to Week-Off'])
            pattern_consec = len(sick_df[sick_df['SL_Pattern'] == 'Consecutive SL'])
            
            df_wo_linked = sick_df[sick_df['SL_Pattern'] == 'Linked to Week-Off'][['EMP Name', 'Department', 'Date', 'SL_Pattern']]
            df_consecutive = sick_df[sick_df['SL_Pattern'] == 'Consecutive SL'][['EMP Name', 'Department', 'Date', 'SL_Pattern']]
            
            sl_counts = sick_df.groupby(['EMP Name', 'Department']).agg(
                total_sl=('Date', 'count'),
                last_date=('Date', 'max'),
                wo_count=('SL_Pattern', lambda x: (x == 'Linked to Week-Off').sum()),
                consec_count=('SL_Pattern', lambda x: (x == 'Consecutive SL').sum())
            ).reset_index()

            sl_counts = sl_counts[sl_counts['total_sl'] >= 2]
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
        height=190, margin=dict(l=25, r=10, t=10, b=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, linecolor='#e2e8f0'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', rangemode='tozero')
    )

    # ==========================================
    # ROUTING: SHOW DETAILS PAGE OR MAIN DASHBOARD
    # ==========================================
    if st.session_state.active_view is not None:
        st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            section[data-testid="stSidebar"] { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"<div style='font-size: 16px; font-weight: 700; color: #1e293b; margin-top:-10px; margin-bottom: 16px;'>📋 {st.session_state.active_view} - Detailed View:-</div>", unsafe_allow_html=True)
        
        if st.session_state.active_view == "UPL Report":
            if not upl_files_found:
                st.warning(f"⚠️ No DWD files found for selected dates in {selected_site}. Expected format: DWD-{selected_site}-DDMMYYYY.xlsx")
            else:
                if day_wise_data:
                    day_df = pd.DataFrame(day_wise_data)

                    t_hc_ds = day_df['HC DS'].sum()
                    t_hc_ns = day_df['HC NS'].sum()
                    t_hc = day_df['Total HC'].sum()
                    t_sl = day_df['SL'].sum()
                    t_ab = day_df['AB'].sum()
                    t_abwi = day_df['ABWI'].sum()
                    t_upl = day_df['Total UPLs'].sum()
                    t_pl = day_df['Total PLs'].sum()
                    t_upl_trend = round((t_upl / t_hc) * 100, 2) if t_hc > 0 else 0
                    t_pl_trend = round((t_pl / t_hc) * 100, 2) if t_hc > 0 else 0

                    t_upl_target = round((day_df['_UPLTargetNum'] * day_df['Total HC']).sum() / t_hc, 2) if t_hc > 0 else 3.50
                    t_pl_target = round((day_df['_PLTargetNum'] * day_df['Total HC']).sum() / t_hc, 2) if t_hc > 0 else 9.67

                    week_no = get_week(upl_files_found[0][0])

                    # ===== BOX 1: DAY WISE =====
                    st.markdown("**Day wise:-**")

                    display_day = day_df[['Date','HC DS','HC NS','Total HC','SL','AB','ABWI','Total UPLs','Target','Trend','Total PLs','Target ','Trend ']].copy()
                    total_row_df = pd.DataFrame([{
                        'Date': 'Total', 'HC DS': t_hc_ds, 'HC NS': t_hc_ns, 'Total HC': t_hc,
                        'SL': t_sl, 'AB': t_ab, 'ABWI': t_abwi, 'Total UPLs': t_upl,
                        'Target': f'{t_upl_target:.2f}%', 'Trend': f'{t_upl_trend:.2f}%',
                        'Total PLs': t_pl, 'Target ': f'{t_pl_target:.2f}%', 'Trend ': f'{t_pl_trend:.2f}%',
                    }])
                    display_day = pd.concat([display_day, total_row_df], ignore_index=True)

                    row_upl_targets = list(day_df['_UPLTargetNum']) + [t_upl_target]
                    row_pl_targets = list(day_df['_PLTargetNum']) + [t_pl_target]

                    day_html = '<table style="border-collapse:collapse; width:100%; font-size:11.5px; font-family:sans-serif;">'
                    day_html += '<tr>'
                    hdr_colors = ['#1a237e','#1a237e','#1a237e','#0d47a1','#e65100','#e65100','#e65100','#b71c1c','#4a148c','#2e7d32','#1565c0','#4a148c','#2e7d32']
                    for idx_h, col in enumerate(display_day.columns):
                        day_html += f'<td style="padding:5px 6px; background:{hdr_colors[idx_h]}; color:white; font-weight:700; text-align:center; border:1px solid #ddd; white-space:nowrap;">{col}</td>'
                    day_html += '</tr>'

                    for row_idx in range(len(display_day)):
                        is_total = display_day.iloc[row_idx]['Date'] == 'Total'
                        bg = '#fff9c4' if is_total else ('#f8f9fa' if row_idx % 2 == 0 else '#ffffff')
                        fw = '700' if is_total else '500'
                        day_html += f'<tr style="background:{bg};">'
                        for col in display_day.columns:
                            val = display_day.iloc[row_idx][col]
                            cell_bg = ''
                            cell_color = '#000'
                            if col == 'Trend' and not is_total:
                                try:
                                    trend_val = float(str(val).replace('%',''))
                                    row_target = row_upl_targets[row_idx]
                                    cell_bg = 'background:#ffcdd2;' if trend_val > row_target else 'background:#c8e6c9;'
                                except: pass
                            if col == 'Trend ' and not is_total:
                                try:
                                    trend_val = float(str(val).replace('%',''))
                                    row_target = row_pl_targets[row_idx]
                                    cell_bg = 'background:#ffcdd2;' if trend_val > row_target else 'background:#c8e6c9;'
                                except: pass
                            day_html += f'<td style="padding:4px 6px; text-align:center; border:1px solid #ddd; font-weight:{fw}; {cell_bg} color:{cell_color}; white-space:nowrap;">{val}</td>'
                        day_html += '</tr>'
                    day_html += '</table>'
                    st.markdown(day_html, unsafe_allow_html=True)

                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

                    # ===== BOX 2: AGENCY WISE + BAR CHART =====
                    if all_roster_scheduled:
                        combined_roster = pd.concat(all_roster_scheduled, ignore_index=True)
                        combined_roster['3P'] = combined_roster['3P'].replace('QuessCorp', 'Quesscorp')

                        agency_data = []
                        for agency in sorted(combined_roster['3P'].dropna().unique()):
                            ag = combined_roster[combined_roster['3P'] == agency]
                            ag_hc = len(ag)
                            ag_sl = len(ag[ag['Attendance'] == 'SL'])
                            ag_abwi = len(ag[ag['Attendance'] == 'ABWI'])
                            ag_ab = len(ag[ag['Attendance'] == 'AB'])
                            ag_upl = ag_sl + ag_abwi + ag_ab
                            ag_pl = len(ag[ag['Attendance'] == 'PL'])
                            ag_upl_trend = round((ag_upl / ag_hc) * 100, 2) if ag_hc > 0 else 0
                            ag_pl_trend = round((ag_pl / ag_hc) * 100, 2) if ag_hc > 0 else 0

                            agency_data.append({
                                'Agency': agency, 'Week No': week_no, 'Total HC': ag_hc,
                                'SL': ag_sl, 'ABWI': ag_abwi, 'NCNS': ag_ab, 'Total UPLs': ag_upl,
                                'Trend': f'{ag_upl_trend:.2f}%', 'Total PLs': ag_pl, 'PL Trend': f'{ag_pl_trend:.2f}%',
                            })

                        agency_df_display = pd.DataFrame(agency_data)

                        ag_t_hc = agency_df_display['Total HC'].sum()
                        ag_t_sl = agency_df_display['SL'].sum()
                        ag_t_abwi = agency_df_display['ABWI'].sum()
                        ag_t_ncns = agency_df_display['NCNS'].sum()
                        ag_t_upl = agency_df_display['Total UPLs'].sum()
                        ag_t_pl = agency_df_display['Total PLs'].sum()
                        ag_t_upl_trend = round((ag_t_upl / ag_t_hc) * 100, 2) if ag_t_hc > 0 else 0
                        ag_t_pl_trend = round((ag_t_pl / ag_t_hc) * 100, 2) if ag_t_hc > 0 else 0

                        ag_total_row = pd.DataFrame([{
                            'Agency': 'Total', 'Week No': week_no, 'Total HC': ag_t_hc,
                            'SL': ag_t_sl, 'ABWI': ag_t_abwi, 'NCNS': ag_t_ncns, 'Total UPLs': ag_t_upl,
                            'Trend': f'{ag_t_upl_trend:.2f}%', 'Total PLs': ag_t_pl, 'PL Trend': f'{ag_t_pl_trend:.2f}%',
                        }])
                        agency_df_display = pd.concat([agency_df_display, ag_total_row], ignore_index=True)

                        ag_left, ag_right = st.columns([6.2, 3.8])

                        with ag_left:
                            st.markdown("**Agency wise:-**")
                            ag_html = '<table style="border-collapse:collapse; width:100%; font-size:11.5px; font-family:sans-serif;">'
                            ag_cols = ['Agency','Week No','Total HC','SL','ABWI','NCNS','Total UPLs','Trend','Total PLs','PL Trend']
                            ag_hdr_colors = ['#00695c','#00695c','#0d47a1','#e65100','#e65100','#e65100','#b71c1c','#2e7d32','#1565c0','#2e7d32']
                            ag_html += '<tr>'
                            for idx_h, col in enumerate(ag_cols):
                                ag_html += f'<td style="padding:5px 6px; background:{ag_hdr_colors[idx_h]}; color:white; font-weight:700; text-align:center; border:1px solid #ddd; white-space:nowrap;">{col}</td>'
                            ag_html += '</tr>'
                            for row_idx in range(len(agency_df_display)):
                                is_total = agency_df_display.iloc[row_idx]['Agency'] == 'Total'
                                bg = '#fff9c4' if is_total else ('#f1f8e9' if row_idx % 2 == 0 else '#ffffff')
                                fw = '700' if is_total else '500'
                                ag_html += f'<tr style="background:{bg};">'
                                for col in ag_cols:
                                    val = agency_df_display.iloc[row_idx][col]
                                    cell_bg = ''
                                    if col == 'Trend' and not is_total:
                                        try:
                                            tv = float(str(val).replace('%',''))
                                            cell_bg = 'background:#ffcdd2;' if tv > 3.50 else 'background:#c8e6c9;'
                                        except: pass
                                    if col == 'PL Trend' and not is_total:
                                        try:
                                            tv = float(str(val).replace('%',''))
                                            cell_bg = 'background:#ffcdd2;' if tv > 7.16 else 'background:#c8e6c9;'
                                        except: pass
                                    ag_html += f'<td style="padding:4px 6px; text-align:center; border:1px solid #ddd; font-weight:{fw}; {cell_bg} white-space:nowrap;">{val}</td>'
                                ag_html += '</tr>'
                            ag_html += '</table>'
                            st.markdown(ag_html, unsafe_allow_html=True)

                        with ag_right:
                            st.markdown("**📊 Agency UPL Share**")
                            chart_data = agency_df_display[agency_df_display['Agency'] != 'Total'][['Agency', 'Total UPLs']].copy()
                            chart_data = chart_data.sort_values('Total UPLs', ascending=False).reset_index(drop=True)

                            gradient_colors = ['#b71c1c', '#e53935', '#f57c00', '#fdd835', '#81c784', '#2e7d32']
                            num_bars = len(chart_data)
                            bar_colors = gradient_colors[:num_bars] if num_bars <= len(gradient_colors) else gradient_colors
                            chart_data['Color'] = bar_colors[:num_bars]
                            agency_order = chart_data['Agency'].tolist()

                            bar_chart = alt.Chart(chart_data).mark_bar(
                                cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=24,
                            ).encode(
                                x=alt.X('Agency:N', sort=agency_order, axis=alt.Axis(labelAngle=-45, labelFontSize=10, title=None)),
                                y=alt.Y('Total UPLs:Q', title='Total UPL Count', axis=alt.Axis(tickCount=5)),
                                color=alt.Color('Agency:N', legend=None, scale=alt.Scale(domain=agency_order, range=bar_colors[:num_bars])),
                                tooltip=['Agency', 'Total UPLs']
                            ).properties(height=200)
                            st.altair_chart(bar_chart, use_container_width=True)

                    # ===== BOX 3: INDEPENDENT MULTI-WEEK WOW SUMMARY (7:3 RATIO) =====
                    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
                    st.markdown("**Summary:-**")

                    # INDEPENDENT 4-WEEK FETCHING LOGIC FOR SUMMARY
                    all_available_files = sorted(glob.glob(f"*{selected_site}*.xlsx"))
                    summary_weeks_dict = {}
                    for f in all_available_files:
                        m = re.search(r'(\d{8})', f)
                        if m:
                            try:
                                f_date = datetime.datetime.strptime(m.group(1), "%d%m%Y").date()
                                wk_num = get_week(f_date)
                                if wk_num not in summary_weeks_dict:
                                    summary_weeks_dict[wk_num] = []
                                summary_weeks_dict[wk_num].append((f_date, f))
                            except: pass

                    sorted_summary_weeks = sorted(summary_weeks_dict.keys())[-4:] # Last 4 active weeks automatically

                    sum_left, sum_right = st.columns([7, 3])

                    with sum_left:
                        if sorted_summary_weeks:
                            tbl = '<table style="border-collapse:collapse; width:100%; font-size:11.5px; font-family:sans-serif;">'
                            tbl += '<tr>'
                            tbl += '<td style="padding:5px; background:#1a237e; color:white; font-weight:700; text-align:center; border:1px solid #ddd;">Site</td>'
                            tbl += '<td style="padding:5px; background:#1a237e; color:white; font-weight:700; text-align:center; border:1px solid #ddd;">Leave Type</td>'
                            tbl += '<td style="padding:5px; background:#1a237e; color:white; font-weight:700; text-align:center; border:1px solid #ddd;">Metric</td>'
                            for wk in sorted_summary_weeks:
                                tbl += f'<td style="padding:5px; background:#9b59b6; color:white; font-weight:700; text-align:center; border:1px solid #ddd;">Week {wk}</td>'
                            tbl += '</tr>'

                            # Calculate aggregates per week dynamically
                            w_metrics = {}
                            for wk in sorted_summary_weeks:
                                w_hc, w_upl, w_pl, w_upl_tsum, w_pl_tsum = 0, 0, 0, 0.0, 0.0
                                for d_dt, f_path in summary_weeks_dict[wk]:
                                    try:
                                        with pd.ExcelFile(f_path) as xl:
                                            dash = xl.parse('Dashboard', dtype=str, header=None)
                                            rdf = xl.parse('Roster', dtype=str, header=None)
                                        tot_hc = int(dash.iloc[8, 3])
                                        upl_val = int(dash.iloc[8, 6])
                                        pl_val = int(dash.iloc[8, 4])
                                        ut, _ = parse_target_pct(safe_cell(dash, 2, 13), 3.50)
                                        pt, _ = parse_target_pct(safe_cell(dash, 2, 14), 9.67)
                                        w_hc += tot_hc
                                        w_upl += upl_val
                                        w_pl += pl_val
                                        w_upl_tsum += ut * tot_hc
                                        w_pl_tsum += pt * tot_hc
                                    except: pass
                                w_metrics[wk] = {
                                    'hc': w_hc, 'upl': w_upl, 'pl': w_pl,
                                    'upl_t': round(w_upl_tsum / w_hc, 2) if w_hc > 0 else 3.50,
                                    'pl_t': round(w_pl_tsum / w_hc, 2) if w_hc > 0 else 9.67,
                                    'upl_a': round((w_upl / w_hc) * 100, 2) if w_hc > 0 else 0.0,
                                    'pl_a': round((w_pl / w_hc) * 100, 2) if w_hc > 0 else 0.0,
                                }

                            # UPL Target Row
                            tbl += '<tr>'
                            tbl += f'<td rowspan="4" style="padding:5px; background:#c8e6c9; color:#000; font-weight:800; font-size:12px; text-align:center; border:1px solid #ddd; vertical-align:middle;">{selected_site}</td>'
                            tbl += '<td rowspan="2" style="padding:5px; background:#fde0d0; color:#000; font-weight:700; text-align:center; border:1px solid #ddd; vertical-align:middle;">Unplanned Leave (UPL)</td>'
                            tbl += '<td style="padding:5px; background:#2e7d32; color:white; font-weight:700; text-align:center; border:1px solid #ddd;">Target</td>'
                            for wk in sorted_summary_weeks:
                                tbl += f'<td style="padding:5px; background:#ffffff; text-align:center; border:1px solid #ddd; font-weight:700;">{w_metrics[wk]["upl_t"]:.2f}%</td>'
                            tbl += '</tr>'

                            # UPL Actual Row
                            tbl += '<tr>'
                            tbl += '<td style="padding:5px; background:#f1c40f; color:#000; font-weight:700; text-align:center; border:1px solid #ddd;">Actual</td>'
                            for wk in sorted_summary_weeks:
                                act = w_metrics[wk]["upl_a"]
                                tgt = w_metrics[wk]["upl_t"]
                                cell_bg = 'background:#ffcdd2;' if act > tgt else 'background:#c8e6c9;'
                                tbl += f'<td style="padding:5px; {cell_bg} text-align:center; border:1px solid #ddd; font-weight:700;">{act:.2f}%</td>'
                            tbl += '</tr>'

                            # PL Target Row
                            tbl += '<tr>'
                            tbl += '<td rowspan="2" style="padding:5px; background:#e0f7fa; color:#000; font-weight:700; text-align:center; border:1px solid #ddd; vertical-align:middle;">Planned Leave (PL)</td>'
                            tbl += '<td style="padding:5px; background:#2e7d32; color:white; font-weight:700; text-align:center; border:1px solid #ddd;">Target</td>'
                            for wk in sorted_summary_weeks:
                                tbl += f'<td style="padding:5px; background:#ffffff; text-align:center; border:1px solid #ddd; font-weight:700;">{w_metrics[wk]["pl_t"]:.2f}%</td>'
                            tbl += '</tr>'

                            # PL Actual Row
                            tbl += '<tr>'
                            tbl += '<td style="padding:5px; background:#f1c40f; color:#000; font-weight:700; text-align:center; border:1px solid #ddd;">Actual</td>'
                            for wk in sorted_summary_weeks:
                                act = w_metrics[wk]["pl_a"]
                                tgt = w_metrics[wk]["pl_t"]
                                cell_bg = 'background:#ffcdd2;' if act > tgt else 'background:#c8e6c9;'
                                tbl += f'<td style="padding:5px; {cell_bg} text-align:center; border:1px solid #ddd; font-weight:700;">{act:.2f}%</td>'
                            tbl += '</tr>'

                            tbl += '</table>'
                            st.markdown(tbl, unsafe_allow_html=True)
                        else:
                            st.info("No multi-week files found for summary comparison.")

                    with sum_right:
                        st.markdown("**📊 PL vs UPL Share**")
                        t_sum_upl = sum([w_metrics[wk]['upl'] for wk in sorted_summary_weeks]) if sorted_summary_weeks else 0
                        t_sum_pl = sum([w_metrics[wk]['pl'] for wk in sorted_summary_weeks]) if sorted_summary_weeks else 0
                        
                        if t_sum_upl + t_sum_pl > 0:
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=['Unplanned (UPL)', 'Planned (PL)'],
                                values=[t_sum_upl, t_sum_pl],
                                hole=0.6,
                                marker=dict(colors=['#f97316', '#3b82f6']),
                                textinfo='percent',
                                hoverinfo='label+value'
                            )])
                            fig_pie.update_layout(
                                height=180, 
                                margin=dict(l=10, r=10, t=10, b=10),
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)',
                                showlegend=True,
                                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
                            )
                            st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
                        else:
                            st.info("No Leave Data available.")

        elif st.session_state.active_view == "Sick Leave":
            if not sick_df.empty: st.dataframe(sick_df[['EMP Name', 'Department', 'Date', 'SL_Pattern']].sort_values(by='Date', ascending=False).reset_index(drop=True), use_container_width=True, height=400)
            else: st.info("No sick leave records found.")
        elif st.session_state.active_view == "Sick Leave Pattern":
            st.markdown("### 🔍 Sick Leave Pattern Analysis (Near Week-Off & Consecutive)")
            tab1, tab2 = st.tabs(["🏖️ SL Near Week-Off", "🗓️ Consecutive SL Events"])
            
            with tab1:
                if not df_wo_linked.empty:
                    st.dataframe(df_wo_linked.reset_index(drop=True), use_container_width=True, height=400)
                else:
                    st.info("No Week-Off linked SL found for selected range.")
            with tab2:
                if not df_consecutive.empty:
                    st.dataframe(df_consecutive.reset_index(drop=True), use_container_width=True, height=400)
                else:
                    st.info("No consecutive sick leave events found for selected range.")

    # ==========================================
    # MAIN DASHBOARD VIEW (WHEN NO DETAIL IS SELECTED)
    # ==========================================
    else:
        col_main, col_side = st.columns([7.4, 2.6])

        with col_main:
            try: st.image("banner.png", use_container_width=True)
            except: pass 
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

            k1, k2, k3, k4 = st.columns(4)
            
            with k1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="kpi-title">UPL Report</span>
                        <span style="background:#f5f3ff; color:#7c3aed; padding:4px 6px; border-radius:6px; font-size:12px;">📉</span>
                    </div>
                    <div class="kpi-val">{total_upl_metric:,}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div class='btn-view-details'>", unsafe_allow_html=True)
                st.button("👁️ View Details", key="btn_upl", on_click=toggle_view, args=("UPL Report",), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with k2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="kpi-title">Total Sick Leave</span>
                        <span style="background:#fef2f2; color:#ef4444; padding:4px 6px; border-radius:6px; font-size:12px;">🤒</span>
                    </div>
                    <div class="kpi-val">{total_sick:,}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div class='btn-view-details'>", unsafe_allow_html=True)
                st.button("👁️ View Details", key="btn_sl", on_click=toggle_view, args=("Sick Leave",), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with k3:
                # 3RD BOX: SHIFT PERFORMANCE BREAKDOWN (WITH DEDICATED VIEW)
                st.markdown(f"""
                <div class="kpi-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="kpi-title">Shift Performance Breakdown</span>
                        <span style="background:#e0f2fe; color:#0284c7; padding:4px 6px; border-radius:6px; font-size:12px;">⚡</span>
                    </div>
                    <div style="font-size: 14px; font-weight: 800; color: #0f172a; margin-top: 6px; line-height: 1.2;">{shift_perf_display}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div class='btn-view-details'>", unsafe_allow_html=True)
                st.button("👁️ View Details", key="btn_shift_perf", on_click=toggle_view, args=("UPL Report",), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with k4:
                # 4TH BOX: SICK LEAVE PATTERN
                st.markdown(f"""
                <div class="kpi-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="kpi-title">Sick Leave Pattern</span>
                        <span style="background:#dcfce7; color:#10b981; padding:4px 6px; border-radius:6px; font-size:12px;">🗓️</span>
                    </div>
                    <div class="kpi-val">{pattern_wo_linked + pattern_consec:,}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div class='btn-view-details'>", unsafe_allow_html=True)
                st.button("👁️ View Details", key="btn_sl_pattern", on_click=toggle_view, args=("Sick Leave Pattern",), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

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

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            rows_str = ""
            if table_data:
                for r in table_data:
                    rows_str += f"<tr><td><b>{r['name']}</b></td><td style='color:#64748b;'>{r['dept']}</td><td style='color:#475569; font-weight:600;'>{r['pattern']}</td><td style='text-align:center;'>{r['events']}</td><td style='color:#64748b;'>{r['date']}</td><td><span class='risk-badge' style='background:{r['bg']}; color:{r['color']};'>{r['risk']}</span></td><td><a href='#' class='action-link' style='color:#2563eb; font-weight:700; text-decoration:none;'>View →</a></td></tr>"
            else:
                rows_str = "<tr><td colspan='7' style='text-align:center; color:#64748b; padding: 20px;'>✅ No suspicious patterns (2+ SLs) found in selected range.</td></tr>"
                
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
            st.markdown(f"""<div style="background-color: #2563eb; border-radius: 12px; padding: 18px; color: white; margin-bottom: 10px; position: relative; overflow: hidden;">
        <div style="display:flex; align-items:center; gap:6px; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; opacity:0.9;"><span style="font-size:14px;">🤖</span> AI ASSISTANT</div>
        <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" style="position:absolute; right:12px; top:18px; width:75px; z-index: 1; opacity: 0.95;">
        <div style="font-weight:800; font-size:17px; margin: 6px 0 12px 0; position: relative; z-index: 2;">Range Analyzed!</div>
        <div style="font-size:12.5px; line-height:1.4; opacity:0.95; width:65%; margin-bottom:16px; position: relative; z-index: 2;">
        Hi PXT! 👋<br>I've filtered out single absences. Focus on the table for employees needing coaching or Medical Certs.
        </div>
        <a href="#" class="ai-insight-btn" onclick="alert('Generating Coaching templates...');">Start Coaching →</a>
        </div>""", unsafe_allow_html=True)

            st.markdown("""<div class="content-box" style="margin-bottom: 10px; padding: 10px 14px;"><div style="font-weight: 700; font-size: 12.5px; color: #0f172a; margin-bottom: 6px;">⚡ Quick Actions</div>""", unsafe_allow_html=True)
            if st.button("📥 Export High-Risk CSV", use_container_width=True): st.success("✅ Risk Report Exported as CSV!")
            if st.button("📝 Generate Coaching File", use_container_width=True): st.success("✅ Coaching template created successfully!")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("""<div class="content-box" style="margin-bottom: 10px;"><div class="box-header">📊 Range SL Breakdown</div>""", unsafe_allow_html=True)
            
            if total_sick > 0:
                normal_sl = total_sick - pattern_wo_linked - pattern_consec
                fig_donut = go.Figure(data=[go.Pie(
                    labels=['Week-Off Linked', 'Consecutive', 'Normal / Isolated'],
                    values=[pattern_wo_linked, pattern_consec, normal_sl],
                    hole=.72,
                    marker=dict(colors=['#0ea5e9', '#8b5cf6', '#cbd5e1']), textinfo='none'
                )])
                fig_donut.update_layout(height=140, margin=dict(l=5, r=5, t=5, b=5), showlegend=False, annotations=[dict(text=f'<b>{total_sick}</b><br><span style="font-size:9px; color:#64748b;">Total SL</span>', x=0.5, y=0.5, font_size=14, showarrow=False)])
                st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
                st.markdown(f"""
                    <div style="font-size:10.5px; color:#475569; margin-top:2px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span><b style="color:#0ea5e9;">●</b> Near Week-Off</span> <b>{pattern_wo_linked}</b></div>
                        <div style="display:flex; justify-content:space-between; margin-bottom:3px;"><span><b style="color:#8b5cf6;">●</b> Consecutive</span> <b>{pattern_consec}</b></div>
                    </div></div>
                """, unsafe_allow_html=True)
            else:
                 st.markdown("<div style='text-align:center; padding: 15px 0; color:#64748b; font-size: 11px;'>No Sick Leave Data in range</div></div>", unsafe_allow_html=True)

            st.markdown("""
            <div class="content-box" style="background: #f0fdf4; border: 1px solid #bbf7d0; display:flex; justify-content:space-between; align-items:center; padding: 10px 14px;">
                <div style="font-size:10.5px; color:#166534; font-weight:600; line-height:1.3;">
                    "Data is only useful if it helps us support our people."
                </div>
                <span style="color:#dc2626; font-size:14px; margin-left:8px;">🤍</span>
            </div>
            """, unsafe_allow_html=True)

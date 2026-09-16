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

# 3. Global Functions & Helpers
def toggle_view(view_name):
    if st.session_state.active_view == view_name:
        st.session_state.active_view = None 
    else:
        st.session_state.active_view = view_name 

def go_back():
    st.session_state.active_view = None

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
        
        /* Modern Visible Buttons */
        .btn-view-details button { 
            border: 1px solid #e2e8f0 !important; 
            background-color: white !important; 
            color: #2563eb !important; 
            font-weight: 700 !important; 
            border-radius: 8px !important; 
            text-align: center !important; 
            padding: 4px 12px !important;
            min-height: 30px !important;
            height: 30px !important;
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
        
        /* Back Button Style */
        .btn-back button {
            background-color: #0f172a !important;
            color: #ffffff !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            padding: 6px 16px !important;
            border: none !important;
            margin-bottom: 15px !important;
            transition: all 0.2s ease;
        }
        .btn-back button:hover { background-color: #1e293b !important; transform: translateX(-2px); }

        /* KPI Cards */
        .kpi-card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; height: 95px; margin-bottom: 4px; position: relative; z-index: 1; }
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
        
        /* Squeezed Filter UI for single line */
        div[data-testid="stDateInput"] label, div[data-testid="stSelectbox"] label, div[data-testid="stMultiSelect"] label { display: none !important; }
        div[data-testid="stDateInput"] div[data-baseweb="input"], div[data-testid="stSelectbox"] div[data-baseweb="select"], div[data-testid="stMultiSelect"] div[data-baseweb="select"] { 
            border-radius: 10px !important; 
            min-height: 34px !important; 
            height: 34px !important; 
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

    # --- SLEEK SINGLE-LINE TOP BAR ---
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
        st.markdown("""
        <div style="display:flex; align-items:center; justify-content:flex-end; gap:16px; margin-top: 0px; height: 34px;">
            <span style="font-size:15px; cursor:pointer;" title="Search Employee">🔍</span>
            <span style="font-size:11.5px; color:#64748b; font-weight:700; cursor:pointer;">⚡ Filters</span>
            <span style="font-size:15px; cursor:pointer;">🔔</span>
            <div style="display:flex; align-items:center; gap:8px;">
                <div style="font-size:13px; font-weight:800; color:#0f172a;">javmuhak</div>
                <div style="width:28px; height:28px; border-radius:50%; background:#ffffff; border: 1px solid #cbd5e1; display:flex; align-items:center; justify-content:center; overflow: hidden;">
                    <img src="https://upload.wikimedia.org/wikipedia/commons/d/de/Amazon_icon.png" style="width: 14px;">
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    # Load Data and Filter by Valid Dates
    df = load_real_data(selected_site, start_date, end_date)
    if not df.empty:
        df = df[df['Date'].isin(valid_dates_set)]

    # --- PROCESS UPL REPORT DATA (DWD FILES) GLOBALLY ---
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

    if not df.empty:
        total_emp_count = df['EMP Name'].nunique()
        df['Att_Clean'] = df['Attendance'].astype(str).str.strip().str.upper()
        df = df.sort_values(by=['EMP Name', 'Date'])
        
        df['Prev_Att'] = df.groupby('EMP Name')['Att_Clean'].shift(1)
        df['Next_Att'] = df.groupby('EMP Name')['Att_Clean'].shift(-1)
        
        off_tags = ['WO', 'OFF', 'DO']
        is_sl = df['Att_Clean'] == 'SL'
        is_prev_off = df['Prev_Att'].isin(off_tags)
        is_next_off = df['Next_Att'].isin(off_tags)
        is_prev_sl = df['Prev_Att'] == 'SL'
        is_next_sl = df['Next_Att'] == 'SL'
        
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
        height=200, margin=dict(l=25, r=10, t=10, b=20),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, linecolor='#e2e8f0'), yaxis=dict(showgrid=True, gridcolor='#f1f5f9', rangemode='tozero')
    )

    # ==========================================
    # ROUTING: SHOW DETAILS PAGE OR MAIN DASHBOARD
    # ==========================================
    if st.session_state.active_view is not None:
        # --- AUTO HIDE SIDEBAR ON DETAILS VIEW FOR FULL SCREEN WIDTH ---
        st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            section[data-testid="stSidebar"] { display: none !important; }
        </style>
        """, unsafe_allow_html=True)

        # --- FULL WIDTH DETAILED PAGE ---
        st.markdown("<div class='btn-back'>", unsafe_allow_html=True)
        st.button("⬅️ Back to Dashboard", on_click=go_back)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background-color: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <h2 style="margin-top: 0; color: #0f172a; font-weight: 800; font-size: 22px;">📋 {st.session_state.active_view} - Detailed View</h2>
            <hr style="border:none; border-top:1px solid #e2e8f0; margin-bottom: 24px;">
        """, unsafe_allow_html=True)
        
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

                    day_html = '<table style="border-collapse:collapse; width:100%; font-size:12px; font-family:sans-serif;">'
                    day_html += '<tr>'
                    hdr_colors = ['#1a237e','#1a237e','#1a237e','#0d47a1','#e65100','#e65100','#e65100','#b71c1c','#4a148c','#2e7d32','#1565c0','#4a148c','#2e7d32']
                    for idx_h, col in enumerate(display_day.columns):
                        day_html += f'<td style="padding:8px 10px; background:{hdr_colors[idx_h]}; color:white; font-weight:700; text-align:center; border:1px solid #ddd; white-space:nowrap;">{col}</td>'
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
                            day_html += f'<td style="padding:6px 10px; text-align:center; border:1px solid #ddd; font-weight:{fw}; {cell_bg} color:{cell_color}; white-space:nowrap;">{val}</td>'
                        day_html += '</tr>'
                    day_html += '</table>'
                    st.markdown(day_html, unsafe_allow_html=True)

                    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

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

                        ag_left, ag_right = st.columns([5.5, 4.5])

                        with ag_left:
                            st.markdown("**Agency wise:-**")
                            ag_html = '<table style="border-collapse:collapse; width:100%; font-size:12px; font-family:sans-serif;">'
                            ag_cols = ['Agency','Week No','Total HC','SL','ABWI','NCNS','Total UPLs','Trend','Total PLs','PL Trend']
                            ag_hdr_colors = ['#00695c','#00695c','#0d47a1','#e65100','#e65100','#e65100','#b71c1c','#2e7d32','#1565c0','#2e7d32']
                            ag_html += '<tr>'
                            for idx_h, col in enumerate(ag_cols):
                                ag_html += f'<td style="padding:8px 6px; background:{ag_hdr_colors[idx_h]}; color:white; font-weight:700; text-align:center; border:1px solid #ddd; white-space:nowrap;">{col}</td>'
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
                                    ag_html += f'<td style="padding:6px; text-align:center; border:1px solid #ddd; font-weight:{fw}; {cell_bg} white-space:nowrap;">{val}</td>'
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
                                cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=28,
                            ).encode(
                                x=alt.X('Agency:N', sort=agency_order, axis=alt.Axis(labelAngle=-45, labelFontSize=11)),
                                y=alt.Y('Total UPLs:Q', title='Total UPL Count'),
                                color=alt.Color('Agency:N', legend=None, scale=alt.Scale(domain=agency_order, range=bar_colors[:num_bars])),
                                tooltip=['Agency', 'Total UPLs']
                            ).properties(height=340)
                            st.altair_chart(bar_chart, use_container_width=True)

                    # ===== BOX 3: SUMMARY + TREND CHART =====
                    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
                    st.markdown("**Summary:-**")

                    weeks_summary = {}
                    for d, fname in upl_files_found:
                        wk = get_week(d)
                        if wk not in weeks_summary:
                            weeks_summary[wk] = {'hc': 0, 'upl': 0, 'pl': 0, 'upl_target_wsum': 0.0, 'pl_target_wsum': 0.0}
                    for row in day_wise_data:
                        row_date_str = row['Date']
                        row_date = None
                        for d, fname in upl_files_found:
                            if d.strftime('%d-%b-%y') == row_date_str:
                                row_date = d
                                break
                        if row_date:
                            wk = get_week(row_date)
                            weeks_summary[wk]['hc'] += row['Total HC']
                            weeks_summary[wk]['upl'] += row['Total UPLs']
                            weeks_summary[wk]['pl'] += row['Total PLs']
                            weeks_summary[wk]['upl_target_wsum'] += row['_UPLTargetNum'] * row['Total HC']
                            weeks_summary[wk]['pl_target_wsum'] += row['_PLTargetNum'] * row['Total HC']

                    sum_left, sum_right = st.columns([5.5, 4.5])

                    with sum_left:
                        sorted_weeks = sorted(weeks_summary.keys())
                        num_weeks = len(sorted_weeks)

                        tbl = '<table style="border-collapse:collapse; width:100%; font-size:13px; font-weight:600; border:2px solid #000;">'
                        tbl += '<tr style="background:#b0c4de; text-align:center;"><td colspan="' + str(num_weeks + 2) + '" style="padding:8px; border:2px solid #000; font-size:15px; font-weight:800;">UPL Trend</td></tr>'
                        tbl += '<tr style="background:#fde0d0; text-align:center;"><td colspan="' + str(num_weeks + 2) + '" style="padding:6px; border:2px solid #000; font-weight:700; font-size:14px;">Unplanned Leave</td></tr>'
                        tbl += '<tr style="text-align:center;"><td style="padding:8px; border:2px solid #000; background:#c8e6c9; font-weight:700; font-size:14px;" rowspan="3">' + selected_site + '</td>'
                        tbl += '<td style="padding:6px; border:2px solid #000;"></td>'
                        for wk in sorted_weeks:
                            tbl += '<td style="padding:6px 10px; border:2px solid #000; background:#9b59b6; color:white; font-weight:700;">Week ' + str(wk) + '</td>'
                        tbl += '</tr>'
                        tbl += '<tr style="text-align:center;"><td style="padding:7px; border:2px solid #000; font-weight:700;">Target</td>'
                        for wk in sorted_weeks:
                            wk_hc_t = weeks_summary[wk]['hc']
                            wk_upl_target = round(weeks_summary[wk]['upl_target_wsum'] / wk_hc_t, 2) if wk_hc_t > 0 else 3.50
                            tbl += '<td style="padding:7px; border:2px solid #000; background:#2e7d32; color:white; font-weight:700;">' + f'{wk_upl_target:.2f}' + '%</td>'
                        tbl += '</tr>'
                        tbl += '<tr style="text-align:center;"><td style="padding:7px; border:2px solid #000; font-weight:700;">Actual</td>'
                        for wk in sorted_weeks:
                            wk_hc = weeks_summary[wk]['hc']
                            wk_upl = weeks_summary[wk]['upl']
                            wk_upl_trend = round((wk_upl / wk_hc) * 100, 2) if wk_hc > 0 else 0
                            tbl += '<td style="padding:7px; border:2px solid #000; background:#f1c40f; color:#000; font-weight:700;">' + str(wk_upl_trend) + '%</td>'
                        tbl += '</tr>'
                        
                        tbl += '<tr style="background:#fde0d0; text-align:center;"><td colspan="' + str(num_weeks + 2) + '" style="padding:6px; border:2px solid #000; font-weight:700; font-size:14px;">Planned Leave</td></tr>'
                        tbl += '<tr style="text-align:center;"><td style="padding:8px; border:2px solid #000; background:#c8e6c9; font-weight:700; font-size:14px;" rowspan="3">' + selected_site + '</td>'
                        tbl += '<td style="padding:6px; border:2px solid #000;"></td>'
                        for wk in sorted_weeks:
                            tbl += '<td style="padding:6px 10px; border:2px solid #000; background:#9b59b6; color:white; font-weight:700;">Week ' + str(wk) + '</td>'
                        tbl += '</tr>'
                        tbl += '<tr style="text-align:center;"><td style="padding:7px; border:2px solid #000; font-weight:700;">Target</td>'
                        for wk in sorted_weeks:
                            wk_hc_t = weeks_summary[wk]['hc']
                            wk_pl_target = round(weeks_summary[wk]['pl_target_wsum'] / wk_hc_t, 2) if wk_hc_t > 0 else 9.67
                            tbl += '<td style="padding:7px; border:2px solid #000; background:#2e7d32; color:white; font-weight:700;">' + f'{wk_pl_target:.2f}' + '%</td>'
                        tbl += '</tr>'
                        tbl += '<tr style="text-align:center;"><td style="padding:7px; border:2px solid #000; font-weight:700;">Actual</td>'
                        for wk in sorted_weeks:
                            wk_hc = weeks_summary[wk]['hc']
                            wk_pl = weeks_summary[wk]['pl']
                            wk_pl_trend = round((wk_pl / wk_hc) * 100, 2) if wk_hc > 0 else 0
                            tbl += '<td style="padding:7px; border:2px solid #000; background:#f1c40f; color:#000; font-weight:700;">' + str(wk_pl_trend) + '%</td>'
                        tbl += '</tr>'
                        tbl += '</table>'
                        st.markdown(tbl, unsafe_allow_html=True)

                    with sum_right:
                        if num_weeks == 1:
                            wk = sorted_weeks[0]
                            wk_hc = weeks_summary[wk]['hc']
                            wk_upl_trend = round((weeks_summary[wk]['upl'] / wk_hc) * 100, 2) if wk_hc > 0 else 0
                            wk_pl_trend = round((weeks_summary[wk]['pl'] / wk_hc) * 100, 2) if wk_hc > 0 else 0
                            wk_label = f'Week {wk}'
                            week_order = [' ', wk_label, '  ']
                            chart_rows = []
                            for lbl in week_order:
                                chart_rows.append({'Week': lbl, 'Metric': 'Unplanned Leave', 'Actual %': wk_upl_trend})
                                chart_rows.append({'Week': lbl, 'Metric': 'Planned Leave', 'Actual %': wk_pl_trend})
                            trend_df = pd.DataFrame(chart_rows)
                            label_df = trend_df[trend_df['Week'] == wk_label]
                        else:
                            week_order = [f'Week {wk}' for wk in sorted_weeks]
                            chart_rows = []
                            for wk in sorted_weeks:
                                wk_hc = weeks_summary[wk]['hc']
                                wk_upl_trend = round((weeks_summary[wk]['upl'] / wk_hc) * 100, 2) if wk_hc > 0 else 0
                                wk_pl_trend = round((weeks_summary[wk]['pl'] / wk_hc) * 100, 2) if wk_hc > 0 else 0
                                wk_label = f'Week {wk}'
                                chart_rows.append({'Week': wk_label, 'Metric': 'Unplanned Leave', 'Actual %': wk_upl_trend})
                                chart_rows.append({'Week': wk_label, 'Metric': 'Planned Leave', 'Actual %': wk_pl_trend})
                            trend_df = pd.DataFrame(chart_rows)
                            label_df = trend_df

                        metric_colors = alt.Scale(domain=['Planned Leave', 'Unplanned Leave'], range=['#3b82f6', '#f97316'])

                        base = alt.Chart(trend_df).encode(
                            x=alt.X('Week:N', sort=week_order, title=None, axis=alt.Axis(domain=True, ticks=True, grid=False)),
                        )

                        trend_area = base.mark_area(line={'strokeWidth': 2.5}, opacity=0.35, interpolate='monotone').encode(
                            y=alt.Y('Actual %:Q', title='Actual %', axis=alt.Axis(domain=True, ticks=True, grid=True)),
                            color=alt.Color('Metric:N', scale=metric_colors, legend=alt.Legend(orient='bottom', labelFontSize=11, labelFontWeight='bold', title=None)),
                            detail='Metric:N', tooltip=['Week', 'Metric', 'Actual %']
                        )

                        trend_points = alt.Chart(label_df).mark_point(filled=True, size=70, stroke='white', strokeWidth=1.5).encode(
                            x=alt.X('Week:N', sort=week_order), y=alt.Y('Actual %:Q'), color=alt.Color('Metric:N', scale=metric_colors, legend=None), detail='Metric:N',
                        )

                        trend_labels = alt.Chart(label_df).mark_text(dy=-12, fontSize=10, fontWeight='bold').encode(
                            x=alt.X('Week:N', sort=week_order), y=alt.Y('Actual %:Q'), text=alt.Text('Actual %:Q', format='.2f'), color=alt.Color('Metric:N', scale=metric_colors, legend=None), detail='Metric:N',
                        )

                        st.altair_chart((trend_area + trend_points + trend_labels).properties(height=280), use_container_width=True)

                    if target_fallback_used: st.info("ℹ️ Target column not found in some DWD files — used defaults.")
                    if upl_missing_dates: st.warning(f"⚠️ Missing DWD files for: {', '.join(upl_missing_dates)}")
                    if upl_shift_fallback_dates: st.warning("⚠️ HC DS/NS shown from Dashboard sheet for: " + ', '.join(upl_shift_fallback_dates))
                    if upl_error_dates: st.warning(f"⚠️ Could not read DWD file for: {', '.join(upl_error_dates)}")

        elif st.session_state.active_view == "Sick Leave":
            if not sick_df.empty: st.dataframe(sick_df[['EMP Name', 'Department', 'Date', 'SL_Pattern']].sort_values(by='Date', ascending=False).reset_index(drop=True), use_container_width=True, height=400)
            else: st.info("No sick leave records found.")
        elif st.session_state.active_view == "Week-Off Linked":
            if not df_wo_linked.empty: st.dataframe(df_wo_linked.reset_index(drop=True), use_container_width=True, height=400)
            else: st.info("No Week-Off linked SL found.")
        elif st.session_state.active_view == "Consecutive Events":
            if not df_consecutive.empty: st.dataframe(df_consecutive.reset_index(drop=True), use_container_width=True, height=400)
            else: st.info("No consecutive sick leave events found.")
                
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # MAIN DASHBOARD VIEW (WHEN NO DETAIL IS SELECTED)
    # ==========================================
    else:
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
                st.markdown(f"""
                <div class="kpi-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="kpi-title">SL near Week-Off</span>
                        <span style="background:#e0f2fe; color:#0284c7; padding:4px 6px; border-radius:6px; font-size:12px;">🏖️</span>
                    </div>
                    <div class="kpi-val">{pattern_wo_linked:,}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div class='btn-view-details'>", unsafe_allow_html=True)
                st.button("👁️ View Details", key="btn_wo_link", on_click=toggle_view, args=("Week-Off Linked",), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            with k4:
                st.markdown(f"""
                <div class="kpi-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="kpi-title">Consecutive SL</span>
                        <span style="background:#dcfce7; color:#10b981; padding:4px 6px; border-radius:6px; font-size:12px;">🗓️</span>
                    </div>
                    <div class="kpi-val">{pattern_consec:,}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("<div class='btn-view-details'>", unsafe_allow_html=True)
                st.button("👁️ View Details", key="btn_consec", on_click=toggle_view, args=("Consecutive Events",), use_container_width=True)
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

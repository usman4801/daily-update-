import base64
from datetime import datetime, timedelta
import os
import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from s3_helper import file_exists, read_file_bytes, read_excel_smart, read_excel_file_smart, read_csv_smart, get_s3_status

# Ensure working directory is the app folder
APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(APP_DIR)

# ==========================================================
# WEEK HELPER — Sunday-to-Sunday fixed calendar
# ==========================================================
import datetime as _dt

WEEK_ANCHOR_DATE = _dt.date(2026, 8, 2)
WEEK_ANCHOR_NUM = 32

def get_week(d):
    if hasattr(d, 'date'):
        d = d.date()
    delta = (d - WEEK_ANCHOR_DATE).days
    return WEEK_ANCHOR_NUM + delta // 7

st.set_page_config(
    page_title="Workforce Compliance Monitor",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ==========================================================
# GLOBAL CSS
# ==========================================================
st.markdown(
    """
    <style>
    #MainMenu {visibility:hidden;}
    header {visibility:hidden;}
    footer {visibility:hidden;}
    [data-testid="stToolbar"] {display:none !important;}
    
    .stApp { background-color:#f8fafc; }
    .block-container {
        background:#ffffff !important;
        padding:1rem 1.5rem !important;
        border-radius:14px !important;
        margin-top:0.2rem !important;
        box-shadow:0 6px 20px rgba(0,0,0,0.05) !important;
        border:1px solid #e2e8f0 !important;
        max-width:100% !important;
    }
    .direct-header-img {
        width:100%;
        border-radius:14px;
        margin-bottom:12px;
        box-shadow:0 6px 20px rgba(168,85,247,0.12);
        border:1px solid rgba(216,180,254,0.6);
        display:block;
    }
    .branch-logo { max-height:40px; margin-top:6px; border-radius:6px; object-fit:contain; }

    div.metric-card {
        padding:26px 20px !important;
        border-radius:12px !important;
        color:white !important;
        font-family:sans-serif !important;
        box-shadow:0 6px 16px rgba(0,0,0,0.1) !important;
        cursor:pointer !important;
        min-height: 140px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    div.metric-card:hover {
        transform:translateY(-3px);
        box-shadow:0 10px 20px rgba(0,0,0,0.18);
    }
    .card-blue { background:linear-gradient(135deg,#3b82f6 0%,#1d4ed8 100%); }
    .card-red { background:linear-gradient(135deg,#ef4444 0%,#b91c1c 100%); }
    .card-orange { background:linear-gradient(135deg,#f59e0b 0%,#b45309 100%); }
    .card-purple { background:linear-gradient(135deg,#8b5cf6 0%,#6d28d9 100%); }
    
    div.card-title {
        font-size:15px !important;
        font-weight:700 !important;
        opacity:0.95 !important;
        margin-bottom:8px !important;
        text-transform:uppercase !important;
        letter-spacing:0.6px !important;
    }
    div.card-value { font-size:40px !important; font-weight:900 !important; line-height:1.1 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# HELPERS
# ==========================================================
@st.cache_data(show_spinner=False)
def get_base64_of_bin_file(bin_file):
    try:
        data = read_file_bytes(bin_file)
        if data:
            return base64.b64encode(data).decode()
        return ""
    except Exception:
        return ""

def clean_id(val):
    try:
        return str(int(float(val))).strip()
    except Exception:
        return str(val).strip().lower()

def normalize_col(c):
    return str(c).strip().lower().replace("_", " ").replace("-", " ").replace(".", " ")

def parse_time(time_val):
    if pd.isna(time_val):
        return None
    value = str(time_val).strip()
    if value.lower() in ["nan", "none", "", "nat"]:
        return None
    for fmt in ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"]:
        try:
            return datetime.strptime(value, fmt).time()
        except Exception:
            pass
    return None

# ==========================================================
# HEADER & FILTERS
# ==========================================================
header_paths = ["header_banner.png", os.path.join("AUH1", "header_banner.png")]
header_img_str = ""
for hp in header_paths:
    header_img_str = get_base64_of_bin_file(hp)
    if header_img_str:
        break

if header_img_str:
    st.markdown(f'<img src="data:image/png;base64,{header_img_str}" class="direct-header-img">', unsafe_allow_html=True)

f_col1, f_col2 = st.columns([4, 8])

with f_col1:
    selected_warehouse = st.selectbox("📍 Site", options=["AUH1", "DXB5", "DXB3"])

with f_col2:
    # Default date range set to current week so data loads automatically
    default_start = datetime.today().date() - timedelta(days=6)
    default_end = datetime.today().date()
    selected_dates_range = st.date_input("Select Date Range • Instant Auto-Fetch", value=(default_start, default_end))

# Sidebar Config
seven_hours_default = "205854274, 206247771, 206930332"
manual_7_ids = st.sidebar.text_area("Paste 7-Hour Employee IDs", value=seven_hours_default)
exclude_ids_input = st.sidebar.text_area("Paste IDs to Ignore", value="203160008, 106495539")

if st.sidebar.button("🔄 Refresh Data Now", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# ==========================================================
# DATA LOADING & PROCESSORS
# ==========================================================
@st.cache_data(show_spinner=False, ttl=300)
def load_permanent_roster():
    roster = pd.DataFrame()
    for filename in [os.path.join("AUH1", "HC.xlsx"), "HC.xlsx"]:
        if file_exists(filename):
            try:
                roster = read_excel_smart(filename, dtype=str)
                break
            except Exception:
                continue
    if roster.empty:
        return roster
    roster.columns = [str(c).strip() for c in roster.columns]
    roster["_Clean_ID"] = roster[roster.columns[0]].apply(clean_id)
    return roster

roster_df = load_permanent_roster()

def build_roster_hours_map(roster):
    result = {}
    if roster.empty:
        return result
    for _, row in roster.iterrows():
        cid = clean_id(row.get("_Clean_ID", ""))
        if not cid:
            continue
        row_text = " ".join(str(v).lower() for v in row.tolist())
        if "7 hour" in row_text or "7 hr" in row_text:
            result[cid] = "7 Hours"
        else:
            result[cid] = "9 Hours"
    return result

roster_hours_map = build_roster_hours_map(roster_df)

def get_possible_paths(d, warehouse):
    d_str = d.strftime("%Y-%m-%d")
    return [os.path.join(warehouse, f"{d_str}.xlsx"), f"{d_str}.xlsx"]

def read_daily_file(path):
    try:
        return read_excel_smart(path, sheet_name=0, dtype=str)
    except Exception:
        return pd.DataFrame()

@st.cache_data(show_spinner=False, ttl=300)
def process_attendance_data(dates_tuple, warehouse, manual_str, exclude_str, roster_map):
    manual_list = [clean_id(x) for x in manual_str.split(",")] if manual_str else []
    exclude_list = [clean_id(x) for x in exclude_str.split(",")] if exclude_str else []
    t_dfs = []
    missing_files = []
    start_d, end_d = dates_tuple

    for d in [start_d + timedelta(days=i) for i in range((end_d - start_d).days + 1)]:
        d_str = d.strftime("%Y-%m-%d")
        f_path = next((p for p in get_possible_paths(d, warehouse) if file_exists(p)), None)
        if not f_path:
            missing_files.append(d_str)
            continue
        tdf = read_daily_file(f_path)
        if tdf.empty:
            missing_files.append(d_str)
            continue
        tdf["Date"] = d_str
        t_dfs.append(tdf)

    if not t_dfs:
        return pd.DataFrame(), missing_files

    a_df = pd.concat(t_dfs, ignore_index=True)
    a_df.columns = [str(c).strip() for c in a_df.columns]
    i_col, n_col = a_df.columns[0], a_df.columns[1]
    a_df["Clean_ID"] = a_df[i_col].apply(clean_id)

    if exclude_list:
        a_df = a_df[~a_df["Clean_ID"].isin(exclude_list)].copy()
        a_df.reset_index(drop=True, inplace=True)

    def get_hours(row):
        cid = row["Clean_ID"]
        if cid in manual_list:
            return "7 Hours"
        if cid in roster_map:
            return roster_map[cid]
        return "9 Hours"

    a_df["Working Hours"] = a_df.apply(get_hours, axis=1)
    p_cols = [col for col in a_df.columns if not any(k in col.lower() for k in ["id", "name", "psoft", "employee", "date"])]

    def analyze(row):
        punches = [parse_time(row.get(c)) for c in p_cols]
        punches = [p for p in punches if p is not None]
        total_punches = len(punches)
        target = str(row.get("Working Hours", "9 Hours"))
        min_mins, max_mins = (405, 435) if "7" in target else (525, 555)

        if total_punches == 0:
            return pd.Series([0, target, "00:00", "OK", "Absent", "Clean"])
        if total_punches == 1:
            return pd.Series([1, target, "N/A", "Error", "Single Scan Only", "Mispunch"])

        dummy = datetime(2026, 1, 1)
        total_secs = 0
        for i in range(0, total_punches - (total_punches % 2), 2):
            start = datetime.combine(dummy, punches[i])
            end = datetime.combine(dummy, punches[i + 1])
            if end < start:
                end += timedelta(days=1)
            total_secs += (end - start).total_seconds()

        eff_mins = total_secs / 60
        hr_str = f"{int(total_secs // 3600):02d}:{int((total_secs % 3600) // 60):02d}"

        if total_punches % 2 == 0:
            if min_mins <= eff_mins <= max_mins:
                return pd.Series([total_punches, target, hr_str, "OK", "Complete Within Window", "Clean"])
            elif eff_mins < min_mins:
                return pd.Series([total_punches, target, hr_str, "Error", "Under Time", "Defaulter Hours"])
            else:
                return pd.Series([total_punches, target, hr_str, "Error", "Over Time", "Defaulter Hours"])
        return pd.Series([total_punches, target, hr_str, "Error", "Incomplete Punches", "Mispunch"])

    analyzed = a_df.apply(analyze, axis=1)
    analyzed.columns = ["Total Punches", "Assigned Target", "Calculated Hours", "Status", "Category", "Issue Type"]

    basic_info = pd.DataFrame({
        "Date": a_df["Date"],
        "P.Soft ID": a_df[i_col].astype(str).str.replace(r"\.0$", "", regex=True).str.strip(),
        "Employee Name": a_df[n_col].astype(str).str.replace(r"\.0$", "", regex=True).str.strip(),
    })
    return pd.concat([basic_info, analyzed], axis=1), missing_files

# ==========================================================
# MAIN EXECUTION WITH CLICKABLE CARDS
# ==========================================================
if isinstance(selected_dates_range, tuple) and len(selected_dates_range) == 2:
    with st.spinner("🔄 Fetching compliance data..."):
        final_df, missing_files = process_attendance_data(
            tuple(selected_dates_range), selected_warehouse, manual_7_ids, exclude_ids_input, tuple(sorted(roster_hours_map.items()))
        )

        mispunches = final_df[final_df["Issue Type"] == "Mispunch"].copy() if not final_df.empty else pd.DataFrame()
        defaulters = final_df[final_df["Issue Type"] == "Defaulter Hours"].copy() if not final_df.empty else pd.DataFrame()
        repeated_mispunches = mispunches[mispunches["P.Soft ID"].isin(mispunches["P.Soft ID"].value_counts()[mispunches["P.Soft ID"].value_counts() > 1].index)] if not mispunches.empty else pd.DataFrame()

    if "selected_view" not in st.session_state:
        st.session_state.selected_view = "defaulters"

    # TOP METRIC CARDS WITH CLICK LOGIC
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f'<div class="metric-card card-purple" id="card_def"><div class="card-title">⏰ Defaulter Hours</div><div class="card-value">{len(defaulters)}</div></div>', unsafe_allow_html=True)
        if st.button("⏰ View Defaulters ➔", key="btn_def", use_container_width=True):
            st.session_state.selected_view = "defaulters"

    with c2:
        st.markdown(f'<div class="metric-card card-orange" id="card_mis"><div class="card-title">⚠️ Mispunches</div><div class="card-value">{len(mispunches)}</div></div>', unsafe_allow_html=True)
        if st.button("⚠️ View Mispunches ➔", key="btn_mis", use_container_width=True):
            st.session_state.selected_view = "mispunches"

    with c3:
        st.markdown(f'<div class="metric-card card-red" id="card_rep_mis"><div class="card-title">🔄 Repeated Mispunches</div><div class="card-value">{len(repeated_mispunches)}</div></div>', unsafe_allow_html=True)
        if st.button("🔄 View Rep. Mispunches ➔", key="btn_rep_mis", use_container_width=True):
            st.session_state.selected_view = "rep_mispunches"

    with c4:
        st.markdown(f'<div class="metric-card card-blue" id="card_upl"><div class="card-title">📋 UPL Report</div><div class="card-value">0</div></div>', unsafe_allow_html=True)
        if st.button("📋 View UPL Summary ➔", key="btn_upl", use_container_width=True):
            st.session_state.selected_view = "upl"

    components.html(
        """
        <script>
        const doc = window.parent.document;
        function bindCardClick(cardId, buttonTextMatch) {
            const card = doc.getElementById(cardId);
            if (card) {
                card.onclick = function() {
                    const buttons = Array.from(doc.querySelectorAll("button"));
                    const targetBtn = buttons.find(b => b.innerText.includes(buttonTextMatch));
                    if (targetBtn) { targetBtn.click(); }
                };
            }
        }
        setTimeout(() => {
            bindCardClick("card_def", "⏰ View Defaulters");
            bindCardClick("card_mis", "⚠️ View Mispunches");
            bindCardClick("card_rep_mis", "🔄 View Rep. Mispunches");
            bindCardClick("card_upl", "📋 View UPL Summary");
        }, 100);
        </script>
        """,
        height=0,
        width=0,
    )

    if not final_df.empty:
        display_df = final_df.copy()
        if st.session_state.selected_view == "rep_mispunches":
            display_df = repeated_mispunches.copy()
        elif st.session_state.selected_view == "mispunches":
            display_df = mispunches.copy()
        elif st.session_state.selected_view == "defaulters":
            display_df = defaulters.copy()

        st.subheader(f"📊 Results View ({len(display_df)} Records)")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("📂 No data found for selected warehouse and date range.")

# FOOTER
st.markdown("<hr style='border:none; border-top:1px solid #e2e8f0; margin:10px 0 6px 0;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#64748b; font-size:11px; font-weight:600; margin:0;'>Built for a smarter, stronger and compliant workplace</p>", unsafe_allow_html=True)

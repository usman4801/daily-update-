import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Amazon Leave Compliance & Attendance Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# STYLING & CSS (Pixel-matched with UI screenshot)
# ==========================================================
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    .stApp {
        background-color: #f4f6fa;
    }
    
    /* Top Header Bar */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    .block-container {
        padding: 0.5rem 1.8rem 2rem 1.8rem !important;
        max-width: 100% !important;
    }
    
    /* Global Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #131921 !important;
        width: 210px !important;
    }
    
    section[data-testid="stSidebar"] div.block-container {
        padding: 1.5rem 0.7rem !important;
    }
    
    .sidebar-btn {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 14px;
        color: #99aab5;
        font-size: 13px;
        font-weight: 600;
        border-radius: 8px;
        margin-bottom: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .sidebar-btn:hover {
        background: rgba(255, 255, 255, 0.06);
        color: #ffffff;
    }
    
    .sidebar-btn.active {
        background: #ff9900;
        color: #ffffff !important;
        font-weight: 700;
    }
    
    /* Custom Card Style */
    .dashboard-card {
        background: #ffffff;
        border: 1px solid #e5e9f2;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
        margin-bottom: 14px;
    }
    
    /* Stat Badges */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 6px;
    }
    .badge-up { background: #fee2e2; color: #dc2626; }
    .badge-down { background: #dcfce7; color: #16a34a; }
    
    /* Risk Badges */
    .risk-high {
        background: #ef4444;
        color: white;
        font-weight: 800;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        text-align: center;
    }
    .risk-med {
        background: #f97316;
        color: white;
        font-weight: 800;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        text-align: center;
    }
    .risk-low {
        background: #facc15;
        color: #78350f;
        font-weight: 800;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: 12px;
        display: inline-block;
        text-align: center;
    }
    
    .status-validated {
        color: #16a34a;
        font-weight: 700;
        font-size: 11.5px;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    
    /* Spike Annotations */
    .spike-pill {
        background: #ff9900;
        color: white;
        font-weight: 800;
        font-size: 10px;
        padding: 2px 8px;
        border-radius: 10px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================================
# SIDEBAR NAVIGATION
# ==========================================================
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:8px; margin-bottom: 22px; padding-left:6px;">
            <span style="font-size:24px; font-weight:900; color:#fff; letter-spacing:-0.5px;">amazon</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div class="sidebar-btn active">📊 Overview</div>
        <div class="sidebar-btn">📋 UPL Intelligence</div>
        <div class="sidebar-btn">🔍 SL / PL Analysis</div>
        <div class="sidebar-btn">📈 Attendance Trends</div>
        <div class="sidebar-btn">📑 Compliance Matrix</div>
        <div class="sidebar-btn">📁 Reports</div>
        <div class="sidebar-btn" style="margin-top: 24px;">⚙️ Settings</div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style="position:fixed; bottom:20px; left:16px; display:flex; flex-direction:column; gap:4px;">
            <span style="font-size:16px; font-weight:900; color:#fff;">amazon</span>
            <span style="font-size:10px; color:#94a3b8; font-weight:600;">Better People<br>Better Tomorrow</span>
        </div>
    """, unsafe_allow_html=True)

# ==========================================================
# TOP HORIZONTAL NAV / BANNER
# ==========================================================
st.markdown("""
    <div style="background:#131921; border-radius:10px; padding:10px 18px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; color:#fff;">
        <div style="display:flex; align-items:center; gap:16px;">
            <span style="font-size:19px; font-weight:900; color:#fff;">amazon</span>
            <span style="font-size:13.5px; font-weight:700; color:#e2e8f0; border-left:1px solid #334155; padding-left:14px; letter-spacing:0.3px;">
                LEAVE COMPLIANCE & ATTENDANCE INTELLIGENCE MONITOR &nbsp;|&nbsp; ABU DHABI
            </span>
        </div>
        <div style="display:flex; align-items:center; gap:18px; font-size:12.5px; font-weight:600; color:#cbd5e1;">
            <span>🔔 <sup style="background:#ea580c; border-radius:50%; padding:1px 5px; color:#fff; font-size:9px;">3</sup></span>
            <span>❓</span>
            <span style="display:flex; align-items:center; gap:6px;">👤 HR Analytics ▾</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==========================================================
# FILTER BAR
# ==========================================================
f_col1, f_col2, f_col3, f_col4 = st.columns([2.2, 2.2, 4, 1.6])

with f_col1:
    site = st.selectbox("Site / Location", ["Abu Dhabi (ADC1)", "AUH1 (Airport)", "DXB3 (Dubai)", "DXB5"])

with f_col2:
    date_val = st.date_input("Date Range", [datetime(2026, 9, 15), datetime(2026, 9, 21)])

with f_col3:
    emp_search = st.text_input("Search Associate", placeholder="Enter Associate ID or Name...")

with f_col4:
    st.markdown("""
        <div style="margin-top:22px; display:flex; justify-content:flex-end; align-items:center; gap:6px; color:#64748b; font-size:11.5px; font-weight:600;">
            <span>🕒 Last Updated<br><b>Today 14:32</b></span>
            <button style="border:1px solid #cbd5e1; background:#fff; border-radius:6px; padding:4px 7px; cursor:pointer;">🔄</button>
        </div>
    """, unsafe_allow_html=True)

# ==========================================================
# MAIN DASHBOARD BODY (LEFT = UPL, RIGHT = PATTERNS)
# ==========================================================
main_col_left, main_col_right = st.columns([5.3, 6.7], gap="medium")

# ----------------------------------------------------------
# LEFT COLUMN: UPL TILE & BREAKDOWN CONTAINER
# ----------------------------------------------------------
with main_col_left:
    st.markdown("""
        <div class="dashboard-card" style="background: linear-gradient(135deg, #ffffff 82%, #fff7ed 100%); border-left:4px solid #ff9900;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:20px;">📋</span>
                    <div>
                        <div style="font-size:16px; font-weight:800; color:#111827;">UPL Report</div>
                        <div style="font-size:11px; color:#64748b; font-weight:600;">Unplanned Leave (UPL) — Key Insights</div>
                    </div>
                </div>
                <div style="font-size:12px; font-weight:700; color:#ea580c; cursor:pointer;">View Full Report ➔</div>
            </div>
            <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px;">
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:10.5px; font-weight:700; color:#64748b;">Total UPL Case Volume</span>
                        <span style="background:#e0f2fe; padding:2px 4px; border-radius:4px; font-size:11px;">👥</span>
                    </div>
                    <div style="font-size:24px; font-weight:900; color:#0f172a; margin:4px 0 2px 0;">1,450</div>
                    <span class="badge-pill badge-up">↑ 12.5% vs. last week</span>
                </div>
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:10.5px; font-weight:700; color:#64748b;">Active Rate</span>
                        <span style="background:#fef3c7; padding:2px 4px; border-radius:4px; font-size:11px;">%</span>
                    </div>
                    <div style="font-size:24px; font-weight:900; color:#0f172a; margin:4px 0 2px 0;">6.8%</div>
                    <span class="badge-pill badge-down">↓ 2.3% vs. last week</span>
                </div>
                <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:10px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:10.5px; font-weight:700; color:#64748b;">Compliance Rate</span>
                        <span style="background:#f3e8ff; padding:2px 4px; border-radius:4px; font-size:11px;">🛡️</span>
                    </div>
                    <div style="font-size:24px; font-weight:900; color:#0f172a; margin:4px 0 2px 0;">93.2%</div>
                    <span class="badge-pill badge-down">↑ 1.7% vs. last week</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Expandable Details Box
    with st.expander("📂 UPL Report Details", expanded=True):
        
        # 1. Day-Wise Compliance Matrix
        st.markdown("<p style='font-size:12px; font-weight:800; color:#1e293b; margin:0 0 6px 0;'>📅 1. Day-Wise Compliance Matrix</p>", unsafe_allow_html=True)
        
        day_matrix_html = """
        <table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center; font-family:sans-serif; margin-bottom:14px;">
            <thead>
                <tr style="background:#f1f5f9; color:#475569; font-weight:800; border-bottom:1px solid #e2e8f0;">
                    <th style="padding:5px;">Day</th>
                    <th>Total Associates</th>
                    <th>Compliant</th>
                    <th>Non-Compliant</th>
                    <th>Compliance Rate</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom:1px solid #f1f5f9;"><td>Sun</td><td>1,820</td><td>1,742</td><td style="color:#dc2626; font-weight:700;">78</td><td style="background:#dcfce7; color:#15803d; font-weight:700;">95.7%</td></tr>
                <tr style="border-bottom:1px solid #f1f5f9; background:#fffaf5;"><td>Mon</td><td>1,834</td><td>1,658</td><td style="color:#dc2626; font-weight:700;">176</td><td style="background:#fee2e2; color:#b91c1c; font-weight:700;">90.3%</td></tr>
                <tr style="border-bottom:1px solid #f1f5f9;"><td>Tue</td><td>1,812</td><td>1,721</td><td style="color:#dc2626; font-weight:700;">91</td><td style="background:#dcfce7; color:#15803d; font-weight:700;">94.9%</td></tr>
                <tr style="border-bottom:1px solid #f1f5f9;"><td>Wed</td><td>1,806</td><td>1,736</td><td style="color:#dc2626; font-weight:700;">70</td><td style="background:#dcfce7; color:#15803d; font-weight:700;">96.1%</td></tr>
                <tr style="border-bottom:1px solid #f1f5f9;"><td>Thu</td><td>1,795</td><td>1,719</td><td style="color:#dc2626; font-weight:700;">76</td><td style="background:#dcfce7; color:#15803d; font-weight:700;">95.8%</td></tr>
                <tr style="border-bottom:1px solid #f1f5f9; background:#fffaf5;"><td>Fri</td><td>1,828</td><td>1,642</td><td style="color:#dc2626; font-weight:700;">186</td><td style="background:#fee2e2; color:#b91c1c; font-weight:700;">89.8%</td></tr>
                <tr style="border-bottom:1px solid #f1f5f9;"><td>Sat</td><td>1,801</td><td>1,738</td><td style="color:#dc2626; font-weight:700;">63</td><td style="background:#dcfce7; color:#15803d; font-weight:700;">96.5%</td></tr>
            </tbody>
        </table>
        """
        st.markdown(day_matrix_html, unsafe_allow_html=True)
        
        # 2. 3P Agency Breakdown & Bar Chart
        st.markdown("<p style='font-size:12px; font-weight:800; color:#1e293b; margin:6px 0;'>👥 2. 3P Agency Breakdown</p>", unsafe_allow_html=True)
        ag_col1, ag_col2 = st.columns([1.2, 1])
        
        with ag_col1:
            ag_table_html = """
            <table style="width:100%; border-collapse:collapse; font-size:10.5px; text-align:center; font-family:sans-serif;">
                <thead>
                    <tr style="background:#f8fafc; color:#475569; font-weight:700; border-bottom:1px solid #e2e8f0;">
                        <th style="padding:4px; text-align:left;">Agency</th>
                        <th>Total</th>
                        <th>UPL</th>
                        <th>% Share</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td style="text-align:left; font-weight:600;">Randstad</td><td>520</td><td>342</td><td>23.6%</td></tr>
                    <tr><td style="text-align:left; font-weight:600;">Manpower</td><td>468</td><td>298</td><td>20.6%</td></tr>
                    <tr><td style="text-align:left; font-weight:600;">Adecco</td><td>412</td><td>261</td><td>18.0%</td></tr>
                    <tr><td style="text-align:left; font-weight:600;">Kelly Services</td><td>358</td><td>223</td><td>15.4%</td></tr>
                    <tr><td style="text-align:left; font-weight:600;">Others</td><td>289</td><td>196</td><td>13.5%</td></tr>
                    <tr style="font-weight:800; background:#fef9c3; border-top:1px solid #cbd5e1;">
                        <td style="text-align:left;">Total</td><td>2,047</td><td>1,450</td><td>100%</td>
                    </tr>
                </tbody>
            </table>
            """
            st.markdown(ag_table_html, unsafe_allow_html=True)
            
        with ag_col2:
            ag_df = pd.DataFrame({
                "Agency": ["Randstad", "Manpower", "Adecco", "Kelly", "Others"],
                "Cases": [342, 298, 261, 223, 196]
            })
            ag_chart = alt.Chart(ag_df).mark_bar(size=14, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                x=alt.X('Agency:N', sort='-y', axis=alt.Axis(labelAngle=-45, title=None, labelFontSize=9)),
                y=alt.Y('Cases:Q', axis=alt.Axis(title=None)),
                color=alt.Color('Agency:N', scale=alt.Scale(range=['#3b82f6', '#f97316', '#06b6d4', '#8b5cf6', '#64748b']), legend=None)
            ).properties(height=130)
            st.altair_chart(ag_chart, use_container_width=True)
            
        # 3. Weekly Trend (Planned vs Unplanned Targets) & 4. Category Donut
        t_col1, t_col2 = st.columns([1.1, 1])
        with t_col1:
            st.markdown("<p style='font-size:11.5px; font-weight:800; color:#1e293b; margin:6px 0;'>📈 3. Weekly Trend Targets</p>", unsafe_allow_html=True)
            trend_df = pd.DataFrame({
                "Day": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
                "Planned Leave (Target)": [180, 195, 188, 176, 165, 172, 160],
                "Unplanned Leave (Target)": [72, 98, 86, 79, 68, 74, 63]
            }).melt("Day", var_name="Type", value_name="Count")
            
            trend_chart = alt.Chart(trend_df).mark_line(point=True).encode(
                x=alt.X('Day:N', sort=None, axis=alt.Axis(title=None, labelFontSize=9)),
                y=alt.Y('Count:Q', axis=alt.Axis(title=None)),
                color=alt.Color('Type:N', scale=alt.Scale(domain=['Planned Leave (Target)', 'Unplanned Leave (Target)'], range=['#3b82f6', '#f97316']), legend=alt.Legend(orient='bottom', title=None, labelFontSize=8))
            ).properties(height=140)
            st.altair_chart(trend_chart, use_container_width=True)
            
        with t_col2:
            st.markdown("<p style='font-size:11.5px; font-weight:800; color:#1e293b; margin:6px 0;'>🍩 4. Absence Distribution</p>", unsafe_allow_html=True)
            donut_df = pd.DataFrame({
                "Category": ["Medical Certified", "Single-day Unannounced", "Personal Emergency"],
                "Count": [792, 411, 247]
            })
            donut_chart = alt.Chart(donut_df).mark_arc(innerRadius=32).encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color("Category:N", scale=alt.Scale(range=['#3b82f6', '#f97316', '#22c55e']), legend=None),
                tooltip=["Category", "Count"]
            ).properties(height=140)
            st.altair_chart(donut_chart, use_container_width=True)

# ----------------------------------------------------------
# RIGHT COLUMN: BEHAVIORAL LEAVE PATTERN ENGINE (SL / PL)
# ----------------------------------------------------------
with main_col_right:
    st.markdown("""
        <div class="dashboard-card" style="margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:20px;">🧠</span>
                    <span style="font-size:15px; font-weight:800; color:#0f172a;">
                        Leave Pattern & Behavioral Abuse Engine <span style="font-weight:500; font-size:12px; color:#64748b;">(SL / PL Focus)</span>
                    </span>
                </div>
                <span style="font-size:11.5px; font-weight:700; color:#2563eb; cursor:pointer;">View Insights ➔</span>
            </div>
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:14px;">
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px; display:flex; align-items:center; gap:12px;">
                    <div style="background:#dbeafe; color:#2563eb; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">👤</div>
                    <div>
                        <div style="font-size:11.5px; font-weight:700; color:#475569;">Single-Day Strategic Leaves</div>
                        <div style="font-size:26px; font-weight:900; color:#0f172a; line-height:1.1;">72 <span style="font-size:12px; font-weight:600; color:#64748b;">Associates flagged</span></div>
                        <span class="badge-pill badge-up" style="margin-top:3px;">↑ 8.4% vs. last week</span>
                    </div>
                </div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px; display:flex; align-items:center; gap:12px;">
                    <div style="background:#e0f2fe; color:#0284c7; width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:18px;">📅</div>
                    <div>
                        <div style="font-size:11.5px; font-weight:700; color:#475569;">2-Day Consecutive Clusters</div>
                        <div style="font-size:26px; font-weight:900; color:#0f172a; line-height:1.1;">35 <span style="font-size:12px; font-weight:600; color:#64748b;">(off-day adjacent patterns)</span></div>
                        <span class="badge-pill badge-up" style="margin-top:3px;">↑ 25.7% vs. last week</span>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Weekly Pattern Prevalence Chart
    st.markdown("""
        <div class="dashboard-card" style="padding-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="font-size:13.5px; font-weight:800; color:#0f172a;">Weekly Pattern Prevalence (SL / PL)</span>
                <div style="display:flex; gap:10px;">
                    <span class="spike-pill">Monday Spike</span>
                    <span class="spike-pill" style="background:#ef4444;">Friday Spike</span>
                </div>
            </div>
    """, unsafe_allow_html=True)
    
    pattern_chart_data = pd.DataFrame({
        "Day": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        "1-Day SL": [32, 72, 51, 43, 38, 64, 27],
        "2-Day SL Cluster": [28, 68, 44, 36, 32, 58, 26],
        "1-Day PL": [38, 58, 47, 39, 36, 54, 34]
    }).melt("Day", var_name="Type", value_name="Incidence")
    
    pat_chart = alt.Chart(pattern_chart_data).mark_bar(size=22).encode(
        x=alt.X('Day:N', sort=None, axis=alt.Axis(title=None, labelFontSize=10, labelFontWeight='bold')),
        y=alt.Y('Incidence:Q', axis=alt.Axis(title=None)),
        color=alt.Color('Type:N', scale=alt.Scale(
            domain=['1-Day SL', '2-Day SL Cluster', '1-Day PL'],
            range=['#1d4ed8', '#f97316', '#22c55e']
        ), legend=alt.Legend(orient='top', title=None, labelFontSize=9)),
        order=alt.Order('Type:N', sort='ascending')
    ).properties(height=180)
    
    st.altair_chart(pat_chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # High Frequency Defaulters Drill-Down Table
    st.markdown("""
        <div class="dashboard-card">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <span style="font-size:13.5px; font-weight:800; color:#0f172a;">High-Frequency Defaulters Drill-Down</span>
                <span style="font-size:11.5px; font-weight:700; color:#2563eb; cursor:pointer;">View All ➔</span>
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:11px; text-align:center; font-family:sans-serif;">
                <thead>
                    <tr style="background:#f8fafc; color:#475569; font-weight:700; border-bottom:1px solid #e2e8f0;">
                        <th style="padding:6px;">#</th>
                        <th>Associate ID</th>
                        <th style="text-align:left;">Name</th>
                        <th>1-Day SL Count</th>
                        <th>2-Day SL Cluster</th>
                        <th>1-Day PL Count</th>
                        <th>Disruption Risk Index</th>
                        <th style="text-align:left;">Medical Certificate Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid #f1f5f9;">
                        <td style="padding:6px;">1</td>
                        <td><b>A102934</b></td>
                        <td style="text-align:left;">Ahmed Khan</td>
                        <td>6</td>
                        <td>4</td>
                        <td>3</td>
                        <td><span class="risk-high">92%</span></td>
                        <td style="text-align:left;"><span class="status-validated">✔ VALIDATED <span style="color:#64748b; font-weight:400;">(Doctor Slip)</span></span></td>
                    </tr>
                    <tr style="border-bottom:1px solid #f1f5f9;">
                        <td style="padding:6px;">2</td>
                        <td><b>A104221</b></td>
                        <td style="text-align:left;">Fatima Al Mansoori</td>
                        <td>5</td>
                        <td>3</td>
                        <td>2</td>
                        <td><span class="risk-med">78%</span></td>
                        <td style="text-align:left;"><span class="status-validated">✔ VALIDATED <span style="color:#64748b; font-weight:400;">(Doctor Slip)</span></span></td>
                    </tr>
                    <tr style="border-bottom:1px solid #f1f5f9;">
                        <td style="padding:6px;">3</td>
                        <td><b>A107563</b></td>
                        <td style="text-align:left;">Rahil Shaikh</td>
                        <td>4</td>
                        <td>3</td>
                        <td>1</td>
                        <td><span class="risk-med">65%</span></td>
                        <td style="text-align:left;"><span class="status-validated">✔ VALIDATED <span style="color:#64748b; font-weight:400;">(Doctor Slip)</span></span></td>
                    </tr>
                    <tr style="border-bottom:1px solid #f1f5f9;">
                        <td style="padding:6px;">4</td>
                        <td><b>A109876</b></td>
                        <td style="text-align:left;">Saeed Al Balushi</td>
                        <td>3</td>
                        <td>2</td>
                        <td>2</td>
                        <td><span class="risk-low">52%</span></td>
                        <td style="text-align:left;"><span class="status-validated">✔ VALIDATED <span style="color:#64748b; font-weight:400;">(Doctor Slip)</span></span></td>
                    </tr>
                    <tr style="border-bottom:1px solid #f1f5f9;">
                        <td style="padding:6px;">5</td>
                        <td><b>A112349</b></td>
                        <td style="text-align:left;">Noora Al Dhaheri</td>
                        <td>3</td>
                        <td>2</td>
                        <td>1</td>
                        <td><span class="risk-low">48%</span></td>
                        <td style="text-align:left;"><span class="status-validated">✔ VALIDATED <span style="color:#64748b; font-weight:400;">(Doctor Slip)</span></span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    """, unsafe_allow_html=True)

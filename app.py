
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

st.set_page_config(
    page_title="Leave Compliance & Attendance Intelligence Monitor | Abu Dhabi",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Theme / CSS — closely follows the supplied screenshot
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: Inter, Arial, sans-serif !important;
}
.stApp { background:#f8fafc; color:#172b4d; }
header[data-testid="stHeader"] { background:#131921; height:0; }
.block-container { padding:0.8rem 1.2rem 1.4rem !important; max-width:100%; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background:#10233b !important;
    min-width:190px !important;
    max-width:190px !important;
}
section[data-testid="stSidebar"] > div { padding:0.6rem 0.65rem; }
.side-logo { color:white; font-size:25px; font-weight:800; padding:4px 10px 18px; }
.side-logo span { color:#ff9900; }
.nav-item {
    color:#dbe7f5; padding:11px 12px; border-radius:7px; margin:3px 0;
    font-size:13px; font-weight:500;
}
.nav-active { background:#ff9900; color:white; font-weight:700; }
.side-foot { position:fixed; bottom:18px; color:white; font-size:12px; opacity:.9; padding-left:12px; }

/* Top bar */
.topbar {
    height:57px; background:#131921; color:white; border-radius:0 0 7px 7px;
    display:flex; align-items:center; padding:0 18px; gap:18px;
    margin:-0.8rem -1.2rem 12px;
}
.amazon { font-size:24px; font-weight:800; letter-spacing:-1px; }
.amazon .smile { color:#ff9900; }
.top-title { border-left:1px solid #596575; padding-left:18px; font-size:16px; font-weight:700; flex:1; }
.top-right { font-size:11px; white-space:nowrap; }

/* Inputs */
div[data-testid="stSelectbox"], div[data-testid="stDateInput"], div[data-testid="stTextInput"] { margin-bottom:0 !important; }
div[data-testid="stSelectbox"] > label,
div[data-testid="stDateInput"] > label,
div[data-testid="stTextInput"] > label { font-size:10px !important; color:#64748b !important; margin-bottom:2px !important; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
    background:white !important; border:1px solid #dbe4ee !important; border-radius:6px !important;
}
div[data-baseweb="select"] span, div[data-baseweb="input"] input { font-size:11px !important; }

/* Cards */
.card {
    background:#fff; border:1px solid #dbe4ee; border-radius:9px;
    box-shadow:0 2px 8px rgba(15,23,42,.06); padding:13px;
    margin-bottom:12px;
}
.card-title { display:flex; align-items:center; font-size:15px; font-weight:800; color:#172b4d; margin-bottom:11px; }
.icon { width:34px; height:34px; border-radius:9px; background:#fff0db; color:#e88400;
        display:inline-flex; align-items:center; justify-content:center; margin-right:9px; font-size:17px; }
.card-link { margin-left:auto; color:#e88400; font-size:11px; font-weight:700; }

/* KPI */
.kpi {
    border:1px solid #dbe8f5; border-radius:7px; padding:11px;
    background:linear-gradient(180deg,#fff,#f7fbff); min-height:98px;
}
.kpi-label { font-size:10px; font-weight:700; }
.kpi-value { font-size:27px; font-weight:800; margin:5px 0; color:#172b4d; }
.delta-red { color:#ef4444; font-size:10px; }
.delta-green { color:#18a765; font-size:10px; }

/* Tables */
.dataframe { font-size:10px !important; }
.stDataFrame { border:1px solid #dbe4ee; border-radius:7px; overflow:hidden; }

/* Buttons */
.stButton > button {
    background:#ff9900 !important; color:#fff !important; border:0 !important;
    border-radius:6px !important; font-weight:800 !important; font-size:11px !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Data
# -----------------------------
days = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"]

compliance = pd.DataFrame({
    "Day":days, "Total Associates":[1820,1834,1812,1806,1795,1828,1801],
    "Compliant":[1742,1658,1721,1736,1719,1642,1738],
    "Non-Compliant":[78,176,91,70,76,186,63],
})
compliance["Compliance Rate"] = (compliance["Compliant"]/compliance["Total Associates"]*100).round(1).astype(str)+"%"

agency = pd.DataFrame({
    "Agency":["Randstad","Manpower","Adecco","Kelly Services","Others"],
    "Total Associates":[520,468,412,358,289],
    "UPL Cases":[342,298,261,223,196],
    "% of Total":["23.6%","20.6%","18.0%","15.4%","13.5%"]
})

defaulters = pd.DataFrame({
    "#":[1,2,3,4,5],
    "Associate ID":["A102934","A104221","A107563","A109876","A112349"],
    "Name":["Ahmed Khan","Fatima Al Mansoori","Rahil Shaikh","Saeed Al Balushi","Noora Al Dhaheri"],
    "1-Day SL Count":[6,5,4,3,3],
    "2-Day SL Cluster Count":[4,3,3,2,2],
    "1-Day PL Count":[3,2,1,2,1],
    "Disruption Risk Index":["92%","78%","65%","52%","48%"],
    "Medical Certificate Status":["✓ VALIDATED\n(Doctor Slip)"]*5
})

pattern1 = pd.DataFrame({
    "Site":["ADC1","AAN","DXB"],
    "Sun":[12,8,4],"Mon":[18,11,7],"Tue":[9,6,5],"Wed":[7,5,4],
    "Thu":[11,8,6],"Fri":[14,9,7],"Sat":[8,6,5],
    "Incidence":["8.2%","5.6%","3.9%"],"Risk Score":[72,58,42]
})
pattern2 = pd.DataFrame({
    "Site":["ADC1","AAN","DXB"],
    "Sun":[5,3,1],"Mon":[9,5,2],"Tue":[7,4,2],"Wed":[4,3,1],
    "Thu":[8,6,3],"Fri":[12,8,5],"Sat":[6,4,2],
    "Incidence":["6.1%","4.2%","2.1%"],"Risk Score":[68,51,34]
})

sl = [32,72,51,43,38,64,27]
cluster = [28,68,44,36,32,58,26]
pl = [38,58,47,39,36,54,34]

# -----------------------------
# Helper charts
# -----------------------------
def stacked_pattern():
    fig = go.Figure()
    fig.add_bar(x=days, y=sl, name="1-Day SL", marker_color="#2877d7")
    fig.add_bar(x=days, y=cluster, name="2-Day SL Cluster", marker_color="#ff9900")
    fig.add_bar(x=days, y=pl, name="1-Day PL", marker_color="#18a765")
    fig.update_layout(
        barmode="stack", height=210, margin=dict(l=8,r=8,t=8,b=28),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(size=10,color="#172b4d"),
        legend=dict(orientation="h", y=1.12, x=0.45, font=dict(size=9)),
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#edf2f7", zeroline=False),
    )
    # callouts
    fig.add_annotation(x="Mon", y=205, text="Monday Spike", showarrow=True, arrowhead=2,
                       bgcolor="#ff9900", font=dict(color="white",size=9))
    fig.add_annotation(x="Fri", y=185, text="Friday Spike", showarrow=True, arrowhead=2,
                       bgcolor="#ff9900", font=dict(color="white",size=9))
    return fig

def weekly_trend():
    planned=[180,195,188,176,165,172,160]
    unplanned=[72,98,86,79,68,74,63]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=days,y=planned,name="Planned Leave (Target)",mode="lines+markers",
                             line=dict(color="#2877d7",width=2.5)))
    fig.add_trace(go.Scatter(x=days,y=unplanned,name="Unplanned Leave (Target)",mode="lines+markers",
                             line=dict(color="#ff9900",width=2.5),fill="tozeroy",fillcolor="rgba(255,153,0,.10)"))
    fig.update_layout(height=190,margin=dict(l=8,r=8,t=8,b=24),paper_bgcolor="white",
                      plot_bgcolor="white",font=dict(size=9,color="#172b4d"),
                      legend=dict(orientation="h",font=dict(size=8)),
                      xaxis=dict(showgrid=False),yaxis=dict(gridcolor="#edf2f7",zeroline=False))
    return fig

def donut():
    fig=go.Figure(go.Pie(labels=["Medical Certified","Single-day Unannounced","Personal Emergency"],
                         values=[792,411,247],hole=.66,
                         marker=dict(colors=["#2877d7","#ff9900","#18a765"]),
                         textinfo="percent",textfont=dict(size=10)))
    fig.update_layout(height=190,margin=dict(l=4,r=4,t=4,b=4),showlegend=True,
                      legend=dict(font=dict(size=9),x=.95,y=.5),
                      paper_bgcolor="white")
    return fig

# -----------------------------
# Header + filters
# -----------------------------
st.markdown("""
<div class="topbar">
  <div class="amazon">amazon<span class="smile">⌣</span></div>
  <div class="top-title">LEAVE COMPLIANCE & ATTENDANCE INTELLIGENCE MONITOR <span style="color:#ff9900">|</span> ABU DHABI</div>
  <div class="top-right">⌂ Home　▤ Reports　⌕ Insights　⚙ Settings　　◉ HR Analytics⌄</div>
</div>
""", unsafe_allow_html=True)

c1,c2,c3,c4 = st.columns([1.15,1.35,2.0,1.1])
with c1:
    st.selectbox("Site / Location",["Abu Dhabi (ADC1)","AAN","DXB"],label_visibility="visible")
with c2:
    st.date_input("Date Range",(date(2025,4,21),date(2025,4,27)))
with c3:
    st.text_input("Search Associate",placeholder="Enter Associate ID or Name...")
with c4:
    st.markdown('<div style="padding:5px 10px;background:white;border:1px solid #dbe4ee;border-radius:6px;font-size:10px;color:#64748b"><b>Last Updated</b><br>Apr 27, 2025　14:32　↻</div>',unsafe_allow_html=True)

left,right = st.columns([1.02,.98], gap="small")

# -----------------------------
# LEFT
# -----------------------------
with left:
    st.markdown("""
    <div class="card">
      <div class="card-title"><span class="icon">▣</span>UPL Report
        <span class="card-link">Interactive Drill-down →</span>
      </div>
      <div style="font-size:10px;color:#64748b;margin:-8px 0 10px 43px">Unplanned Leave (UPL) — Key Insights</div>
    """, unsafe_allow_html=True)
    k1,k2,k3=st.columns(3)
    with k1:
        st.markdown('<div class="kpi"><div class="kpi-label">Total UPL Case Volume</div><div class="kpi-value">1,450</div><div class="delta-red">↑ 12.5% vs. last week</div></div>',unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi"><div class="kpi-label">Active Rate</div><div class="kpi-value">6.8%</div><div class="delta-green">↓ 2.3% vs. last week</div></div>',unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi"><div class="kpi-label">Compliance Rate</div><div class="kpi-value">93.2%</div><div class="delta-green">↑ 1.7% vs. last week</div></div>',unsafe_allow_html=True)
    st.markdown("</div>",unsafe_allow_html=True)

    # Behavioral identifier
    st.markdown('<div class="card"><div class="card-title"><span class="icon">◉</span>Behavioral Policy Breach Pattern Identifier (1-2 Day Focus)</div>',unsafe_allow_html=True)
    h1,h2=st.columns(2)
    with h1:
        st.markdown('<b style="font-size:11px">1-Day Focus — Repeated Single-Day Non-Valid Cases</b> <span style="float:right;background:#fee2e2;color:#dc2626;border-radius:14px;padding:3px 8px;font-size:9px;font-weight:800">Triage A</span>',unsafe_allow_html=True)
        st.dataframe(pattern1,hide_index=True,use_container_width=True,height=170)
    with h2:
        st.markdown('<b style="font-size:11px">2-Day Focus — Consecutive 2-Day Unexcused Overrides</b> <span style="float:right;background:#dcfce7;color:#15803d;border-radius:14px;padding:3px 8px;font-size:9px;font-weight:800">Triage B</span>',unsafe_allow_html=True)
        st.dataframe(pattern2,hide_index=True,use_container_width=True,height=170)
    st.markdown("</div>",unsafe_allow_html=True)

    # UPL details
    st.markdown('<div class="card"><div class="card-title">▣　UPL Report Details</div>',unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.markdown('<div style="font-size:11px;font-weight:800;margin-bottom:5px">Day-Wise Compliance Matrix</div>',unsafe_allow_html=True)
        st.dataframe(compliance,hide_index=True,use_container_width=True,height=260)
    with b:
        st.markdown('<div style="font-size:11px;font-weight:800;margin-bottom:5px">3P Agency Breakdown</div>',unsafe_allow_html=True)
        st.dataframe(agency,hide_index=True,use_container_width=True,height=220)
        fig=go.Figure(go.Bar(x=agency["Agency"],y=agency["UPL Cases"],marker_color=["#2877d7","#ff9900","#20a9c9","#7967d9","#7b8794"],
                              text=agency["UPL Cases"],textposition="outside"))
        fig.update_layout(height=145,margin=dict(l=5,r=5,t=12,b=10),paper_bgcolor="white",plot_bgcolor="white",
                          xaxis=dict(showgrid=False,tickfont=dict(size=8)),yaxis=dict(gridcolor="#edf2f7",tickfont=dict(size=8)))
        st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
    a,b=st.columns(2)
    with a:
        st.markdown('<div style="font-size:11px;font-weight:800">3. Weekly Trend (Planned vs Unplanned Leave Targets)</div>',unsafe_allow_html=True)
        st.plotly_chart(weekly_trend(),use_container_width=True,config={"displayModeBar":False})
    with b:
        st.markdown('<div style="font-size:11px;font-weight:800">4. Absence Category Distribution</div>',unsafe_allow_html=True)
        st.plotly_chart(donut(),use_container_width=True,config={"displayModeBar":False})
    st.markdown("</div>",unsafe_allow_html=True)

# -----------------------------
# RIGHT
# -----------------------------
with right:
    st.markdown('<div class="card"><div class="card-title"><span class="icon">◉</span>Leave Pattern & Behavioral Abuse Engine <small style="margin-left:5px">(SL / PL Focus)</small><span class="card-link">View Insights →</span></div>',unsafe_allow_html=True)
    k1,k2=st.columns(2)
    with k1:
        st.markdown('<div class="kpi"><div class="kpi-label">Single-Day Strategic Leaves</div><div class="kpi-value">72</div><div style="font-size:10px">Associates flagged</div><div class="delta-red" style="margin-top:10px">↑ 8.4% vs. last week</div></div>',unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi"><div class="kpi-label">2-Day Consecutive Clusters</div><div class="kpi-value">35</div><div style="font-size:10px">Associates flagged<br>(with off-day adjacent patterns)</div><div class="delta-red" style="margin-top:5px">↑ 25.7% vs. last week</div></div>',unsafe_allow_html=True)
    st.markdown('<div style="border:1px solid #dbe4ee;border-radius:7px;padding:10px;margin-top:10px"><div style="font-size:11px;font-weight:800">Weekly Pattern Prevalence (SL / PL)</div>',unsafe_allow_html=True)
    st.plotly_chart(stacked_pattern(),use_container_width=True,config={"displayModeBar":False})
    st.markdown('</div>',unsafe_allow_html=True)

    st.markdown('<div style="border:1px solid #dbe4ee;border-radius:7px;padding:10px;margin-top:10px"><div style="font-size:11px;font-weight:800;margin-bottom:7px">High-Frequency Defaulters Drill-Down <span class="card-link">View All →</span></div>',unsafe_allow_html=True)
    st.dataframe(defaulters,hide_index=True,use_container_width=True,height=255)
    st.markdown("</div></div>",unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown('<div class="side-logo">amazon<span>⌣</span></div>',unsafe_allow_html=True)
    for label,active in [
        ("⌂  Overview",True),("▣  UPL Intelligence",False),("◉  SL / PL Analysis",False),
        ("⌁  Attendance Trends",False),("▤  Compliance Matrix",False),("▥  Reports",False),("⚙  Settings",False)]:
        cls="nav-item nav-active" if active else "nav-item"
        st.markdown(f'<div class="{cls}">{label}</div>',unsafe_allow_html=True)
    st.markdown('<div class="side-foot"><b>amazon</b><br><br>Better People<br>Better Tomorrow</div>',unsafe_allow_html=True)

# UPL drill-down controls at bottom
st.divider()
with st.expander("UPL Report — Full Drill-down Portal", expanded=False):
    d1,d2,d3=st.columns(3)
    d1.metric("Avg. Monthly UPL Rate","8.4%","↓ 1.1% MoM")
    d2.metric("High-Risk Associates","142","↑ 6.2% YTD")
    d3.metric("YTD UPL Trend","−4.8%","Improving")
    st.subheader("Site Drill-down")
    site=pd.DataFrame({"Site":["ADC1","AAN","DXB"],"UPL Cases":[1450,486,392],"Rate":["6.8%","5.9%","4.7%"],"Risk Score":[58,41,36]})
    st.dataframe(site,hide_index=True,use_container_width=True)
    st.info("Connect this section to your production API to replace the demonstration values with live UPL and behavioral-pattern results.")


import re
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="DWD Leave Compliance & Attendance Intelligence Monitor | Abu Dhabi",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "AUH 1"
DWD_RE = re.compile(r"^DWD-AUH1-(\d{8})\.xlsx$", re.I)

# ---------- Design ----------
st.markdown("""
<style>
:root {
  --navy:#131921;
  --navy2:#172f4d;
  --orange:#ff9900;
  --bg:#f4f7fb;
  --card:#ffffff;
  --line:#dbe5f0;
  --text:#142b4a;
  --muted:#60758f;
  --green:#13a56b;
  --red:#ef4444;
  --amber:#f59e0b;
}
html, body, [class*="css"] { font-family: Arial, Helvetica, sans-serif; }
.stApp { background:var(--bg); color:var(--text); }
.block-container { padding:0.55rem 1.15rem 1.2rem 1.15rem; max-width: 100%; }
header[data-testid="stHeader"] { background:var(--navy); height:58px; }
header[data-testid="stHeader"] * { color:white !important; }
[data-testid="stSidebar"] {
  background:linear-gradient(180deg,#102a46 0%,#0e233a 100%);
  min-width:225px; max-width:225px;
}
[data-testid="stSidebar"] * { color:#fff !important; }
[data-testid="stSidebar"] .stButton button {
  border:0; background:transparent; color:#e8f0f9 !important;
  text-align:left; width:100%; border-radius:8px; padding:10px 13px;
  font-weight:600; margin:2px 0;
}
[data-testid="stSidebar"] .stButton button:hover { background:rgba(255,153,0,.16); }
.brand {font-size:31px;font-weight:800;letter-spacing:-1px;margin:10px 8px 30px 8px;}
.brand span {color:var(--orange);}
.side-foot {margin-top:50px;padding:0 8px;color:#dbe7f4;font-size:14px;line-height:1.6;}
.topbar {
  height:58px; background:var(--navy); color:#fff; border-radius:0 0 8px 8px;
  display:flex; align-items:center; padding:0 20px; font-weight:700;
}
.topbar .amazon {font-size:28px; margin-right:26px;}
.topbar .sep {height:28px;width:1px;background:#8392a6;margin-right:22px;}
.topbar .title {font-size:16px;letter-spacing:.1px;}
.topbar .orange {color:var(--orange);margin:0 9px;}
.filter-label {font-size:12px;color:#60758f;font-weight:700;margin:7px 0 4px 2px;}
.card {
  background:#fff;border:1px solid var(--line);border-radius:11px;
  box-shadow:0 2px 8px rgba(25,55,90,.07); padding:13px 15px;
}
.card-title {font-size:17px;font-weight:800;color:var(--text);}
.sub {font-size:12px;color:var(--muted);margin-top:3px;}
.section-head {
  display:flex;justify-content:space-between;align-items:center;
  background:#fff;border:1px solid var(--line);border-radius:11px 11px 0 0;
  padding:11px 14px;font-weight:800;color:var(--text);
}
.metric {
  background:linear-gradient(180deg,#fff,#fbfdff); border:1px solid var(--line);
  border-radius:10px; min-height:108px; padding:13px 15px;
}
.metric .label {font-size:13px;font-weight:700;color:var(--text);}
.metric .value {font-size:31px;font-weight:850;line-height:1.1;margin-top:9px;color:#142b4a;}
.metric .delta {font-size:11px;margin-top:7px;}
.up {color:#ef4444}.down {color:#10a36b}
.kpi-icon {
 display:inline-flex;width:34px;height:34px;border-radius:50%;align-items:center;justify-content:center;
 background:#e9f3ff;color:#2670c9;font-weight:800;float:left;margin-right:9px;
}
.tile {cursor:pointer;background:#fff;border:1px solid var(--line);border-radius:11px;padding:13px 15px;
       box-shadow:0 2px 8px rgba(25,55,90,.07);}
.tile:hover {border-color:#f6b24d;box-shadow:0 3px 12px rgba(255,153,0,.12);}
.orange-link {color:#e87900;font-weight:800;font-size:12px;}
.small-note {font-size:11px;color:#71849b;}
.flag {
 display:inline-block;padding:4px 9px;border-radius:999px;font-size:10px;font-weight:800;
}
.flag-red {background:#fee2e2;color:#b91c1c}.flag-amber {background:#fff0d5;color:#a16207}
.flag-green {background:#dcfce7;color:#15803d}.flag-blue {background:#e0efff;color:#2563eb}
.dataframe {border-radius:8px;}
.stButton button[kind="secondary"] {
 border:1px solid #e6a23c;background:#fff7e8;color:#b75c00;font-weight:800;border-radius:8px;
}
div[data-testid="stMetric"] {background:#fff;border:1px solid var(--line);padding:12px;border-radius:10px;}
div[data-testid="stExpander"] {border:1px solid var(--line);border-radius:10px;background:#fff;}
hr {border:0;border-top:1px solid #e1e8f0;margin:10px 0;}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def clean_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df

def parse_file_date(name):
    m = DWD_RE.match(name)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%d%m%Y").date()

@st.cache_data(show_spinner=False)
def load_file(path_str):
    path = Path(path_str)
    sheets = pd.ExcelFile(path).sheet_names
    out = {"file": path.name, "date": parse_file_date(path.name)}
    if "Roster" in sheets:
        raw = pd.read_excel(path, sheet_name="Roster", header=None)
        header_idx = None
        for i in range(min(20, len(raw))):
            vals = raw.iloc[i].astype(str).str.strip().tolist()
            if "AMZ ID" in vals and "EMP Name" in vals:
                header_idx = i
                break
        if header_idx is not None:
            roster = raw.iloc[header_idx+1:].copy()
            roster.columns = [str(x).strip() for x in raw.iloc[header_idx].tolist()]
            roster = clean_columns(roster)
            roster = roster.dropna(how="all")
            roster = roster[roster.get("AMZ ID", pd.Series(index=roster.index)).astype(str).str.lower().ne("amz id")]
            out["roster"] = roster
        else:
            out["roster"] = pd.DataFrame()
    else:
        out["roster"] = pd.DataFrame()

    if "Dashboard" in sheets:
        out["dashboard"] = pd.read_excel(path, sheet_name="Dashboard", header=None)
    else:
        out["dashboard"] = pd.DataFrame()

    if "DWD RAW File" in sheets:
        out["raw"] = clean_columns(pd.read_excel(path, sheet_name="DWD RAW File"))
    else:
        out["raw"] = pd.DataFrame()
    return out

@st.cache_data(show_spinner=False)
def load_all():
    files = []
    if DATA_DIR.exists():
        for p in DATA_DIR.glob("DWD-AUH1-*.xlsx"):
            d = parse_file_date(p.name)
            if d:
                files.append((d, p))
    files.sort()
    return [load_file(str(p)) for d,p in files]

def safe_col(df, names):
    for n in names:
        if n in df.columns:
            return n
    return None

def fmt_num(x):
    if pd.isna(x): return "—"
    try: return f"{int(round(float(x))):,}"
    except: return str(x)

def fmt_pct(x):
    if pd.isna(x): return "—"
    return f"{float(x)*100:.1f}%"

def add_site_filter(df, site):
    if not site or site == "All sites":
        return df.copy()
    c = safe_col(df, ["Building","Site"])
    if not c: return df.copy()
    return df[df[c].astype(str).str.strip().eq(site)].copy()

def normalize_attendance(df):
    c = safe_col(df, ["Attendance","Attendance "])
    if not c:
        return pd.Series("", index=df.index)
    return df[c].astype(str).str.strip().str.upper()

# ---------- Load actual data ----------
bundle = load_all()
if not bundle:
    st.error("No valid DWD-AUH1-DDMMYYYY.xlsx files were found in the 'AUH 1' folder.")
    st.stop()

all_rosters = []
for b in bundle:
    r = b.get("roster", pd.DataFrame()).copy()
    if not r.empty:
        r["_file_date"] = b["date"]
        all_rosters.append(r)
history = pd.concat(all_rosters, ignore_index=True) if all_rosters else pd.DataFrame()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="brand">amazon<span>⌁</span></div>', unsafe_allow_html=True)
    nav = st.radio(
        "Navigation",
        ["Overview","DWD Intelligence","SL / PL Analysis","Attendance Trends","Compliance Matrix","Reports","Settings"],
        label_visibility="collapsed"
    )
    st.markdown('<div class="side-foot"><b>amazon</b><br><br>Better People<br>Better Tomorrow</div>', unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("""
<div class="topbar">
  <div class="amazon">amazon</div><div class="sep"></div>
  <div class="title">LEAVE COMPLIANCE &amp; ATTENDANCE INTELLIGENCE MONITOR
  <span class="orange">|</span> ABU DHABI</div>
</div>
""", unsafe_allow_html=True)

# ---------- Filters ----------
sites = ["All sites"]
site_col = safe_col(history, ["Building","Site"])
if site_col:
    vals = sorted([x for x in history[site_col].dropna().astype(str).str.strip().unique() if x])
    if vals: sites += vals
default_site = "AUH1" if "AUH1" in sites else sites[0]

c1,c2,c3,c4 = st.columns([1.05,1.25,2.05,.9])
with c1:
    st.markdown('<div class="filter-label">Site / Location</div>', unsafe_allow_html=True)
    site = st.selectbox("site", sites, index=sites.index(default_site), label_visibility="collapsed")
with c2:
    st.markdown('<div class="filter-label">Date Range</div>', unsafe_allow_html=True)
    dates = [b["date"] for b in bundle if b["date"]]
    dmin,dmax=min(dates),max(dates)
    date_range = st.date_input("dates",(dmin,dmax),min_value=dmin,max_value=dmax,label_visibility="collapsed")
with c3:
    st.markdown('<div class="filter-label">Search Associate</div>', unsafe_allow_html=True)
    search = st.text_input("associate","",placeholder="Enter Associate ID or Name...",label_visibility="collapsed")
with c4:
    st.markdown('<div class="filter-label">Last Updated</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="card" style="padding:8px 10px;font-size:11px"><b>Last Updated</b><br>{dmax.strftime("%b %d, %Y")} &nbsp; {datetime.now().strftime("%H:%M")}</div>', unsafe_allow_html=True)

# Filter history by date and site
if isinstance(date_range, tuple) and len(date_range)==2:
    start,end=date_range
else:
    start=end=date_range
h = history[(history["_file_date"]>=start)&(history["_file_date"]<=end)].copy()
h = add_site_filter(h,site)

if search.strip():
    q=search.strip().lower()
    idc=safe_col(h,["AMZ ID","EmpID","Psoft No"])
    nc=safe_col(h,["EMP Name","Emp Name"])
    mask=False
    if idc: mask = h[idc].astype(str).str.lower().str.contains(q,na=False)
    if nc: mask = mask | h[nc].astype(str).str.lower().str.contains(q,na=False)
    h=h[mask]

att=normalize_attendance(h)
total=len(h)
present=int((att=="P").sum())
off=int((att=="OFF").sum())
pl=int((att=="PL").sum())
sl=int((att=="SL").sum())
ab=int((att=="AB").sum())
non_present=total-present-off
active_rate=(non_present/total) if total else np.nan
compliance=(present/(total-off)) if total-off else np.nan
dwd_col=safe_col(h,["DWD dashboard"])
dwd_present=int(h[dwd_col].astype(str).str.strip().eq("Present").sum()) if dwd_col else np.nan

# ---------- Main ----------
if nav in ["Overview","DWD Intelligence","SL / PL Analysis","Attendance Trends","Compliance Matrix","Reports"]:
    left,right=st.columns([1.02,.98],gap="small")

    with left:
        # Clickable single DWD entry tile
        st.markdown("""
        <div class="tile">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div>
              <div class="card-title">▣ &nbsp; DWD Report</div>
              <div class="sub">Daily Workforce &amp; Unplanned Leave — Key Insights</div>
            </div>
            <div class="orange-link">Interactive Drill-down →</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open DWD Report Details", key="dwd_open", type="secondary"):
            st.session_state["dwd_open"] = not st.session_state.get("dwd_open",False)

        m1,m2,m3=st.columns(3)
        with m1:
            st.markdown(f'<div class="metric"><div class="label">Total DWD Case Volume</div><div class="value">{fmt_num(non_present)}</div><div class="delta up">● Source: Roster attendance</div></div>',unsafe_allow_html=True)
        with m2:
            st.markdown(f'<div class="metric"><div class="label">Active Rate</div><div class="value">{fmt_pct(active_rate)}</div><div class="delta">● Calculated from current file set</div></div>',unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div class="metric"><div class="label">Compliance Rate</div><div class="value">{fmt_pct(compliance)}</div><div class="delta down">● Present / scheduled-on roster</div></div>',unsafe_allow_html=True)

        if st.session_state.get("dwd_open",False) or nav=="DWD Intelligence":
            st.markdown('<div class="section-head">▣ &nbsp; DWD Report Details <span class="small-note">Calculated only from loaded DWD files</span></div>',unsafe_allow_html=True)
            st.markdown("<div style='height:6px'></div>",unsafe_allow_html=True)
            a,b=st.columns([1.05,.95])
            with a:
                st.markdown('<div class="card"><b>Day-Wise Attendance / Leave Matrix</b></div>',unsafe_allow_html=True)
                day_rows=[]
                for dt,g in h.groupby("_file_date"):
                    aa=normalize_attendance(g)
                    day_rows.append({"Date":dt.strftime("%d %b"),"Associates":len(g),"Present":int((aa=="P").sum()),
                                     "SL":int((aa=="SL").sum()),"PL":int((aa=="PL").sum()),"Absent":int((aa=="AB").sum()),
                                     "OFF":int((aa=="OFF").sum())})
                if day_rows:
                    st.dataframe(pd.DataFrame(day_rows),hide_index=True,use_container_width=True)
            with b:
                st.markdown('<div class="card"><b>3P Agency Breakdown</b></div>',unsafe_allow_html=True)
                ag=safe_col(h,["3P","Agency"])
                if ag:
                    aa=h[ag].fillna("Unassigned").astype(str).str.strip().replace({"":"Unassigned"}).value_counts().head(8)
                    fig=go.Figure(go.Bar(x=aa.index,y=aa.values,text=aa.values,textposition="outside"))
                    fig.update_layout(height=270,margin=dict(l=10,r=10,t=10,b=45),paper_bgcolor="white",plot_bgcolor="white",
                                      font=dict(color="#173252",size=11),showlegend=False)
                    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                else:
                    st.info("Agency/3P field is not present in the source.")

            a,b=st.columns([1.25,.75])
            with a:
                st.markdown('<div class="card"><b>Leave / Attendance Trend — loaded dates only</b></div>',unsafe_allow_html=True)
                if not h.empty:
                    rows=[]
                    for dt,g in h.groupby("_file_date"):
                        aa=normalize_attendance(g)
                        rows.append((dt,int((aa=="SL").sum()),int((aa=="PL").sum()),int((aa=="AB").sum())))
                    t=pd.DataFrame(rows,columns=["Date","SL","PL","AB"]).sort_values("Date")
                    fig=go.Figure()
                    for col,label in [("SL","SL"),("PL","PL"),("AB","Absent")]:
                        fig.add_trace(go.Scatter(x=t["Date"],y=t[col],mode="lines+markers",name=label,fill="tozeroy" if col=="PL" else None))
                    fig.update_layout(height=260,margin=dict(l=10,r=10,t=10,b=35),paper_bgcolor="white",plot_bgcolor="white",
                                      font=dict(color="#173252",size=11),legend=dict(orientation="h",y=1.12,x=0))
                    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                else: st.info("No records in selected date range.")
            with b:
                st.markdown('<div class="card"><b>Absence Category Distribution</b></div>',unsafe_allow_html=True)
                labels=["SL","PL","Absent","Present"]
                values=[sl,pl,ab,present]
                fig=go.Figure(go.Pie(labels=labels,values=values,hole=.62,textinfo="percent"))
                fig.update_layout(height=260,margin=dict(l=0,r=0,t=10,b=0),paper_bgcolor="white",
                                  legend=dict(font=dict(size=10)),showlegend=True)
                st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})

    with right:
        st.markdown("""
        <div class="tile">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div class="card-title">◉ &nbsp; Leave Pattern &amp; Behavioral Abuse Engine <span class="small-note">(SL / PL Focus)</span></div>
            <div class="orange-link">View Insights →</div>
          </div>
        </div>
        """,unsafe_allow_html=True)
        k1,k2=st.columns(2)
        with k1:
            st.markdown(f'<div class="metric"><div class="label">Single-Day Strategic Leaves</div><div class="value">{sl}</div><div>SL records in loaded source</div><div class="delta up">● No inference of medical validity</div></div>',unsafe_allow_html=True)
        with k2:
            # Genuine 2-day clusters require at least two dated files for the same associate.
            st.markdown(f'<div class="metric"><div class="label">2-Day Consecutive Clusters</div><div class="value">{"—" if len(bundle)<2 else "Calculated"}</div><div>{"Requires ≥2 dated DWD files" if len(bundle)<2 else "See pattern engine below"}</div><div class="delta">● No fabricated clusters</div></div>',unsafe_allow_html=True)

        st.markdown('<div class="section-head">Weekly Pattern Prevalence (SL / PL)</div>',unsafe_allow_html=True)
        # Use actual dates. If there is only one file, only that date is plotted.
        if not h.empty:
            rows=[]
            for dt,g in h.groupby("_file_date"):
                aa=normalize_attendance(g)
                rows.append({"Date":dt,"SL":int((aa=="SL").sum()),"PL":int((aa=="PL").sum()),"Absent":int((aa=="AB").sum())})
            t=pd.DataFrame(rows).sort_values("Date")
            fig=go.Figure()
            fig.add_trace(go.Bar(x=t["Date"],y=t["SL"],name="SL"))
            fig.add_trace(go.Bar(x=t["Date"],y=t["PL"],name="PL"))
            fig.add_trace(go.Bar(x=t["Date"],y=t["Absent"],name="Absent"))
            fig.update_layout(barmode="stack",height=300,margin=dict(l=10,r=10,t=20,b=40),paper_bgcolor="white",plot_bgcolor="white",
                              font=dict(color="#173252",size=11),legend=dict(orientation="h",y=1.08,x=0))
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            if len(bundle)<7:
                st.caption("Only loaded DWD dates are shown. Add more DWD-AUH1-DDMMYYYY.xlsx files to populate the historical pattern timeline. No missing dates are filled with synthetic values.")
        else:
            st.info("No source records for the selected date range.")

        st.markdown('<div class="section-head">High-Frequency Defaulters Drill-Down</div>',unsafe_allow_html=True)
        # Pattern engine: only flags repeated SL/PL activity when multiple dated files exist.
        idc=safe_col(history,["AMZ ID","EmpID","Psoft No"])
        nc=safe_col(history,["EMP Name","Emp Name"])
        if idc and nc and len(bundle)>=2:
            hh=add_site_filter(history,site)
            hh=hh[(hh["_file_date"]>=start)&(hh["_file_date"]<=end)].copy()
            hh["_att"]=normalize_attendance(hh)
            grp=hh.groupby([idc,nc],dropna=False)
            rows=[]
            for (aid,name),g in grp:
                dates_sl=sorted(g.loc[g["_att"]=="SL","_file_date"].dropna().unique())
                dates_pl=sorted(g.loc[g["_att"]=="PL","_file_date"].dropna().unique())
                two=0
                for i in range(1,len(dates_sl)):
                    if dates_sl[i]-dates_sl[i-1] == timedelta(days=1):
                        two += 1
                one=max(0,len(dates_sl)-two*2)
                if one+two+len(dates_pl)>0:
                    risk=min(100, one*10+two*25+len(dates_pl)*4)
                    rows.append([aid,name,one,two,len(dates_pl),risk])
            drill=pd.DataFrame(rows,columns=["Associate ID","Name","1-Day SL Count","2-Day SL Cluster Count","1-Day PL Count","Disruption Risk Index"])
            if not drill.empty:
                drill=drill.sort_values("Disruption Risk Index",ascending=False).head(15)
                drill["Disruption Risk Index"]=drill["Disruption Risk Index"].map(lambda x:f"{int(x)}%")
                st.dataframe(drill,hide_index=True,use_container_width=True)
            else:
                st.info("No repeated SL/PL pattern meets the review threshold in the selected source files.")
        else:
            st.info("High-frequency and 2-day cluster detection needs at least two dated DWD files containing Associate ID/Name and Attendance. The current workbook contains one dated roster, so the app intentionally does not manufacture historical patterns.")

# ---------- Settings ----------
if nav=="Settings":
    st.markdown('<div class="card"><div class="card-title">Data Source Settings</div><p class="sub">The app reads only files stored in <b>AUH 1</b> whose names match <b>DWD-AUH1-DDMMYYYY.xlsx</b>.</p></div>',unsafe_allow_html=True)
    st.markdown("### Loaded DWD files")
    st.dataframe(pd.DataFrame([{"File":b["file"],"Date":b["date"],"Roster rows":len(b.get("roster",[]))} for b in bundle]),hide_index=True,use_container_width=True)
    st.info("Add additional dated DWD files to AUH 1 and refresh the Streamlit app. Historical SL/PL clusters will then be calculated from actual dated records.")

if nav=="Reports":
    st.markdown('<div class="card"><div class="card-title">Source Audit</div><div class="sub">No synthetic records are used.</div></div>',unsafe_allow_html=True)
    st.write(f"Loaded files: {len(bundle)}")
    st.write(f"Records after filters: {len(h):,}")
    st.write("Workbook sheets detected:", ", ".join(pd.ExcelFile(bundle[0]["file"] if False else DATA_DIR / bundle[0]["file"]).sheet_names))


from flask import Flask, render_template_string

app = Flask(__name__)

HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Leave Compliance & Attendance Intelligence Monitor | Abu Dhabi</title>
<style>
*{box-sizing:border-box}html,body{margin:0;min-height:100%;font-family:Arial,Helvetica,sans-serif;background:#f3f7fb;color:#142b4d}
body{overflow-x:auto}
:root{
 --navy:#131921;--side:#10243d;--orange:#ff9900;--blue:#2877d7;--green:#19a766;
 --border:#dce6f0;--muted:#61758f;--red:#ef3b3b;--purple:#7358d8;
}
.app{min-height:100vh;background:linear-gradient(135deg,#edf3f8 0,#f8fafc 50%,#edf3f8 100%)}
.header{height:68px;background:var(--navy);color:#fff;display:flex;align-items:center;padding:0 22px 0 28px;gap:20px;box-shadow:0 2px 7px #07111e55}
.logo{font-size:31px;font-weight:800;letter-spacing:-1.5px;line-height:1}
.logo:after{content:"";display:block;width:38px;height:8px;border-bottom:4px solid var(--orange);border-radius:50%;transform:translate(34px,-5px) rotate(-6deg)}
.sep{height:30px;width:1px;background:#9ba6b4}
.title{font-size:17px;font-weight:800;letter-spacing:.1px;flex:1}.title b{color:var(--orange);margin:0 10px}
.head-icons{display:flex;align-items:center;gap:21px;font-size:18px}.bell{position:relative}.badge{position:absolute;right:-9px;top:-8px;background:#ff7a00;border-radius:50%;font-size:10px;padding:3px 5px;font-weight:800}.user{display:flex;align-items:center;gap:8px;font-size:11px;font-weight:700}.avatar{width:28px;height:28px;border-radius:50%;background:#eef2f7;color:#74859a;display:grid;place-items:center;font-size:17px}

.shell{display:flex;min-width:1220px}
.sidebar{width:190px;min-height:calc(100vh - 68px);background:linear-gradient(#10243d,#0e2138);color:#dce8f5;padding:16px 9px;position:relative}
.side-logo{font-size:27px;font-weight:800;color:#fff;padding:4px 20px 19px}.side-logo:after{content:"";display:inline-block;width:28px;height:6px;border-bottom:3px solid var(--orange);border-radius:50%;transform:translate(-26px,8px) rotate(-8deg)}
.nav{display:flex;align-items:center;gap:13px;height:43px;margin:3px 4px;padding:0 13px;border-radius:7px;font-size:13px;font-weight:600;white-space:nowrap}.nav.active{background:var(--orange);color:#fff}.nav .ico{font-size:18px;width:17px;text-align:center}.side-bottom{position:absolute;bottom:20px;left:28px;color:#fff;line-height:1.55;font-size:12px}.side-bottom strong{font-size:16px}

main{flex:1;padding:17px 18px 22px;min-width:1030px}
.filters{display:grid;grid-template-columns:1.05fr 1.22fr 1.65fr .75fr;gap:14px;margin-bottom:14px}
.filter label{display:block;color:#536a87;font-size:11px;font-weight:700;margin:0 0 5px 7px}
.field{height:42px;background:#fff;border:1px solid var(--border);border-radius:8px;display:flex;align-items:center;padding:0 11px;color:#394b64;font-size:12px;box-shadow:0 1px 2px #152c4810}
.field .small{font-size:16px;margin-right:9px;color:#6c809a}.field .arrow{margin-left:auto;font-size:17px}.search{color:#8a99ab}.updated{font-size:9px;line-height:1.45;padding-left:13px}.updated b{font-size:9px;color:#536a87}.updated strong{font-size:10px;color:#536a87}

.columns{display:grid;grid-template-columns:1.02fr .98fr;gap:14px;align-items:start}
.card{background:#fff;border:1px solid var(--border);border-radius:10px;box-shadow:0 2px 9px #0e2b4812;padding:10px;margin-bottom:11px}
.card-head{height:40px;display:flex;align-items:center;gap:9px}.head-icon{width:35px;height:35px;border-radius:9px;background:#fff0da;color:#ef9000;display:grid;place-items:center;font-size:19px;font-weight:800}.card-head h2{font-size:17px;margin:0;font-weight:800;color:#152e50}.sub{font-size:10px;color:#647995;margin:1px 0 0 44px}.link{margin-left:auto;color:#ef8b00;font-size:10px;font-weight:800;cursor:pointer}.hero{padding:10px 10px 11px;position:relative;overflow:hidden}.hero:after{content:"";position:absolute;right:-8px;top:-22px;width:115px;height:70px;background:linear-gradient(135deg,transparent 0 38%,#ffd99b 39% 59%,#ff9900 60% 100%);border-radius:30px;opacity:.9}

.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:11px}.kpi{border:1px solid #d8e5f1;border-radius:8px;min-height:91px;padding:11px 12px;background:linear-gradient(#fff,#f9fcff)}.kpi-label{font-size:11px;font-weight:800;color:#183352}.kpi-value{font-size:28px;font-weight:800;margin:5px 0 3px;color:#122b4c}.delta{font-size:9px}.red{color:#ef3b3b}.green{color:#19a766}

.details-title{font-size:14px;font-weight:800;display:flex;align-items:center;gap:8px;margin-bottom:9px}.details-title .collapse{margin-left:auto;color:#60758e}
.mini-grid{display:grid;grid-template-columns:1.12fr 1fr;gap:8px}.mini{border:1px solid #dce6f0;border-radius:8px;padding:7px;background:#fff}.mini h3{font-size:10px;margin:0 0 7px;font-weight:800}.mini2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
table{width:100%;border-collapse:separate;border-spacing:0;font-size:8.6px;color:#314963}th{background:#f5f8fc;color:#4d6681;font-weight:800;border-bottom:1px solid #d9e3ee;padding:6px 4px;text-align:center}td{padding:6px 4px;border-bottom:1px solid #e8eef5;text-align:center}tbody tr:last-child td{border-bottom:0}.bad{color:#e22e38;background:#fff0f1}.good{color:#148b5a;background:#eefbf5}.rate{font-weight:700}.agency td:first-child{text-align:left}.agency th:first-child{text-align:left}

.chart{height:145px;position:relative;padding:4px 4px 0}.bars{height:115px;display:flex;align-items:flex-end;justify-content:space-around;border-bottom:1px solid #d8e3ee;background:repeating-linear-gradient(to top,transparent 0,transparent 27px,#eaf0f6 28px)}.barwrap{width:13%;height:100%;display:flex;align-items:flex-end;justify-content:center;gap:0;position:relative}.bar{width:70%;background:var(--blue);border-radius:3px 3px 0 0;min-height:4px}.bar.o{background:#ff9900}.bar.c{background:#20a8bd}.bar.p{background:#7967d9}.bar.g{background:#7b8794}.barlabel{position:absolute;bottom:-20px;font-size:7px;color:#5c7087;white-space:nowrap}.barvalue{position:absolute;top:calc(100% - var(--h) - 13px);font-size:8px;font-weight:800;color:#233b57}
.svgchart{width:100%;height:158px}.legend{display:flex;gap:13px;justify-content:center;font-size:8px;color:#536a83;margin-top:-2px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:4px}

.pattern{margin-top:11px}.pattern-grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}.pattern-box h3{font-size:10px;margin:0 0 7px;line-height:1.3}.tag{float:right;border-radius:12px;padding:3px 7px;font-size:8px;font-weight:800}.tag.a{background:#ffe0e3;color:#dc2c3c}.tag.b{background:#ddf8e9;color:#178653}.pattern-table{overflow:hidden;border:1px solid #dce6f0;border-radius:7px}.pattern-table table{font-size:8px}.risk-high{color:#fff;background:#ef4444;border-radius:9px;padding:3px 7px;font-weight:800}.risk-mid{color:#7c4500;background:#ffd66b;border-radius:9px;padding:3px 7px;font-weight:800}.risk-low{color:#fff;background:#18a566;border-radius:9px;padding:3px 7px;font-weight:800}

.stack{height:210px;position:relative;padding-top:10px}.stack svg{width:100%;height:190px}.callout{position:absolute;top:3px;background:#ff9900;color:white;font-size:8px;font-weight:800;border-radius:3px;padding:4px 7px}.callout.mon{left:25%}.callout.fri{right:9%}.callout:after{content:"";position:absolute;left:50%;top:100%;border:5px solid transparent;border-top-color:#555;transform:translateX(-50%)}

.def{margin-top:10px}.def table{font-size:8px}.def th{line-height:1.05}.valid{color:#168f5d;font-weight:800}.check{display:inline-grid;place-items:center;background:#18aa67;color:#fff;width:14px;height:14px;border-radius:50%;margin-right:3px;font-size:9px}

.modal{display:none;position:fixed;inset:0;background:#08162699;z-index:20;align-items:center;justify-content:center;padding:30px}.modal.show{display:flex}.modal-box{width:min(1050px,94vw);max-height:90vh;overflow:auto;background:#f7fafc;border-radius:12px;box-shadow:0 18px 60px #0007;border:1px solid #cbd8e6}.modal-head{background:var(--navy);color:#fff;padding:14px 18px;display:flex;align-items:center}.modal-head h2{margin:0;font-size:16px}.close{margin-left:auto;background:#fff1;color:white;border:1px solid #ffffff55;border-radius:5px;padding:5px 9px;cursor:pointer}.modal-body{padding:14px}.portal-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.portal-kpi{background:#fff;border:1px solid var(--border);border-radius:8px;padding:13px}.portal-kpi b{font-size:10px}.portal-kpi strong{display:block;font-size:24px;margin:7px 0}.portal-section{margin-top:12px;background:#fff;border:1px solid var(--border);border-radius:8px;padding:12px}.portal-section h3{font-size:12px;margin:0 0 10px}

@media(max-width:1300px){.title{font-size:14px}.head-icons{gap:10px}.sidebar{width:175px}.shell{min-width:1120px}main{padding:14px}.columns{gap:10px}.filters{gap:9px}}
</style>
</head>
<body>
<div class="app">
<header class="header">
  <div class="logo">amazon</div><div class="sep"></div>
  <div class="title">LEAVE COMPLIANCE &amp; ATTENDANCE INTELLIGENCE MONITOR <b>|</b> ABU DHABI</div>
  <div class="head-icons"><span class="bell">♧<i class="badge">3</i></span><span>?</span><span class="user"><span class="avatar">●</span>HR Analytics　⌄</span></div>
</header>
<div class="shell">
<aside class="sidebar">
  <div class="side-logo">amazon</div>
  <div class="nav active"><span class="ico">⌂</span>Overview</div>
  <div class="nav"><span class="ico">▣</span>UPL Intelligence</div>
  <div class="nav"><span class="ico">▣</span>SL / PL Analysis</div>
  <div class="nav"><span class="ico">⌁</span>Attendance Trends</div>
  <div class="nav"><span class="ico">▤</span>Compliance Matrix</div>
  <div class="nav"><span class="ico">▥</span>Reports</div>
  <div class="nav"><span class="ico">⚙</span>Settings</div>
  <div class="side-bottom"><strong>amazon</strong><br><br>Better People<br>Better Tomorrow</div>
</aside>

<main>
<section class="filters">
  <div class="filter"><label>Site / Location</label><div class="field"><span class="small">⌖</span>Abu Dhabi (ADC1)<span class="arrow">⌄</span></div></div>
  <div class="filter"><label>Date Range</label><div class="field"><span class="small">▣</span>Apr 21, 2025 – Apr 27, 2025<span class="arrow">▣</span></div></div>
  <div class="filter"><label>Search Associate</label><div class="field search"><span class="small">⌕</span>Enter Associate ID or Name...<span class="arrow">⌕</span></div></div>
  <div class="filter"><label>&nbsp;</label><div class="field updated"><span style="font-size:16px;margin-right:8px">◷</span><span><b>Last Updated</b><br><strong>Apr 27, 2025　14:32</strong>　↻</span></div></div>
</section>

<div class="columns">
<section>
  <div class="card hero">
    <div class="card-head"><div class="head-icon">▣</div><div><h2>UPL Report</h2><div class="sub">Unplanned Leave (UPL) — Key Insights</div></div><div class="link" onclick="openModal()">View Full Report →</div></div>
    <div class="kpis">
      <div class="kpi"><div class="kpi-label">⚫　Total UPL Case Volume</div><div class="kpi-value">1,450</div><div class="delta red">↑ 12.5%　vs. last week</div></div>
      <div class="kpi"><div class="kpi-label">🟢　Active Rate</div><div class="kpi-value">6.8%</div><div class="delta green">↓ 2.3%　vs. last week</div></div>
      <div class="kpi"><div class="kpi-label">🟣　Compliance Rate</div><div class="kpi-value">93.2%</div><div class="delta green">↑ 1.7%　vs. last week</div></div>
    </div>
  </div>

  <div class="card pattern">
    <div class="details-title"><span style="color:#ef9000">◉</span> Behavioral Policy Breach Pattern Identifier (1-2 Day Focus)</div>
    <div class="pattern-grid">
      <div class="pattern-box"><h3>1-Day Focus — Repeated Single-Day Non-Valid Cases <span class="tag a">Triage A</span></h3>
        <div class="pattern-table"><table><thead><tr><th>Site</th><th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th><th>Incidence</th><th>Risk</th></tr></thead><tbody>
        <tr><td>ADC1</td><td>12</td><td class="bad">18</td><td>9</td><td>7</td><td>11</td><td class="bad">14</td><td>8</td><td>8.2%</td><td><span class="risk-high">72</span></td></tr>
        <tr><td>AAN</td><td>8</td><td>11</td><td>6</td><td>5</td><td>8</td><td>9</td><td>6</td><td>5.6%</td><td><span class="risk-mid">58</span></td></tr>
        <tr><td>DXB</td><td>4</td><td>7</td><td>5</td><td>4</td><td>6</td><td>7</td><td>5</td><td>3.9%</td><td><span class="risk-low">42</span></td></tr>
        </tbody></table></div>
      </div>
      <div class="pattern-box"><h3>2-Day Focus — Consecutive 2-Day Unexcused Overrides <span class="tag b">Triage B</span></h3>
        <div class="pattern-table"><table><thead><tr><th>Site</th><th>Sun</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th><th>Incidence</th><th>Risk</th></tr></thead><tbody>
        <tr><td>ADC1</td><td>5</td><td class="bad">9</td><td>7</td><td>4</td><td>8</td><td class="bad">12</td><td>6</td><td>6.1%</td><td><span class="risk-high">68</span></td></tr>
        <tr><td>AAN</td><td>3</td><td>5</td><td>4</td><td>3</td><td>6</td><td>8</td><td>4</td><td>4.2%</td><td><span class="risk-mid">51</span></td></tr>
        <tr><td>DXB</td><td>1</td><td>2</td><td>2</td><td>1</td><td>3</td><td>5</td><td>2</td><td>2.1%</td><td><span class="risk-low">34</span></td></tr>
        </tbody></table></div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="details-title">▣　UPL Report Details <span class="collapse">⌃</span></div>
    <div class="mini-grid">
      <div class="mini"><h3>▣　Day-Wise Compliance Matrix</h3><table><thead><tr><th>Day</th><th>Total Associates</th><th>Compliant</th><th>Non-Compliant</th><th>Compliance Rate</th></tr></thead><tbody>
        <tr><td>Sun</td><td>1,820</td><td>1,742</td><td class="bad">78</td><td class="good rate">95.7%</td></tr>
        <tr><td>Mon</td><td>1,834</td><td>1,658</td><td class="bad">176</td><td class="bad rate">90.3%</td></tr>
        <tr><td>Tue</td><td>1,812</td><td>1,721</td><td class="bad">91</td><td class="good rate">94.9%</td></tr>
        <tr><td>Wed</td><td>1,806</td><td>1,736</td><td class="bad">70</td><td class="good rate">96.1%</td></tr>
        <tr><td>Thu</td><td>1,795</td><td>1,719</td><td class="bad">76</td><td class="good rate">95.8%</td></tr>
        <tr><td>Fri</td><td>1,828</td><td>1,642</td><td class="bad">186</td><td class="bad rate">89.8%</td></tr>
        <tr><td>Sat</td><td>1,801</td><td>1,738</td><td class="bad">63</td><td class="good rate">96.5%</td></tr>
      </tbody></table></div>
      <div class="mini"><h3>♟　3P Agency Breakdown <span style="float:right;font-weight:500">3P Agency UPL Volume (Altair)</span></h3>
        <table class="agency"><thead><tr><th>Agency</th><th>Total Associates</th><th>UPL Cases</th><th>% of Total</th></tr></thead><tbody>
        <tr><td>Randstad</td><td>520</td><td>342</td><td>23.6%</td></tr><tr><td>Manpower</td><td>468</td><td>298</td><td>20.6%</td></tr><tr><td>Adecco</td><td>412</td><td>261</td><td>18.0%</td></tr><tr><td>Kelly Services</td><td>358</td><td>223</td><td>15.4%</td></tr><tr><td>Others</td><td>289</td><td>196</td><td>13.5%</td></tr>
        </tbody></table>
        <div class="chart"><div class="bars">
          <div class="barwrap"><div class="bar" style="height:86%"></div><span class="barvalue" style="top:5px">342</span><span class="barlabel">Randstad</span></div>
          <div class="barwrap"><div class="bar o" style="height:75%"></div><span class="barvalue" style="top:18px">298</span><span class="barlabel">Manpower</span></div>
          <div class="barwrap"><div class="bar c" style="height:65%"></div><span class="barvalue" style="top:30px">261</span><span class="barlabel">Adecco</span></div>
          <div class="barwrap"><div class="bar p" style="height:55%"></div><span class="barvalue" style="top:43px">223</span><span class="barlabel">Kelly</span></div>
          <div class="barwrap"><div class="bar g" style="height:49%"></div><span class="barvalue" style="top:51px">196</span><span class="barlabel">Others</span></div>
        </div></div>
      </div>
    </div>
    <div class="mini2" style="margin-top:8px">
      <div class="mini"><h3>3. Weekly Trend (Planned vs Unplanned Leave Targets)</h3>
        <svg class="svgchart" viewBox="0 0 520 155" preserveAspectRatio="none">
          <g stroke="#e7edf4" stroke-width="1"><line x1="38" y1="20" x2="510" y2="20"/><line x1="38" y1="55" x2="510" y2="55"/><line x1="38" y1="90" x2="510" y2="90"/><line x1="38" y1="125" x2="510" y2="125"/></g>
          <polygon points="40,68 115,55 190,61 265,74 340,85 415,78 505,92 505,128 40,128" fill="#2877d711"/>
          <polyline points="40,68 115,55 190,61 265,74 340,85 415,78 505,92" fill="none" stroke="#2877d7" stroke-width="2.5"/>
          <polyline points="40,106 115,96 190,102 265,108 340,116 415,111 505,117" fill="none" stroke="#ff9900" stroke-width="2.5"/>
          <g fill="#2877d7"><circle cx="40" cy="68" r="3"/><circle cx="115" cy="55" r="3"/><circle cx="190" cy="61" r="3"/><circle cx="265" cy="74" r="3"/><circle cx="340" cy="85" r="3"/><circle cx="415" cy="78" r="3"/><circle cx="505" cy="92" r="3"/></g>
          <g font-size="8" fill="#566d86"><text x="33" y="148">Sun</text><text x="108" y="148">Mon</text><text x="183" y="148">Tue</text><text x="258" y="148">Wed</text><text x="333" y="148">Thu</text><text x="408" y="148">Fri</text><text x="498" y="148">Sat</text></g>
          <g font-size="8" fill="#2877d7" font-weight="700"><text x="37" y="61">180</text><text x="110" y="48">195</text><text x="185" y="54">188</text><text x="260" y="67">176</text><text x="335" y="78">165</text><text x="410" y="71">172</text><text x="500" y="85">160</text></g>
          <g font-size="8" fill="#e98900" font-weight="700"><text x="37" y="101">72</text><text x="110" y="91">98</text><text x="185" y="97">86</text><text x="260" y="103">79</text><text x="335" y="111">68</text><text x="410" y="106">74</text><text x="500" y="112">63</text></g>
        </svg><div class="legend"><span><i class="dot" style="background:#2877d7"></i>Planned Leave (Target)</span><span><i class="dot" style="background:#ff9900"></i>Unplanned Leave (Target)</span></div>
      </div>
      <div class="mini"><h3>4. Absence Category Distribution</h3>
        <div style="display:flex;align-items:center;gap:14px;height:158px">
          <svg width="145" height="145" viewBox="0 0 145 145"><circle cx="72.5" cy="72.5" r="47" fill="none" stroke="#2877d7" stroke-width="27" stroke-dasharray="161 134" transform="rotate(-90 72.5 72.5)"/><circle cx="72.5" cy="72.5" r="47" fill="none" stroke="#ff9900" stroke-width="27" stroke-dasharray="84 211" stroke-dashoffset="-161" transform="rotate(-90 72.5 72.5)"/><circle cx="72.5" cy="72.5" r="47" fill="none" stroke="#19a766" stroke-width="27" stroke-dasharray="51 244" stroke-dashoffset="-245" transform="rotate(-90 72.5 72.5)"/><text x="72.5" y="69" text-anchor="middle" font-size="17" font-weight="800" fill="#172f50">1,450</text><text x="72.5" y="83" text-anchor="middle" font-size="8" fill="#61758f">Total UPL Cases</text></svg>
          <div style="font-size:9px;line-height:1.8"><div><span class="dot" style="background:#2877d7"></span>Medical Certified<br><b style="margin-left:11px">792 (54.5%)</b></div><div><span class="dot" style="background:#ff9900"></span>Single-day Unannounced<br><b style="margin-left:11px">411 (28.3%)</b></div><div><span class="dot" style="background:#19a766"></span>Personal Emergency<br><b style="margin-left:11px">247 (17.2%)</b></div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<section>
  <div class="card">
    <div class="card-head"><div class="head-icon">◉</div><div><h2>Leave Pattern &amp; Behavioral Abuse Engine <span style="font-size:10px">(SL / PL Focus)</span></h2></div><div class="link">View Insights →</div></div>
    <div class="kpis" style="grid-template-columns:1fr 1fr">
      <div class="kpi"><div class="kpi-label">🔵　Single-Day Strategic Leaves</div><div class="kpi-value">72</div><div style="font-size:10px">Associates flagged</div><div class="delta red" style="margin-top:12px">↑ 8.4%　vs. last week</div></div>
      <div class="kpi"><div class="kpi-label">🔵　2-Day Consecutive Clusters</div><div class="kpi-value">35</div><div style="font-size:10px">Associates flagged<br>(with off-day adjacent patterns)</div><div class="delta red" style="margin-top:6px">↑ 25.7%　vs. last week</div></div>
    </div>
    <div class="mini" style="margin-top:10px"><h3>Weekly Pattern Prevalence (SL / PL)</h3>
      <div class="stack">
        <span class="callout mon">Monday Spike</span><span class="callout fri">Friday Spike</span>
        <svg viewBox="0 0 620 220" preserveAspectRatio="none">
          <g stroke="#e5ebf2" stroke-width="1"><line x1="35" y1="24" x2="605" y2="24"/><line x1="35" y1="69" x2="605" y2="69"/><line x1="35" y1="114" x2="605" y2="114"/><line x1="35" y1="159" x2="605" y2="159"/></g>
          <g font-size="9" fill="#63768d"><text x="7" y="162">50</text><text x="7" y="117">100</text><text x="7" y="72">150</text><text x="7" y="27">200</text></g>
          <g>
          <rect x="55" y="130" width="38" height="29" fill="#2877d7"/><rect x="55" y="105" width="38" height="25" fill="#ff9900"/><rect x="55" y="71" width="38" height="34" fill="#19a766"/>
          <rect x="135" y="94" width="38" height="65" fill="#2877d7"/><rect x="135" y="33" width="38" height="61" fill="#ff9900"/><rect x="135" y="0" width="38" height="33" fill="#19a766"/>
          <rect x="215" y="113" width="38" height="46" fill="#2877d7"/><rect x="215" y="73" width="38" height="40" fill="#ff9900"/><rect x="215" y="31" width="38" height="42" fill="#19a766"/>
          <rect x="295" y="120" width="38" height="39" fill="#2877d7"/><rect x="295" y="88" width="38" height="32" fill="#ff9900"/><rect x="295" y="53" width="38" height="35" fill="#19a766"/>
          <rect x="375" y="125" width="38" height="34" fill="#2877d7"/><rect x="375" y="96" width="38" height="29" fill="#ff9900"/><rect x="375" y="64" width="38" height="32" fill="#19a766"/>
          <rect x="455" y="101" width="38" height="58" fill="#2877d7"/><rect x="455" y="49" width="38" height="52" fill="#ff9900"/><rect x="455" y="0" width="38" height="49" fill="#19a766"/>
          <rect x="535" y="135" width="38" height="24" fill="#2877d7"/><rect x="535" y="112" width="38" height="23" fill="#ff9900"/><rect x="535" y="82" width="38" height="30" fill="#19a766"/>
          </g>
          <g font-size="9" fill="#526981" text-anchor="middle"><text x="74" y="179">Sun</text><text x="154" y="179">Mon</text><text x="234" y="179">Tue</text><text x="314" y="179">Wed</text><text x="394" y="179">Thu</text><text x="474" y="179">Fri</text><text x="554" y="179">Sat</text></g>
          <g font-size="8" fill="#fff" text-anchor="middle" font-weight="700"><text x="154" y="120">72</text><text x="154" y="67">68</text><text x="154" y="19">58</text><text x="474" y="122">64</text><text x="474" y="77">58</text><text x="474" y="28">54</text></g>
        </svg>
      </div>
      <div class="legend"><span><i class="dot" style="background:#2877d7"></i>1-Day SL</span><span><i class="dot" style="background:#ff9900"></i>2-Day SL Cluster</span><span><i class="dot" style="background:#19a766"></i>1-Day PL</span></div>
    </div>
  </div>

  <div class="card def">
    <div class="details-title">High-Frequency Defaulters Drill-Down <span class="link">View All →</span></div>
    <table><thead><tr><th>#</th><th>Associate ID</th><th>Name</th><th>1-Day SL<br>Count</th><th>2-Day SL<br>Cluster Count</th><th>1-Day PL<br>Count</th><th>Disruption<br>Risk Index</th><th>Medical Certificate<br>Status</th></tr></thead><tbody>
      <tr><td>1</td><td>A102934</td><td>Ahmed Khan</td><td>6</td><td>4</td><td>3</td><td><span class="risk-high">92%</span></td><td class="valid"><span class="check">✓</span>VALIDATED<br><small>(Doctor Slip)</small></td></tr>
      <tr><td>2</td><td>A104221</td><td>Fatima Al Mansoori</td><td>5</td><td>3</td><td>2</td><td><span class="risk-high" style="background:#ff8b19">78%</span></td><td class="valid"><span class="check">✓</span>VALIDATED<br><small>(Doctor Slip)</small></td></tr>
      <tr><td>3</td><td>A107563</td><td>Rahil Shaikh</td><td>4</td><td>3</td><td>1</td><td><span class="risk-high" style="background:#ff7a19">65%</span></td><td class="valid"><span class="check">✓</span>VALIDATED<br><small>(Doctor Slip)</small></td></tr>
      <tr><td>4</td><td>A109876</td><td>Saeed Al Balushi</td><td>3</td><td>2</td><td>2</td><td><span class="risk-mid">52%</span></td><td class="valid"><span class="check">✓</span>VALIDATED<br><small>(Doctor Slip)</small></td></tr>
      <tr><td>5</td><td>A112349</td><td>Noora Al Dhaheri</td><td>3</td><td>2</td><td>1</td><td><span class="risk-mid">48%</span></td><td class="valid"><span class="check">✓</span>VALIDATED<br><small>(Doctor Slip)</small></td></tr>
    </tbody></table>
  </div>
</section>
</div>
</main>
</div>
</div>

<div class="modal" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="modal-box">
    <div class="modal-head"><h2>UPL Report — Full Drill-down Portal</h2><button class="close" onclick="closeModal()">Close ✕</button></div>
    <div class="modal-body">
      <div class="portal-grid">
        <div class="portal-kpi"><b>Avg. Monthly UPL Rate</b><strong>8.4%</strong><span class="green">↓ 1.1% MoM</span></div>
        <div class="portal-kpi"><b>High-Risk Associates</b><strong>142</strong><span class="red">↑ 6.2% YTD</span></div>
        <div class="portal-kpi"><b>YTD UPL Trend</b><strong>−4.8%</strong><span class="green">Improving</span></div>
      </div>
      <div class="portal-section"><h3>Target Variance</h3>
        <svg viewBox="0 0 950 190" style="width:100%;height:190px"><g stroke="#e5ebf2"><line x1="45" y1="25" x2="925" y2="25"/><line x1="45" y1="75" x2="925" y2="75"/><line x1="45" y1="125" x2="925" y2="125"/><line x1="45" y1="165" x2="925" y2="165"/></g><polyline points="50,80 195,55 340,67 485,82 630,95 775,73 920,88" fill="none" stroke="#2877d7" stroke-width="4"/><polyline points="50,125 195,104 340,116 485,123 630,137 775,128 920,143" fill="none" stroke="#ff9900" stroke-width="4"/></svg>
      </div>
      <div class="portal-section"><h3>Site Drill-down</h3><table><thead><tr><th>Site</th><th>UPL Cases</th><th>UPL Rate</th><th>Risk Score</th><th>Review Queue</th></tr></thead><tbody><tr><td>ADC1</td><td>1,450</td><td>6.8%</td><td>58</td><td>142</td></tr><tr><td>AAN</td><td>486</td><td>5.9%</td><td>41</td><td>67</td></tr><tr><td>DXB</td><td>392</td><td>4.7%</td><td>36</td><td>42</td></tr></tbody></table></div>
    </div>
  </div>
</div>
<script>
function openModal(){document.getElementById('modal').classList.add('show')}
function closeModal(){document.getElementById('modal').classList.remove('show')}
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal()})
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    print("Opening: http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)

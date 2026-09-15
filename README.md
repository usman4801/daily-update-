# People Analytics Dashboard (Streamlit)

A Streamlit replica of the "People Analytics — Sick Leave Pattern" dashboard.
**Every number on the dashboard is computed live from the Excel file you upload
— nothing is hardcoded.**

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

## Data format

Upload an `.xlsx` workbook from the sidebar. Use the **Download Excel template**
button in the app to get a pre-formatted starter file.

### Sheet `LeaveEvents` (required — one row per sick-leave event)
| Column | Type | Notes |
|---|---|---|
| `EmployeeID` | text | unique employee id |
| `EmployeeName` | text | |
| `Department` | text | |
| `LeaveDate` | date | date the leave started |
| `DurationDays` | number | `1` or `2` (2+ is treated as "2-day") |

### Sheet `Employees` (optional)
If omitted, the employee roster (and Total Employees count) is derived
automatically from unique employees in `LeaveEvents`.
| Column | Type |
|---|---|
| `EmployeeID` | text |
| `EmployeeName` | text |
| `Department` | text |

### Sheet `Coaching` (optional — powers the "Recent Coaching Activity" feed)
If omitted, that panel shows an empty state instead of fake data.
| Column | Type | Notes |
|---|---|---|
| `EmployeeName` | text | |
| `PatternType` | text | e.g. `1-Day Pattern` / `2-Day Pattern` |
| `Status` | text | e.g. `Completed`, `Scheduled`, `In progress` |
| `Date` | date | |

## What's computed vs. what's static

- **Computed from your data:** Total Employees, Sick Leave (This Month),
  1-Day / 2-Day event counts and their vs.-last-month deltas, the 6-month
  pattern chart, the Leave Duration donut, Key Insights (weekday skew,
  1-day trend %, Mon/Fri share), the Repeated Sick Leave table, risk levels,
  top-3 at-risk employees, and the AI Assistant's headline number.
- **Static UI only (no numbers attached):** section icons, nav labels,
  hero banner copy, and button labels — these are interface chrome, same
  as in the original design.

## Notes on fidelity

Streamlit renders through its own component system rather than raw HTML/CSS,
so this matches the reference design's layout, colors, cards, charts and
right-rail AI panel closely, but won't be byte-identical to a browser-rendered
mockup (fonts/shadows render slightly differently). The banner uses a CSS
gradient instead of the original photo — swap in a real image easily by
replacing the `background` property of `.hero` in the CSS block with
`background-image:url('your-image.jpg')`.

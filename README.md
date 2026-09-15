# UPL Behavioral Leave Monitor — Python App

This project recreates the supplied dashboard screenshot as a functional Python/Streamlit application.

## Run

1. Install Python 3.10+.
2. Open a terminal in this folder.
3. Install dependencies:

   pip install -r requirements.txt

4. Start the app:

   streamlit run app.py

The browser will open the dashboard.

## Included

- Screenshot-matched navy/orange Amazon-style dashboard
- Left sidebar and top filters
- UPL Report KPI tile
- Behavioral Policy Breach Pattern Identifier
- 1-Day and 2-Day pattern grids with Triage A/B
- Day-wise compliance matrix
- 3P agency breakdown + bar chart
- Weekly planned vs unplanned leave trend
- Absence category donut
- SL/PL weekly stacked chart with Monday/Friday callouts
- High-frequency defaulters drill-down
- Expandable UPL full drill-down portal

## Backend integration

The data is currently demonstration data. Replace the DataFrame definitions in `app.py`
with calls to your API/database. The UI can remain unchanged.

For production, avoid treating a valid medical certificate as a policy breach merely
because a behavioral pattern exists. Keep behavioral risk separate from medical
validation and route flagged cases to human review.

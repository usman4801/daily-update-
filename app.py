import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Amazon Transport & Fleet Tracker (DXB5 | AUH1 | DXB3)",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide left sidebar completely
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
        .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 1. FIXED BUS FLEET & LIVE TRACKING DATA (DXB5, AUH1, DXB3)
# =============================================================================
DEFAULT_FLEET = [
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-01", "Plate No": "DXB-10101 (Temp)", "Route": "Sahara / Stadium / Al Nahda / DAFZA / Etisalat", "Capacity": 50, "Booked": 46, "Vendor": "Mango Transport", "Driver Name": "Driver 1", "Phone": "971525539471", "WhatsApp / Live Loc": "https://wa.me/971525539471", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-02", "Plate No": "DXB-10102 (Temp)", "Route": "Rashidiya Metro / International City / DIP Metro", "Capacity": 50, "Booked": 44, "Vendor": "Mango Transport", "Driver Name": "Driver 2", "Phone": "971555309916", "WhatsApp / Live Loc": "https://wa.me/971555309916", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-03", "Plate No": "DXB-10103 (Temp)", "Route": "Abuhail / Abubacker / Baniyas / Salah Din / Union / Al Rigga", "Capacity": 50, "Booked": 48, "Vendor": "Mango Transport", "Driver Name": "Driver 3", "Phone": "971525539471", "WhatsApp / Live Loc": "https://wa.me/971525539471", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-04", "Plate No": "DXB-10104 (Temp)", "Route": "Al Ghubaiba / Sharaf DG / Burjuman / ADCB / Satwa / WTC / Financial Ctr", "Capacity": 50, "Booked": 45, "Vendor": "Mango Transport", "Driver Name": "Driver 4", "Phone": "971555309916", "WhatsApp / Live Loc": "https://wa.me/971555309916", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-05", "Plate No": "DXB-10105 (Temp)", "Route": "Onpassive / MOE / Mashreq / Internet City / Gardens / Expo Rove", "Capacity": 50, "Booked": 42, "Vendor": "Mango Transport", "Driver Name": "Driver 5", "Phone": "971525539471", "WhatsApp / Live Loc": "https://wa.me/971525539471", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-06", "Plate No": "DXB-10106 (Temp)", "Route": "Dulsco Camps (Al Quoz, Liwan, Rahaba) & EFS Camps (Jabel Ali, Al Quoz)", "Capacity": 60, "Booked": 55, "Vendor": "Mango Transport", "Driver Name": "Driver 6", "Phone": "971555309916", "WhatsApp / Live Loc": "https://wa.me/971555309916", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Night Shift (06:10 PM)", "Bus No": "DXB-07", "Plate No": "DXB-20201 (Temp)", "Route": "Sahara Bus Stops / DAFZA Metro / Etisalat Metro", "Capacity": 50, "Booked": 47, "Vendor": "Mango / Shahara Sky", "Driver Name": "Driver 7", "Phone": "971555309916", "WhatsApp / Live Loc": "https://wa.me/971555309916", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Night Shift (06:10 PM)", "Bus No": "DXB-08", "Plate No": "DXB-20202 (Temp)", "Route": "Abuhail / Abubacker / Baniyas / Salah Din / Union / Al Rigga", "Capacity": 50, "Booked": 49, "Vendor": "Mango / Shahara Sky", "Driver Name": "Driver 8", "Phone": "971525539471", "WhatsApp / Live Loc": "https://wa.me/971525539471", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Night Shift (06:10 PM)", "Bus No": "DXB-09", "Plate No": "DXB-20203 (Temp)", "Route": "Rashidiya Metro / International City / DIP MS", "Capacity": 50, "Booked": 43, "Vendor": "Mango / Shahara Sky", "Driver Name": "Driver 9", "Phone": "971585887560", "WhatsApp / Live Loc": "https://wa.me/971585887560", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Night Shift (06:10 PM)", "Bus No": "DXB-10", "Plate No": "DXB-20204 (Temp)", "Route": "Al Ghubaiba / Al Fahidi / Burjuman / ADCB / Financial Ctr / MOE / Satwa", "Capacity": 50, "Booked": 46, "Vendor": "Mango / Shahara Sky", "Driver Name": "Driver 10", "Phone": "971585887560", "WhatsApp / Live Loc": "https://wa.me/971585887560", "Status": "🟢 On Route"},
    {"Site": "DXB5", "Shift": "Night Shift (06:10 PM)", "Bus No": "DXB-11", "Plate No": "DXB-20205 (Temp)", "Route": "Dulsco Village Alquoz / Livon / Rahaba & EFS Camps (Jabel Ali / Alquoz)", "Capacity": 60, "Booked": 58, "Vendor": "Mango / Shahara Sky", "Driver Name": "Driver 11", "Phone": "971585887560", "WhatsApp / Live Loc": "https://wa.me/971585887560", "Status": "🟢 On Route"},
    {"Site": "AUH1", "Shift": "Day Shift (07:30 AM)", "Bus No": "AUH-01", "Plate No": "AUH-50101 (Temp)", "Route": "Dulsco ICAD-1 Bus Stop & Dulsco Camp", "Capacity": 65, "Booked": 62, "Vendor": "Dulsco Transport", "Driver Name": "Driver 12", "Phone": "971500000001", "WhatsApp / Live Loc": "https://wa.me/971500000001", "Status": "🟢 On Route"},
    {"Site": "AUH1", "Shift": "Day Shift (07:30 AM)", "Bus No": "AUH-02", "Plate No": "AUH-50102 (Temp)", "Route": "Dulsco Al Razeen Camp Abu Dhabi", "Capacity": 65, "Booked": 60, "Vendor": "Dulsco Transport", "Driver Name": "Driver 13", "Phone": "971500000002", "WhatsApp / Live Loc": "https://wa.me/971500000002", "Status": "🟢 On Route"},
    {"Site": "AUH1", "Shift": "Day Shift (07:30 AM)", "Bus No": "AUH-03", "Plate No": "AUH-50103 (Temp)", "Route": "Abu Dhabi Mall / Al Salama Hospital (Tourist Club Area)", "Capacity": 55, "Booked": 52, "Vendor": "Fastlink Transport", "Driver Name": "Driver 14", "Phone": "971500000003", "WhatsApp / Live Loc": "https://wa.me/971500000003", "Status": "🟢 On Route"},
    {"Site": "AUH1", "Shift": "Day Shift (07:30 AM)", "Bus No": "AUH-04", "Plate No": "AUH-50104 (Temp)", "Route": "Shinning Tower (Khalidiyah) / LifeLine Hospital / Central Bus Station", "Capacity": 60, "Booked": 57, "Vendor": "Fastlink Transport", "Driver Name": "Driver 15", "Phone": "971500000004", "WhatsApp / Live Loc": "https://wa.me/971500000004", "Status": "🟢 On Route"},
    {"Site": "AUH1", "Shift": "Day Shift (07:30 AM)", "Bus No": "AUH-05", "Plate No": "AUH-50105 (Temp)", "Route": "Shabiya 10 / 11 / 12 Bus Stop / Filli Cafe / Mussafah Workers Village", "Capacity": 60, "Booked": 54, "Vendor": "Fastlink Transport", "Driver Name": "Driver 16", "Phone": "971500000005", "WhatsApp / Live Loc": "https://wa.me/971500000005", "Status": "🟢 On Route"},
    {"Site": "AUH1", "Shift": "Night Shift (06:00 PM)", "Bus No": "AUH-06", "Plate No": "AUH-50201 (Temp)", "Route": "Dulsco ICAD-1 Bus Stop & Dulsco Camp (Night)", "Capacity": 65, "Booked": 61, "Vendor": "Dulsco Transport", "Driver Name": "Driver 17", "Phone": "971500000006", "WhatsApp / Live Loc": "https://wa.me/971500000006", "Status": "🟢 On Route"},
    {"Site": "AUH1", "Shift": "Night Shift (06:00 PM)", "Bus No": "AUH-07", "Plate No": "AUH-50202 (Temp)", "Route": "Dulsco Al Razeen Camp Abu Dhabi (Night)", "Capacity": 60, "Booked": 54, "Vendor": "Dulsco Transport", "Driver Name": "Driver 18", "Phone": "971500000007", "WhatsApp / Live Loc": "https://wa.me/971500000007", "Status": "🟢 On Route"},
    {"Site": "AUH1", "Shift": "Night Shift (06:00 PM)", "Bus No": "AUH-08", "Plate No": "AUH-50203 (Temp)", "Route": "Abu Dhabi Mall / Al Salama / Shinning Tower / LifeLine / Central Bus Stn", "Capacity": 65, "Booked": 63, "Vendor": "Fastlink Transport", "Driver Name": "Driver 19", "Phone": "971500000008", "WhatsApp / Live Loc": "https://wa.me/971500000008", "Status": "🟢 On Route"},
    {"Site": "DXB3", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB3-01", "Plate No": "DXB-30101 (Temp)", "Route": "Deira / BurJuman / Satwa / Sheikh Zayed Road Route", "Capacity": 50, "Booked": 45, "Vendor": "Mango Transport", "Driver Name": "Driver 20", "Phone": "971525539471", "WhatsApp / Live Loc": "https://wa.me/971525539471", "Status": "🟢 On Route"},
    {"Site": "DXB3", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB3-02", "Plate No": "DXB-30102 (Temp)", "Route": "Dulsco & EFS Accommodations Route (Al Quoz / Jabel Ali)", "Capacity": 60, "Booked": 53, "Vendor": "Mango Transport", "Driver Name": "Driver 21", "Phone": "971555309916", "WhatsApp / Live Loc": "https://wa.me/971555309916", "Status": "🟢 On Route"},
    {"Site": "DXB3", "Shift": "Night Shift (06:00 PM)", "Bus No": "DXB3-03", "Plate No": "DXB-30201 (Temp)", "Route": "Deira / BurJuman / Satwa / Camps Night Route", "Capacity": 60, "Booked": 51, "Vendor": "Mango Transport", "Driver Name": "Driver 22", "Phone": "971585887560", "WhatsApp / Live Loc": "https://wa.me/971585887560", "Status": "🟢 On Route"},
]

# =============================================================================
# 2. FIXED PICKUP LOCATIONS & EXACT TIMINGS (DXB5, AUH1, DXB3)
# =============================================================================
FIXED_PICKUP_SCHEDULES = [
    # DXB5 DAY SHIFT (08:00 AM SOS)
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-01", "Pickup Location": "Sahara _ ENOC Fuel Filling Station Backside Sahara Centre", "Pickup Time": "06:25 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-01", "Pickup Location": "Sahara _ Foot Bridge Parking lot Near Save More Supermarket / Aster", "Pickup Time": "06:30 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-01", "Pickup Location": "Stadium Metro _ Near Lulu round about & Adnoc Fuel Station", "Pickup Time": "06:35 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-01", "Pickup Location": "Al Nahda Metro _ Service Road Bus Stop Sharjah Route", "Pickup Time": "06:40 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-01", "Pickup Location": "DAFZA Metro _ Bus Stop Sharjah Route", "Pickup Time": "06:42 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-01", "Pickup Location": "Etisalat Metro _ Bus Stop Sharjah Route", "Pickup Time": "06:45 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-02", "Pickup Location": "Rashidiya Metro _ Near KFC", "Pickup Time": "06:35 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day Shift (08:00 AM)", "Bus No": "DXB-02", "Pickup Location": "International City (Near Post office Bus Stop)", "Pickup Time": "06:45 AM", "Vendor": "Mango Transport", "Coordinator": "+971 52 553 9471 / +971 55 530 9916"},
    {"Site": "DXB5", "Shift": "Day

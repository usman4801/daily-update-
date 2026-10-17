# Bus & Driver Live Tracking Module
st.subheader("📍 Bus Driver Live Location & Tracking")

# Sample data for buses, drivers and their WhatsApp links
bus_tracking_data = [
    {"Bus No": "DXB-01", "Route": "Sahara / DAFZA", "Driver Name": "Driver 1", "Phone": "+971501234567", "WhatsApp Link": "https://wa.me/971501234567"},
    {"Bus No": "DXB-02", "Route": "Metro Stations", "Driver Name": "Driver 2", "Phone": "+971507654321", "WhatsApp Link": "https://wa.me/971507654321"},
    {"Bus No": "AUH-01", "Route": "ICAD & Razeen", "Driver Name": "Driver 3", "Phone": "+971559876543", "WhatsApp Link": "https://wa.me/971559876543"}
]

import pandas as pd
tracking_df = pd.DataFrame(bus_tracking_data)

# Display table with clickable action links
for index, row in tracking_df.iterrows():
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    col1.write(f"**{row['Bus No']}** ({row['Route']})")
    col2.write(f"Driver: {row['Driver Name']}")
    col3.write(f"Phone: {row['Phone']}")
    if col4.button(f"💬 Chat / Live Loc", key=f"btn_{index}"):
        st.markdown(f"[Click here to open WhatsApp chat]({row['WhatsApp Link']})")

st.caption("Note: Drivers apni live location WhatsApp par share karenge, jiska link yahan update kiya ja sakta hai.")

import streamlit as st

# Ouper ki basic config agar na ho
# st.set_page_config(layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Caveat:wght@600&display=swap'); /* Handwritten font for quote */

    .hero-section {
        background: linear-gradient(110deg, #e0f2fe 0%, #f0fdf4 60%, #e0f2fe 100%);
        border-radius: 16px;
        padding: 24px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid #bae6fd;
        margin-bottom: 20px;
        font-family: 'Inter', sans-serif;
    }
    
    .hero-badge {
        background: #0ea5e9;
        color: white;
        font-size: 11px;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
        margin-bottom: 12px;
    }

    .hero-title {
        font-size: 26px;
        font-weight: 800;
        color: #0f172a;
        margin: 0 0 10px 0;
        line-height: 1.2;
    }

    .hero-desc {
        font-size: 13.5px;
        color: #475569;
        margin: 0 0 20px 0;
        max-width: 85%;
        line-height: 1.5;
    }

    .pill-container {
        display: flex;
        gap: 12px;
        flex-wrap: nowrap;
    }

    .action-pill {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }

    .pill-icon {
        width: 28px;
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }

    .pill-text {
        display: flex;
        flex-direction: column;
    }
    
    .pill-text .title { font-size: 11.5px; font-weight: 700; color: #0f172a; }
    .pill-text .sub { font-size: 10px; color: #64748b; }

    /* Right side image & quote */
    .hero-visual {
        position: relative;
        flex-shrink: 0;
        margin-right: 10px;
    }

    .floating-quote {
        position: absolute;
        top: -15px;
        right: 20px;
        font-family: 'Caveat', cursive; /* Casual handwritten look */
        font-size: 18px;
        color: #0f172a;
        transform: rotate(-6deg);
        z-index: 2;
        text-align: center;
        line-height: 1.1;
    }

    .hero-image {
        width: 240px;
        height: 135px;
        border-radius: 12px;
        object-fit: cover;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: 2px solid rgba(255,255,255,0.6);
    }
</style>

<div class="hero-section">
    <div style="flex: 1;">
        <div class="hero-badge">✨ AI Powered</div>
        <h2 class="hero-title">Turn Attendance Patterns<br>into Positive Conversations</h2>
        <p class="hero-desc">We help you spot recurring sick leave patterns, understand the bigger picture, and coach your team with confidence.</p>
        
        <div class="pill-container">
            <!-- Button 1 -->
            <div class="action-pill">
                <div class="pill-icon" style="background:#f3e8ff; color:#9333ea;">🔮</div>
                <div class="pill-text">
                    <span class="title">Detect Patterns</span>
                    <span class="sub">Spot 1-day & 2-day trends</span>
                </div>
            </div>
            <!-- Button 2 -->
            <div class="action-pill">
                <div class="pill-icon" style="background:#e0f2fe; color:#0284c7;">⚡</div>
                <div class="pill-text">
                    <span class="title">Get AI Insights</span>
                    <span class="sub">Understand the why</span>
                </div>
            </div>
            <!-- Button 3 -->
            <div class="action-pill">
                <div class="pill-icon" style="background:#dcfce7; color:#16a34a;">🗣️</div>
                <div class="pill-text">
                    <span class="title">Coach with Confidence</span>
                    <span class="sub">Get suggested conversations</span>
                </div>
            </div>
            <!-- Button 4 -->
            <div class="action-pill">
                <div class="pill-icon" style="background:#ecfdf5; color:#059669;">🌱</div>
                <div class="pill-text">
                    <span class="title">Build Healthier Teams</span>
                    <span class="sub">Support & retain talent</span>
                </div>
            </div>
        </div>
    </div>
    
    <div class="hero-visual">
        <div class="floating-quote">Healthier people<br>build brighter<br>futures ↗</div>
        <!-- Original building picture link -->
        <img src="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=500&q=80" class="hero-image">
    </div>
</div>
""", unsafe_allow_html=True)

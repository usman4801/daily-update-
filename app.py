with col_side:
    # 1. AI Assistant Card (Fixed with 3D Robot Photo)
    st.markdown("""
    <div style="background-color: #2563eb; border-radius: 12px; padding: 20px; color: white; margin-bottom: 12px; position: relative; overflow: hidden;">
        <div style="display:flex; align-items:center; gap:6px; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:0.5px; opacity:0.9;">
            <span style="font-size:14px;">🤖</span> AI ASSISTANT
        </div>
        <div style="font-weight:800; font-size:18px; margin: 8px 0 16px 0;">Always here to help</div>
        <div style="font-size:13px; line-height:1.5; opacity:0.95; width:70%; margin-bottom:20px;">
            Hi Sarah! 👋<br>I've found <b>3 employees</b> with recurring 1-day and 2-day sick leave patterns in the last 6 months.
        </div>
        <div style="background:white; color:#2563eb; border-radius:8px; padding:10px 16px; font-weight:700; font-size:13px; display:inline-block; cursor:pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.1); position: relative; z-index: 2;">
            View Insights →
        </div>
        <!-- 3D Robot Photo -->
        <img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/Smilies/Robot.png" style="position:absolute; right:-5px; bottom:-5px; width:110px; z-index: 1;">
    </div>
    """, unsafe_allow_html=True)

    # 2. Action Links
    st.markdown("""
    <div class="content-box" style="margin-bottom: 12px; padding: 10px;">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; border-bottom:1px solid #f8fafc;">
            <div><div style="font-size:11px; font-weight:700;">Top 3 At-Risk Employees</div><div style="font-size:9.5px; color:#64748b;">With recurring sick leave patterns</div></div>
            <span style="color:#94a3b8; font-size:12px;">&gt;</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px; border-bottom:1px solid #f8fafc;">
            <div><div style="font-size:11px; font-weight:700;">Generate Coaching Conversation</div><div style="font-size:9.5px; color:#64748b;">For selected employee</div></div>
            <span style="color:#94a3b8; font-size:12px;">&gt;</span>
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center; padding:7px 10px;">
            <div><div style="font-size:11px; font-weight:700;">View Team Trend</div><div style="font-size:9.5px; color:#64748b;">Sick leave patterns by department</div></div>
            <span style="color:#94a3b8; font-size:12px;">&gt;</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 3. Donut Chart
    st.markdown("""
    <div class="content-box" style="margin-bottom: 12px;">
        <div class="box-header">📊 Leave Duration Breakdown</div>
    """, unsafe_allow_html=True)
    fig_donut = go.Figure(data=[go.Pie(
        labels=['1 Day', '2 Days'],
        values=[78, 46],
        hole=.72,
        marker=dict(colors=['#2563eb', '#9333ea']),
        textinfo='none'
    )])
    fig_donut.update_layout(
        height=150,
        margin=dict(l=5, r=5, t=5, b=5),
        showlegend=False,
        annotations=[dict(text='<b>124</b><br><span style="font-size:9px; color:#64748b;">Total Sick</span>', x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
    st.markdown("""
        <div style="display:flex; justify-content:space-around; font-size:10.5px; color:#475569; margin-top:2px;">
            <span><b style="color:#2563eb;">●</b> 1 Day: <b>78 (63%)</b></span>
            <span><b style="color:#9333ea;">●</b> 2 Days: <b>46 (37%)</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4. Recent Coaching Activity
    st.markdown("""
    <div class="content-box" style="margin-bottom: 12px;">
        <div class="box-header">
            <span>⚡ Recent Coaching</span>
            <span style="font-size:10px; color:#2563eb; cursor:pointer;">View All &gt;</span>
        </div>
        <div style="font-size:11px; padding:6px 0; border-bottom:1px solid #f8fafc; display:flex; justify-content:space-between; align-items:center;">
            <div><b>Emma Wilson</b><br><span style="font-size:9.5px; color:#94a3b8;">Completed • Jun 10</span></div>
            <span class="risk-badge" style="background:#fef3c7; color:#b45309;">1-Day Pattern</span>
        </div>
        <div style="font-size:11px; padding:6px 0; border-bottom:1px solid #f8fafc; display:flex; justify-content:space-between; align-items:center;">
            <div><b>James Carter</b><br><span style="font-size:9.5px; color:#94a3b8;">Scheduled • Jun 8</span></div>
            <span class="risk-badge" style="background:#ede9fe; color:#7c3aed;">2-Day Pattern</span>
        </div>
        <div style="font-size:11px; padding:6px 0; display:flex; justify-content:space-between; align-items:center;">
            <div><b>Olivia Davis</b><br><span style="font-size:9.5px; color:#94a3b8;">In Progress • Jun 6</span></div>
            <span class="risk-badge" style="background:#fef3c7; color:#b45309;">1-Day Pattern</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 5. Quote Card at Bottom Right
    st.markdown("""
    <div class="content-box" style="background: #f0fdf4; border: 1px solid #bbf7d0; display:flex; justify-content:space-between; align-items:center; padding: 10px 14px;">
        <div style="font-size:10.5px; color:#166534; font-weight:600; line-height:1.3;">
            “The best leaders don't just manage, they support people.”
        </div>
        <span style="color:#dc2626; font-size:14px; margin-left:8px;">🤍</span>
    </div>
    """, unsafe_allow_html=True)

"""
MathComp — app.py
Application routing state controller and sidebar setup
© Math Mission Thailand 2026
"""
import streamlit as st
from shared import inject_css, db, topbar, footer

# Setup page layout configs once
st.set_page_config(
    page_title="MathComp • Math Mission Thailand",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

from pages_student import page_login, page_dashboard, page_exam, page_result, page_history, page_leaderboard, page_realtime
from pages_admin import page_admin, page_admin_analytics, page_admin_student_history

if "page" not in st.session_state:
    st.session_state["page"] = "login"

inject_css()

# Modern Sidebar design integration
if "uid" in st.session_state:
    with st.sidebar:
        st.markdown(f"""
        <div style='padding: 10px 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 20px;'>
            <h3 style='margin:0; font-size:16px; color:#1B2B6B;'>{st.session_state.get('display_name','')}</h3>
            <span style='background:#EEF3FF; color:#4A7CF7; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600;'>
                ROLE: {st.session_state.get('role','Student').upper()}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏠 แผงควบคุม (Dashboard)", use_container_width=True):
            st.session_state["page"] = "dashboard"
            st.rerun()
        if st.button("📋 ประวัติการสอบ (History)", use_container_width=True):
            st.session_state["page"] = "history"
            st.rerun()
        if st.button("🏆 อันดับคะแนน (Leaderboard)", use_container_width=True):
            st.session_state["page"] = "leaderboard"
            st.rerun()
            
        if st.session_state.get("role") == "admin":
            st.markdown("<div style='margin:15px 0 5px 0; font-size:11px; color:#94A3B8; font-weight:600; text-transform:uppercase;'>Admin Center</div>", unsafe_allow_html=True)
            if st.button("⚙️ แผงจัดการระบบ (Admin Panel)", use_container_width=True):
                st.session_state["page"] = "admin"
                st.rerun()
            if st.button("📊 วิเคราะห์ภาพรวม (Analytics)", use_container_width=True):
                st.session_state["page"] = "admin_analytics"
                st.rerun()
                
        st.divider()
        if st.button("🚪 ออกจากระบบ (Log Out)", use_container_width=True):
            st.session_state.clear()
            st.session_state["page"] = "login"
            st.rerun()

# Execute page routing
p = st.session_state["page"]
if p == "login": page_login()
elif p == "dashboard": page_dashboard()
elif p == "exam": page_exam()
elif p == "result": page_result()
elif p == "history": page_history()
elif p == "leaderboard": page_leaderboard()
elif p == "realtime": page_realtime()
elif p == "admin": page_admin()
elif p == "admin_analytics": page_admin_analytics()
elif p == "admin_student_history": page_admin_student_history()

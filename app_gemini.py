"""
MathComp — app.py
Application entry point and routing manager
"""
import streamlit as st
from shared import inject_premium_css

st.set_page_config(
    page_title="MathComp | Premium EdTech",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded"
)

from pages_student import page_login, page_dashboard, page_exam, page_result
from pages_admin import page_admin

# Initialize session state
if "page" not in st.session_state:
    st.session_state["page"] = "login"

inject_premium_css()

# --- SIDEBAR NAVIGATION ---
if "uid" in st.session_state and st.session_state["page"] != "login":
    with st.sidebar:
        st.markdown(f"""
        <div style="padding-bottom: 1.5rem; border-bottom: 1px solid #E2E8F0; margin-bottom: 1.5rem;">
            <h3 style="margin: 0; font-size: 1.1rem; color: #1E3A8A;">{st.session_state.get('display_name', 'Student')}</h3>
            <span style="font-size: 0.8rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">
                {st.session_state.get('role', 'student')} Account
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏠 แดชบอร์ดหลัก", use_container_width=True):
            st.session_state["page"] = "dashboard"
            st.rerun()
        if st.button("📊 ประวัติผลการสอบ", use_container_width=True):
            st.session_state["page"] = "history"
            st.rerun()
            
        if st.session_state.get("role") == "admin":
            st.markdown("<div style='margin-top: 2rem; margin-bottom: 0.5rem; font-size: 0.75rem; color: #94A3B8; font-weight: 600; text-transform: uppercase;'>Admin Area</div>", unsafe_allow_html=True)
            if st.button("⚙️ จัดการระบบ (Admin Panel)", use_container_width=True):
                st.session_state["page"] = "admin"
                st.rerun()
                
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 ออกจากระบบ", use_container_width=True):
            st.session_state.clear()
            st.session_state["page"] = "login"
            st.rerun()

# --- ROUTER ---
pages = {
    "login": page_login,
    "dashboard": page_dashboard,
    "exam": page_exam,
    "result": page_result,
    "admin": page_admin
}

# Execute the current page function
if st.session_state["page"] in pages:
    pages[st.session_state["page"]]()
else:
    st.error("Page not found.")
    st.session_state["page"] = "login"
    st.rerun()

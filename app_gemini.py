import streamlit as st
from shared import inject_css, db, get_all_competitions, load_settings
from pages_student import page_login, page_dashboard, page_exam, page_result, page_history, page_leaderboard, page_realtime
from pages_admin import page_admin, page_admin_analytics, page_admin_student_history

if "page" not in st.session_state: st.session_state["page"] = "login"
inject_css()

if "uid" in st.session_state:
    with st.sidebar:
        st.markdown(f"<h3>{st.session_state.get('display_name','')}</h3>", unsafe_allow_html=True)
        if st.button("🏠 Dashboard", use_container_width=True): st.session_state["page"] = "dashboard"; st.rerun()
        if st.button("📋 My History", use_container_width=True): st.session_state["page"] = "history"; st.rerun()
        if st.button("🚪 Log Out", use_container_width=True): st.session_state.clear(); st.session_state["page"] = "login"; st.rerun()

page = st.session_state["page"]
if page == "login": page_login()
elif page == "dashboard": page_dashboard()
elif page == "exam": page_exam()
elif page == "result": page_result()
elif page == "history": page_history()
elif page == "leaderboard": page_leaderboard()
elif page == "realtime": page_realtime()
elif page == "admin": page_admin()
elif page == "admin_analytics": page_admin_analytics()
elif page == "admin_student_history": page_admin_student_history()

"""
MathComp — app.py
Math Mission Thailand · Online Mathematics Competition Platform
© Math Mission Thailand 2026
"""
import streamlit as st
from shared import (
    inject_css, db, get_all_competitions, load_settings,
    COMPETITIONS_BUILTIN, DIFFICULTY_OPTIONS, TOPICS,
    footer, topbar,
)
from pages_student import (
    page_login, page_dashboard, page_exam, page_result,
    page_history, page_leaderboard
)
from pages_admin import (
    page_admin, page_admin_analytics, page_admin_student_history,
)

st.set_page_config(
    page_title="MathComp · Math Mission Thailand",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

def render_sidebar():
    if "uid" not in st.session_state: return
    with st.sidebar:
        st.markdown(f"**{st.session_state.get('display_name','')}**")
        st.caption(st.session_state.get("role","student").capitalize())
        st.divider()
        if st.button("🏠  Dashboard", use_container_width=True):
            st.session_state["page"]="dashboard"; st.rerun()
        if st.button("📋  My History", use_container_width=True):
            st.session_state["page"]="history"; st.rerun()
        if st.button("🏆  Leaderboard", use_container_width=True):
            st.session_state["page"]="leaderboard"; st.rerun()
        if st.session_state.get("role")=="admin":
            st.divider()
            if st.button("⚙️  Admin Panel", use_container_width=True):
                st.session_state["page"]="admin"; st.rerun()
            if st.button("📊  Analytics", use_container_width=True):
                st.session_state["page"]="admin_analytics"; st.rerun()
        st.divider()
        if st.button("Log out", use_container_width=True):
            st.session_state.clear(); st.rerun()
        st.markdown("---")
        st.markdown(
            "<div style='font-size:10px;color:rgba(255,255,255,.3);"
            "font-family:monospace;line-height:1.7;'>"
            "© Math Mission Thailand 2026<br>MathComp Platform</div>",
            unsafe_allow_html=True)

def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    render_sidebar()
    page = st.session_state["page"]

    if   page=="login":                 page_login()
    elif page=="dashboard":             page_dashboard()
    elif page=="exam":                  page_exam()
    elif page=="result":                page_result()
    elif page=="admin":                 page_admin()
    elif page=="history":               page_history()
    elif page=="leaderboard":           page_leaderboard()
    elif page=="admin_analytics":       page_admin_analytics()
    elif page=="admin_student_history": page_admin_student_history()
    else:
        st.error(f"Unknown page: {page}")
        st.session_state["page"]="login"; st.rerun()

if __name__=="__main__":
    main()

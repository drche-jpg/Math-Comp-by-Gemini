"""
MathComp — app.py  (router only)
Math Mission Thailand · Online Mathematics Competition Platform
© Math Mission Thailand 2026

Run: streamlit run app.py
"""
import streamlit as st
from shared import (
    inject_css, db, get_all_competitions, load_settings,
    COMPETITIONS_BUILTIN, DIFFICULTY_OPTIONS, TOPICS,
    footer, topbar,
)
from pages_student import (
    page_login, page_dashboard, page_exam, page_result,
    page_history, page_leaderboard, page_realtime,
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
        if st.button("🏠  Dashboard",   use_container_width=True):
            for k in ("rt_comp","rt_status"): st.session_state.pop(k,None)
            st.session_state["page"]="dashboard"; st.rerun()
        if st.button("📋  My History",  use_container_width=True):
            st.session_state["page"]="history"; st.rerun()
        if st.button("🏆  Leaderboard", use_container_width=True):
            st.session_state["page"]="leaderboard"; st.rerun()
        if st.session_state.get("role")=="admin":
            st.divider()
            if st.button("⚙️  Admin Panel",  use_container_width=True):
                st.session_state["page"]="admin"; st.rerun()
            if st.button("📊  Analytics",    use_container_width=True):
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

    params = st.query_params

    if "comp" in params:
        comp_param = params.get("comp","").strip()
        if comp_param:
            if "uid" not in st.session_state:
                if st.session_state.get("pending_comp") != comp_param:
                    st.session_state["pending_comp"]  = comp_param
                    st.session_state["pending_level"] = params.get("level","")
            elif st.session_state.get("rt_comp") != comp_param:
                rt_doc_id = comp_param.replace(" ","_").replace("/","_")
                try:
                    rt_doc    = db.collection("realtime_sessions").document(rt_doc_id).get()
                    rt_data   = rt_doc.to_dict() if rt_doc.exists else {}
                    rt_status = rt_data.get("status","not started")
                except:
                    rt_status = "not started"
                st.session_state["rt_comp"]   = comp_param
                st.session_state["rt_status"] = rt_status
                st.session_state["page"]      = "realtime"
                st.session_state.pop("pending_comp",  None)
                st.session_state.pop("pending_level", None)
                st.rerun()
            else:
                current_page = st.session_state.get("page","")
                if current_page not in ("realtime","exam","result"):
                    st.session_state["page"] = "realtime"

    render_sidebar()
    page = st.session_state["page"]

    if "uid" in st.session_state and st.session_state.get("pending_comp"):
        comp_param  = st.session_state.pop("pending_comp","")
        if comp_param:
            rt_doc_id = comp_param.replace(" ","_").replace("/","_")
            try:
                rt_doc    = db.collection("realtime_sessions").document(rt_doc_id).get()
                rt_data   = rt_doc.to_dict() if rt_doc.exists else {}
                rt_status = rt_data.get("status","not started")
            except:
                rt_status = "not started"
            st.session_state["rt_comp"]   = comp_param
            st.session_state["rt_status"] = rt_status
            st.session_state["page"]      = "realtime"
            st.rerun()

    if   page=="login":                 page_login()
    elif page=="dashboard":             page_dashboard()
    elif page=="exam":                  page_exam()
    elif page=="result":                page_result()
    elif page=="admin":                 page_admin()
    elif page=="history":               page_history()
    elif page=="leaderboard":           page_leaderboard()
    elif page=="admin_analytics":       page_admin_analytics()
    elif page=="realtime":              page_realtime()
    elif page=="admin_student_history": page_admin_student_history()
    else:
        st.error(f"Unknown page: {page}")
        st.session_state["page"]="login"; st.rerun()


if __name__=="__main__":
    main()

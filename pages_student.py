import streamlit as st
import time, random
import plotly.graph_objects as go
from shared import inject_css, topbar, footer, get_all_competitions, DIFFICULTY_OPTIONS, compute_score, get_advanced_anti_ai_js

def page_login():
    inject_css(); topbar("Login", show_user=False)
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login", type="primary"):
        st.session_state.update({"uid": "u1", "display_name": u, "role": "admin" if u=="admin" else "student", "page": "dashboard"})
        st.rerun()
    footer()

def page_dashboard():
    inject_css(); topbar("Dashboard")
    comps = get_all_competitions()
    sc = st.selectbox("Select Competition", list(comps.keys()))
    lvl = st.selectbox("Select Level", comps[sc]["levels"])
    diff = st.selectbox("Difficulty", DIFFICULTY_OPTIONS)
    nq = st.slider("Questions", 5, 30, 10)
    
    if st.button("Start Exam", type="primary"):
        mqs = [{"id": f"q_{i}", "topic": random.choice(comps[sc]["topics"]), "question_text": f"โจทย์ข้อที่ {i+1}: $x + \\frac{{1}}{{x}} = 3$ จงหา $x^2 + \\frac{{1}}{{x^2}}$", "choices": ["5","7","9","11"], "correct_answer": "B"} for i in range(nq)]
        st.session_state.update({"page": "exam", "competition": sc, "level": lvl, "questions": mqs, "answers": {}, "flagged": set(), "current_idx": 0, "start_time": time.time(), "time_limit": nq*120})
        st.rerun()
    footer()

def page_exam():
    qs = st.session_state["questions"]; ans = st.session_state["answers"]; flg = st.session_state["flagged"]; idx = st.session_state["current_idx"]
    rem = max(0.0, st.session_state["time_limit"] - (time.time() - st.session_state["start_time"]))
    
    st.markdown(f"<h4>Time Remaining: {int(rem//60)}:{int(rem%60):02d}</h4>", unsafe_allow_html=True)
    q = qs[idx]
    st.markdown(f"<div class='premium-card'><strong>Question {idx+1}:</strong><br>{q['question_text']}</div>", unsafe_allow_html=True)
    
    sel = st.radio("Options", q["choices"], key=f"r_{idx}")
    if sel: ans[q["id"]] = "B" # mock handling
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if idx > 0:
            if st.button("Previous"): st.session_state["current_idx"] -= 1; st.rerun()
    with f_col:=c2:
        if st.button("Flag"): flg.add(q["id"])
    with c3:
        if idx < len(qs)-1:
            if st.button("Next"): st.session_state["current_idx"] += 1; st.rerun()
        else:
            if st.button("Submit", type="primary"):
                st.session_state["result"] = compute_score(st.session_state["competition"], qs, ans)
                st.session_state["page"] = "result"; st.rerun()

def page_result():
    inject_css(); topbar("Result Summary")
    res = st.session_state.get("result", {})
    st.success(f"Score: {res.get('score')} / {res.get('total')}")
    if st.button("Go to Dashboard"): st.session_state["page"] = "dashboard"; st.rerun()
    footer()

def page_history(): inject_css(); st.write("History list"); footer()
def page_leaderboard(): inject_css(); st.write("Leaderboard"); footer()
def page_realtime(): inject_css(); st.write("Realtime Live Room"); footer()

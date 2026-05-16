from shared import *

def page_login():
    inject_css()
    topbar("Math Mission Thailand", show_user=False)
    st.markdown("""
    <div style="background:linear-gradient(135deg,#EEF3FF 0%,#FBF0FF 100%); padding:60px 20px;display:flex;align-items:center;justify-content:center;">
      <div style="width:380px;background:#fff;border-radius:20px; box-shadow:0 8px 40px rgba(27,43,107,.12);padding:40px;position:relative;overflow:hidden;">
        <div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.16em; color:#4A7CF7;text-transform:uppercase;margin-bottom:12px;">Math Mission Thailand</div>
        <div style="font-family:'Fraunces',serif;font-size:36px;font-weight:300; color:#1B2B6B;line-height:1.1;margin-bottom:6px;">Welcome to<br><em style="font-style:italic;color:#4A7CF7;">MathComp</em></div>
        <div style="font-size:13px;color:#8898CC;margin-bottom:32px;">Online Mathematics Competition Platform</div>
      </div>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1,1.1,1])
    with col:
        with st.form("login"):
            email    = st.text_input("Email address")
            password = st.text_input("Password", type="password")
            sub      = st.form_submit_button("Log in →", use_container_width=True, type="primary")
    if sub:
        if not email or not password: st.error("Please enter both email and password.")
        else:
            with st.spinner("Authenticating…"):
                user = sign_in(email, password)
            if user:
                uid = user["localId"]; profile = get_profile(uid)
                st.session_state.update({
                    "uid":uid,"email":email,
                    "display_name":profile.get("display_name",email.split("@")[0]),
                    "role":profile.get("role","student"),"page":"dashboard"})
                st.rerun()
            else: st.error("Incorrect email or password.")
    footer()

def page_dashboard():
    require_auth(); inject_css()
    uid  = st.session_state["uid"]; name = st.session_state.get("display_name","Student")
    topbar("Dashboard")

    sessions = []
    try: sessions = [s.to_dict() for s in db.collection("users").document(uid).collection("exam_sessions").order_by("timestamp_start",direction=firestore.Query.DESCENDING).limit(5).stream()]
    except: pass

    if sessions:
        last = sessions[0]; avg = round(sum(s["pct"] for s in sessions)/len(sessions),1)
        m1,m2,m3,m4 = f"{last['raw_score']} / {last['max_score']}",f"{last['pct']}%",str(len(sessions)),f"{avg}%"
        s1,s2,s3,s4 = last.get('competition','—'),"last session","exams taken","all time"
    else: m1=m2=m3=m4="—"; s1=s2=s3=s4=""

    st.markdown(f"""
    <div class="mc-hero">
      <div class="mc-hero-eyebrow">Good day</div>
      <div class="mc-hero-title">Welcome back, <em>{name}</em></div>
      <div class="mc-metrics">
        <div class="mc-metric"><div class="mc-metric-label">Last Score</div><div class="mc-metric-val">{m1}</div><div class="mc-metric-sub">{s1}</div></div>
        <div class="mc-metric"><div class="mc-metric-label">Accuracy</div><div class="mc-metric-val">{m2}</div><div class="mc-metric-sub">{s2}</div></div>
        <div class="mc-metric"><div class="mc-metric-label">Sessions</div><div class="mc-metric-val">{m3}</div><div class="mc-metric-sub">{s3}</div></div>
        <div class="mc-metric"><div class="mc-metric-label">Avg Accuracy</div><div class="mc-metric-val">{m4}</div><div class="mc-metric-sub">{s4}</div></div>
      </div>
    </div>
    <div class="mc-body">""", unsafe_allow_html=True)

    st.markdown('<span class="mc-section-lbl">Start a new exam</span>', unsafe_allow_html=True)
    st.markdown('<div class="mc-card">', unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        comp_keys    = list(get_all_competitions().keys())
        competition  = st.selectbox("Competition", comp_keys)
        comp_info   = get_all_competitions()[competition]
        st.caption(comp_info.get("description", ""))
        level = st.selectbox("Level / Division", comp_info["levels"])
    with cb:
        difficulty  = st.selectbox("Difficulty", DIFFICULTY_OPTIONS)
        n_questions = st.slider("Number of questions", 1, 50, 15, step=1)
        suggested   = n_questions * comp_info["secs_per_q"]
        st.caption(f"Suggested time: **{suggested//60} min** ({comp_info['secs_per_q']}s per question)")

    if st.button("Start Exam →", type="primary", use_container_width=True):
        with st.spinner("Loading questions…"):
            qs = fetch_questions(competition, level, difficulty, n_questions)
        if not qs: st.error("No questions found. Try a different selection.")
        else:
            st.session_state.update({
                "page":"exam","competition":competition,"level":level,"difficulty":difficulty,
                "questions":qs,"answers":{},"flagged":set(),"current_idx":0,
                "start_time":time.time(),"time_limit":suggested,"exam_settings":load_settings(competition)})
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    footer()

def _go(idx): st.session_state["current_idx"] = idx

def _submit():
    uid=st.session_state["uid"]; qs=st.session_state["questions"]; answers=st.session_state["answers"]
    duration=int(time.time()-st.session_state["start_time"])
    result=compute_score(st.session_state["competition"],qs,answers)
    sid=save_session(uid,st.session_state["competition"],st.session_state["level"], st.session_state["difficulty"],qs,answers,result,duration)
    st.session_state.update({"page":"result","result":result,"session_id":sid,"duration":duration})
    st.rerun()

def page_exam():
    require_auth(); inject_css()
    qs = st.session_state["questions"]; answers = st.session_state["answers"]; flagged = st.session_state["flagged"]; idx = st.session_state["current_idx"]
    settings = st.session_state.get("exam_settings", DEFAULT_SETTINGS)
    
    remaining = max(0.0, st.session_state["time_limit"]-(time.time()-st.session_state["start_time"]))
    mins,secs = divmod(int(remaining), 60)
    if remaining == 0: _submit(); return

    js = get_anti_ai_js(settings)
    if js: components.html(js, height=0)

    warn = remaining < 300
    tc   = "#FCA5A5" if warn else "#ffffff"
    st.markdown(f"""
    <div style="background:#1B2B6B;padding:0 28px;height:54px;display:flex;align-items:center;gap:12px;">
      <span style="font-family:'DM Mono',monospace;font-size:13px;letter-spacing:.14em;color:#fff;font-weight:500;">MATHCOMP</span>
      <span style="width:1px;height:18px;background:rgba(255,255,255,.2);display:inline-block;"></span>
      <span style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15); font-size:11px;padding:3px 10px;border-radius:4px;color:rgba(255,255,255,.7);">{st.session_state['competition']}</span>
      <span style="font-size:13px;color:#fff;font-weight:500;flex:1;">Question {idx+1} of {len(qs)}</span>
      <div style="display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:6px 14px;">
        <span style="font-size:9px;color:rgba(255,255,255,.45);text-transform:uppercase;">Time left</span>
        <span style="font-family:'DM Mono',monospace;font-size:18px;font-weight:500;color:{tc};">{'⚠️ ' if warn else ''}{mins:02d}:{secs:02d}</span>
      </div>
    </div>""", unsafe_allow_html=True)

    answered_count = sum(1 for q in qs if answers.get(q["id"]) is not None)
    st.progress(answered_count/len(qs), text=f"{answered_count} of {len(qs)} answered")

    dots_html = ""
    for i,q in enumerate(qs):
        if i==idx: dots_html += f'<span class="mc-nav-dot" style="background:#1B2B6B;border-color:#1B2B6B;color:#fff;font-weight:600;">{i+1}</span>'
        elif q["id"] in flagged: dots_html += f'<span class="mc-nav-dot" style="background:#FDF2F8;border-color:#F472B6;color:#9D174D;">🚩</span>'
        elif answers.get(q["id"]) is not None: dots_html += f'<span class="mc-nav-dot" style="background:#EEF3FF;border-color:#4A7CF7;color:#1B2B6B;">✓{i+1}</span>'
        else: dots_html += f'<span class="mc-nav-dot">{i+1}</span>'
    st.markdown(f'<div class="mc-nav-strip">{dots_html}</div>', unsafe_allow_html=True)

    q = qs[idx]; qid = q["id"]
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
      <span style="font-family:'DM Mono',monospace;font-size:11px;color:#8898CC;">Q{idx+1} / {len(qs)}</span>
      <span style="font-size:11px;padding:3px 10px;border-radius:20px; background:#EEF3FF;border:1px solid #C8D8FF;color:#4A7CF7;">{q.get('topic','')}</span>
    </div>""", unsafe_allow_html=True)

    if q.get("question_image_url"): st.image(q["question_image_url"], use_container_width=True)
    if q.get("question_text"):      st.markdown(q["question_text"])

    answer_type = q.get("answer_type","mc4"); current_ans = answers.get(qid)
    if answer_type in ("mc4","mc5"):
        choices = q.get("choices",[]); labels = [chr(65+i) for i in range(len(choices))]
        options = [f"{labels[i]}.  {choices[i]}" for i in range(len(choices))]
        cur = options[labels.index(current_ans.upper())] if current_ans and current_ans.upper() in labels else None
        choice = st.radio("Select your answer:", options, index=options.index(cur) if cur else None, key=f"r_{qid}")
        if choice: answers[qid]=choice[0]; st.session_state["answers"]=answers
    else:
        val = st.text_input("Enter numeric answer:", value=current_ans or "", key=f"i_{qid}")
        if val: answers[qid]=val; st.session_state["answers"]=answers

    is_f = qid in flagged
    if st.button("🚩 Remove flag" if is_f else "🏳 Flag for review", key=f"f_{qid}"):
        flagged.discard(qid) if is_f else flagged.add(qid)
        st.session_state["flagged"]=flagged; st.rerun()

    st.divider()
    n1,n2,n3 = st.columns([1,2,1])
    if idx>0:         n1.button("← Previous", on_click=_go, args=(idx-1,), use_container_width=True)
    if idx<len(qs)-1: n3.button("Next →",     on_click=_go, args=(idx+1,), use_container_width=True)
    with n2:
        if st.button("✅  Submit Exam", type="primary", use_container_width=True):
            if len(qs)-answered_count==0: _submit()
            else: st.session_state["confirm_submit"]=True

    if st.session_state.get("confirm_submit"):
        st.warning(f"You have **{len(qs)-answered_count}** unanswered question(s). Submit anyway?")
        ca,cb = st.columns(2)
        if ca.button("Yes, submit now", type="primary"): st.session_state.pop("confirm_submit",None); _submit()
        if cb.button("Go back"): st.session_state.pop("confirm_submit",None); st.rerun()
    footer()

def page_result():
    require_auth(); inject_css()
    result=st.session_state["result"]; competition=st.session_state["competition"]
    level=st.session_state["level"]; qs=st.session_state["questions"]
    duration=st.session_state.get("duration",0); settings=st.session_state.get("exam_settings",DEFAULT_SETTINGS)
    correct_c=sum(1 for pq in result["per_question"] if pq["correct"])
    wrong_c  =sum(1 for pq in result["per_question"] if not pq["correct"] and pq["chosen"] is not None)
    blank_c  =sum(1 for pq in result["per_question"] if pq["chosen"] is None)

    topbar("Exam Results")
    st.markdown(f"""
    <div class="mc-result-hero">
      <div class="mc-result-score">{result['raw_score']} <span>/ {result['max_score']}</span></div>
      <div class="mc-result-meta">
        <div class="mc-rm"><div class="mc-rm-val">{result['pct']}%</div><div class="mc-rm-lbl">Accuracy</div></div>
        <div class="mc-rm"><div class="mc-rm-val">{duration//60}m {duration%60}s</div><div class="mc-rm-lbl">Time taken</div></div>
      </div>
    </div>
    <div class="mc-body">""", unsafe_allow_html=True)

    col_r,col_b = st.columns(2)
    with col_r:
        st.markdown('<span class="mc-section-lbl">Performance by topic</span>', unsafe_allow_html=True)
        st.plotly_chart(radar_chart(result["topic_breakdown"]), use_container_width=True)
    with col_b:
        st.markdown('<span class="mc-section-lbl">Topic breakdown</span>', unsafe_allow_html=True)
        bars = ""
        for topic,v in result["topic_breakdown"].items():
            pct   = round(v["correct"]/v["total"]*100) if v["total"]>0 else 0
            color = "#4A7CF7" if pct>=50 else "#F472B6"
            bars += f'<div class="mc-topic-row"><span class="mc-topic-name">{topic}</span><div class="mc-bar-bg"><div class="mc-bar-fill" style="width:{pct}%;background:{color};"></div></div><span class="mc-bar-pct">{pct}%</span></div>'
        st.markdown(bars, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style="background:linear-gradient(135deg,#EEF3FF,#FDF2F8); border:1.5px solid #C8D8FF;border-radius:16px;padding:20px 24px;margin-bottom:4px;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
        <span style="font-size:24px;">🤖</span>
        <div><div style="font-size:15px;font-weight:600;color:#1B2B6B;">AI Performance Analysis</div><div style="font-size:12px;color:#8898CC;">Powered by Gemini 1.5 Pro</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if "ai_analysis" not in st.session_state: st.session_state["ai_analysis"] = None

    if st.session_state.get("ai_analysis"):
        st.markdown(f'<div style="background:#fff;border:1.5px solid #E8ECF8;border-radius:12px;padding:24px 28px;">{st.session_state["ai_analysis"]}</div>', unsafe_allow_html=True)
    else:
        if st.button("✨  Analyse my results", type="primary", use_container_width=True):
            with st.spinner("Gemini is analysing your performance…"):
                st.session_state["ai_analysis"] = ai_analyze_performance(st.session_state.get("display_name", "Student"), competition, level, result, qs, duration)
            st.rerun()

    st.divider()
    st.subheader("Question review")
    for i,(q,pq) in enumerate(zip(qs,result["per_question"])):
        chosen=pq["chosen"] or "—"; correct=pq["right_answer"] or "—"
        icon="✅" if pq["correct"] else ("⬜" if pq["chosen"] is None else "❌")
        with st.expander(f"{icon}  Q{i+1} · {q.get('topic','—')} · Your answer: **{chosen}** · Correct: **{correct}**"):
            if q.get("question_image_url"): st.image(q["question_image_url"],use_container_width=True)
            if q.get("question_text"):      st.markdown(q["question_text"])
            st.divider()
            if settings.get("show_answer_after_submit",True):
                if q.get("solution_image_url"): st.image(q.get("solution_image_url"),use_container_width=True)
                if q.get("solution_text"):      st.markdown("**Solution:**"); st.markdown(q["solution_text"])
            else: st.caption("Solutions are not shown for this competition.")

    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("← Back to dashboard", use_container_width=True):
        for k in ["questions","answers","flagged","current_idx","start_time","time_limit","result","session_id","duration","ai_analysis"]: st.session_state.pop(k,None)
        st.session_state["page"]="dashboard"; st.rerun()
    footer()

def page_history():
    require_auth(); inject_css(); topbar("My History")
    st.info("Performance history has been migrated to the analytics dashboard. Please check back soon.")
    if st.button("← Back to Dashboard"): st.session_state["page"]="dashboard"; st.rerun()
    footer()

def page_leaderboard():
    require_auth(); inject_css(); topbar("Leaderboard")
    st.info("Leaderboard is updating.")
    if st.button("← Back to Dashboard"): st.session_state["page"]="dashboard"; st.rerun()
    footer()

"""
MathComp — pages_student.py
Student-facing pages: login, dashboard, exam, result, history, leaderboard, realtime
© Math Mission Thailand 2026
"""
from shared import *

def page_login():
    inject_css()
    topbar("Math Mission Thailand", show_user=False)
    st.markdown("""
    <div style="background:linear-gradient(135deg,#EEF3FF 0%,#FBF0FF 100%);
                padding:60px 20px;display:flex;align-items:center;justify-content:center;">
      <div style="width:380px;background:#fff;border-radius:20px;
                  box-shadow:0 8px 40px rgba(27,43,107,.12);padding:40px;position:relative;overflow:hidden;">
        <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;
                    background:radial-gradient(circle,rgba(244,114,182,.1) 0%,transparent 70%);"></div>
        <div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.16em;
                    color:#4A7CF7;text-transform:uppercase;margin-bottom:12px;">Math Mission Thailand</div>
        <div style="font-family:'Fraunces',serif;font-size:36px;font-weight:300;
                    color:#1B2B6B;line-height:1.1;margin-bottom:6px;">
          Welcome to<br><em style="font-style:italic;color:#4A7CF7;">MathComp</em>
        </div>
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

# ══════════════════════════════════════════════
# Page: Dashboard
# ══════════════════════════════════════════════
def page_dashboard():
    require_auth(); inject_css()
    uid  = st.session_state["uid"]
    name = st.session_state.get("display_name","Student")
    topbar("Dashboard")

    sessions = []
    try:
        sessions = [s.to_dict() for s in
                    db.collection("users").document(uid).collection("exam_sessions")
                    .order_by("timestamp_start",direction=firestore.Query.DESCENDING).limit(5).stream()]
    except: pass

    if sessions:
        last = sessions[0]; avg = round(sum(s["pct"] for s in sessions)/len(sessions),1)
        m1,m2,m3,m4 = f"{last['raw_score']} / {last['max_score']}",f"{last['pct']}%",str(len(sessions)),f"{avg}%"
        s1,s2,s3,s4 = last.get('competition','—'),"last session","exams taken","all time"
    else:
        m1=m2=m3=m4="—"; s1=s2=s3=s4=""

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

    # Admin shortcut banner — only visible to admin
    if st.session_state.get("role") == "admin":
        st.markdown("""
        <div style="background:linear-gradient(135deg,#1B2B6B,#243580);border-radius:12px;
                    padding:16px 24px;margin-bottom:20px;display:flex;align-items:center;gap:16px;">
          <span style="font-size:28px;">⚙️</span>
          <div style="flex:1;">
            <div style="font-size:14px;font-weight:600;color:#fff;margin-bottom:2px;">Admin Panel</div>
            <div style="font-size:12px;color:rgba(255,255,255,.5);">Import questions · Manage members · Competition settings</div>
          </div>
        </div>""", unsafe_allow_html=True)
        col_ab1, col_ab2 = st.columns(2)
        if col_ab1.button("Open Admin Panel →", type="primary", key="admin_shortcut", use_container_width=True):
            st.session_state["page"] = "admin"; st.rerun()
        if col_ab2.button("📊 Analytics Dashboard →", key="analytics_shortcut", use_container_width=True):
            st.session_state["page"] = "admin_analytics"; st.rerun()
        st.divider()

    st.markdown('<span class="mc-section-lbl">Start a new exam</span>', unsafe_allow_html=True)
    st.markdown('<div class="mc-card">', unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        # Pre-fill from direct competition URL
        default_comp = st.session_state.pop("_prefill_comp","") if "_prefill_comp" in st.session_state else None
        comp_keys    = list(get_all_competitions().keys())
        comp_idx     = comp_keys.index(default_comp) if default_comp and default_comp in comp_keys else 0
        competition  = st.selectbox("Competition", comp_keys, index=comp_idx)
        comp_info   = get_all_competitions()[competition]
        st.caption(comp_info["description"])
        level = st.selectbox("Level / Division", comp_info["levels"])
    with cb:
        difficulty  = st.selectbox("Difficulty", DIFFICULTY_OPTIONS)
        n_questions = st.slider("Number of questions", 1, 100, 15, step=1)
        suggested   = n_questions * comp_info["secs_per_q"]
        st.caption(f"Suggested time: **{suggested//60} min** ({comp_info['secs_per_q']}s per question)")

    rules = comp_info["scoring"]
    if rules["wrong"] < 0:
        st.markdown(f'<div class="mc-penalty">⚠️ Penalty scoring: Correct +{rules["correct"]} · Wrong {rules["wrong"]} · Blank {rules["blank"]}</div>', unsafe_allow_html=True)

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

    # Quick nav buttons
    qn1, qn2 = st.columns(2)
    if qn1.button("📋  My full history & download", use_container_width=True):
        st.session_state["page"]="history"; st.rerun()
    if qn2.button("🏆  View leaderboard", use_container_width=True):
        st.session_state["page"]="leaderboard"; st.rerun()

    if sessions:
        st.markdown('<span class="mc-section-lbl" style="display:block;margin-top:20px;">Recent sessions</span>', unsafe_allow_html=True)
        for s in sessions:
            ts  = s.get("timestamp_start"); dt = ts.strftime("%d %b %Y") if ts else "—"
            pct = s.get("pct",0)
            c1,c2,c3,c4 = st.columns([3,2,2,1])
            c1.markdown(f"**{s.get('competition','')}** · {s.get('level','')}")
            c2.markdown(f"<span style='font-size:13px;color:#8898CC;'>{dt}</span>", unsafe_allow_html=True)
            c3.markdown(f"{s.get('raw_score','')} / {s.get('max_score','')}  ({pct}%)")
            c4.markdown("🟢" if pct>=70 else ("🟡" if pct>=50 else "🔴"))

    st.markdown("</div>", unsafe_allow_html=True)
    footer()

# ══════════════════════════════════════════════
# Page: Exam
# ══════════════════════════════════════════════
def _go(idx):
    st.session_state["current_idx"] = idx
    # Write progress if in realtime competition
    if st.session_state.get("from_realtime"):
        qs = st.session_state.get("questions",[])
        answers = st.session_state.get("answers",{})
        answered = sum(1 for q in qs if answers.get(q["id"]) is not None)
        _write_progress(
            st.session_state.get("uid",""),
            st.session_state.get("competition",""),
            idx, answered, len(qs)
        )

def _write_progress(uid:str, comp:str, current_idx:int, answered:int, total:int):
    """Write student exam progress to Firestore for live monitoring."""
    try:
        rt_doc_id = comp.replace(" ","_").replace("/","_")
        db.collection("realtime_sessions").document(rt_doc_id)          .collection("progress").document(uid).set({
            "uid":          uid,
            "display_name": st.session_state.get("display_name","—"),
            "current_q":    current_idx + 1,
            "answered":     answered,
            "total":        total,
            "pct_done":     round(answered/total*100) if total>0 else 0,
            "updated_at":   datetime.now(timezone.utc),
            "status":       "in_progress",
        }, merge=True)
    except: pass

def _submit():
    uid=st.session_state["uid"]; qs=st.session_state["questions"]; answers=st.session_state["answers"]
    duration=int(time.time()-st.session_state["start_time"])
    result=compute_score(st.session_state["competition"],qs,answers)
    sid=save_session(uid,st.session_state["competition"],st.session_state["level"],
                     st.session_state["difficulty"],qs,answers,result,duration)
    # Mark as submitted in progress tracker
    try:
        comp = st.session_state.get("competition","")
        if st.session_state.get("from_realtime") and comp:
            rt_doc_id = comp.replace(" ","_").replace("/","_")
            db.collection("realtime_sessions").document(rt_doc_id)              .collection("progress").document(uid).set({
                "status":    "submitted",
                "pct_done":  100,
                "answered":  len(qs),
                "total":     len(qs),
                "current_q": len(qs),
                "updated_at":datetime.now(timezone.utc),
            }, merge=True)
    except: pass
    st.session_state.update({"page":"result","result":result,"session_id":sid,"duration":duration})
    st.rerun()

def page_exam():
    require_auth(); inject_css()
    qs       = st.session_state["questions"]
    answers  = st.session_state["answers"]
    flagged  = st.session_state["flagged"]
    idx      = st.session_state["current_idx"]
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
      <span style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);
                   font-family:'DM Mono',monospace;font-size:11px;padding:3px 10px;border-radius:4px;
                   color:rgba(255,255,255,.7);">{st.session_state['competition']}</span>
      <span style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.15);
                   font-family:'DM Mono',monospace;font-size:11px;padding:3px 10px;border-radius:4px;
                   color:rgba(255,255,255,.7);">{st.session_state['level']}</span>
      <span style="font-size:13px;color:#fff;font-weight:500;flex:1;">Question {idx+1} of {len(qs)}</span>
      <div style="display:flex;align-items:center;gap:8px;background:rgba(255,255,255,.1);
                  border:1px solid rgba(255,255,255,.15);border-radius:8px;padding:6px 14px;">
        <span style="font-size:9px;font-family:'DM Mono',monospace;letter-spacing:.1em;
                     color:rgba(255,255,255,.45);text-transform:uppercase;">Time left</span>
        <span style="font-family:'DM Mono',monospace;font-size:18px;font-weight:500;
                     color:{tc};letter-spacing:.08em;">{'⚠️ ' if warn else ''}{mins:02d}:{secs:02d}</span>
      </div>
    </div>""", unsafe_allow_html=True)

    if warn: st.warning("⚠️  Less than 5 minutes remaining!")

    answered_count = sum(1 for q in qs if answers.get(q["id"]) is not None)
    st.progress(answered_count/len(qs), text=f"{answered_count} of {len(qs)} answered")

    # Navigator
    dots_html = ""
    for i,q in enumerate(qs):
        if i==idx:
            dots_html += f'<span class="mc-nav-dot" style="background:#1B2B6B;border-color:#1B2B6B;color:#fff;font-weight:600;">{i+1}</span>'
        elif q["id"] in flagged:
            dots_html += f'<span class="mc-nav-dot" style="background:#FDF2F8;border-color:#F472B6;color:#9D174D;">🚩</span>'
        elif answers.get(q["id"]) is not None:
            dots_html += f'<span class="mc-nav-dot" style="background:#EEF3FF;border-color:#4A7CF7;color:#1B2B6B;">✓{i+1}</span>'
        else:
            dots_html += f'<span class="mc-nav-dot">{i+1}</span>'
    st.markdown(f'<div class="mc-nav-strip">{dots_html}</div>', unsafe_allow_html=True)

    # Question
    q = qs[idx]; qid = q["id"]
    # Per-question timer
    tpq = settings.get("time_per_question", 0)
    if tpq and tpq > 0:
        q_key = f"q_start_{idx}"
        if q_key not in st.session_state:
            st.session_state[q_key] = time.time()
        q_elapsed = time.time() - st.session_state[q_key]
        q_remain  = max(0, tpq - q_elapsed)
        qm, qs2   = divmod(int(q_remain), 60)
        qtc = "#EF4444" if q_remain < 10 else ("#F5A623" if q_remain < 30 else "#4A7CF7")
        q_timer_html = (
            f'<span style="background:rgba(74,124,247,.1);border:1px solid #C8D8FF;'
            f'border-radius:6px;padding:3px 10px;font-family:monospace;'
            f'font-size:11px;color:{qtc};font-weight:600;">⏱ {qm:02d}:{qs2:02d}</span>'
        )
        if q_remain == 0:
            # Auto-advance to next question
            if idx < len(qs)-1:
                st.session_state["current_idx"] = idx + 1
            st.rerun()
    else:
        q_timer_html = ""

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
      <span style="font-family:'DM Mono',monospace;font-size:11px;color:#8898CC;">Q{idx+1} / {len(qs)}</span>
      <span style="font-size:11px;font-family:'DM Mono',monospace;padding:3px 10px;border-radius:20px;
                   background:#EEF3FF;border:1px solid #C8D8FF;color:#4A7CF7;">{q.get('topic','')}</span>
      {q_timer_html}
    </div>""", unsafe_allow_html=True)

    if q.get("question_image_url"): st.image(q["question_image_url"], use_container_width=True)
    if q.get("question_text"):      st.markdown(q["question_text"])
    st.write("")

    answer_type = q.get("answer_type","mc4"); current_ans = answers.get(qid)
    if answer_type in ("mc4","mc5"):
        choices = q.get("choices",[]); labels = [chr(65+i) for i in range(len(choices))]
        options = [f"{labels[i]}.  {choices[i]}" for i in range(len(choices))]
        cur = options[labels.index(current_ans.upper())] if current_ans and current_ans.upper() in labels else None
        choice = st.radio("Select your answer:", options, index=options.index(cur) if cur else None, key=f"r_{qid}")
        if choice: answers[qid]=choice[0]; st.session_state["answers"]=answers
    else:
        lbl = "Enter integer answer:" if answer_type=="integer" else "Enter decimal answer:"
        val = st.text_input(lbl, value=current_ans or "", key=f"i_{qid}")
        if val:
            try:
                int(val) if answer_type=="integer" else float(val)
                answers[qid]=val; st.session_state["answers"]=answers
            except ValueError: st.error("Please enter a valid number.")

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
        if ca.button("Yes, submit now", type="primary"):
            st.session_state.pop("confirm_submit",None); _submit()
        if cb.button("Go back"):
            st.session_state.pop("confirm_submit",None); st.rerun()
    footer()

# ══════════════════════════════════════════════
# Page: Result
# ══════════════════════════════════════════════
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
      <div style="font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.15em;
                  color:rgba(255,255,255,.4);text-transform:uppercase;margin-bottom:14px;position:relative;">
        {competition} · {level} · {len(qs)} questions · {datetime.now().strftime('%d %b %Y')}
      </div>
      <div class="mc-result-score">{result['raw_score']} <span>/ {result['max_score']}</span></div>
      <div class="mc-result-meta">
        <div class="mc-rm"><div class="mc-rm-val">{result['pct']}%</div><div class="mc-rm-lbl">Accuracy</div></div>
        <div class="mc-rm"><div class="mc-rm-val">{duration//60}m {duration%60}s</div><div class="mc-rm-lbl">Time taken</div></div>
        <div class="mc-rm"><div class="mc-rm-val">{correct_c} / {len(qs)}</div><div class="mc-rm-lbl">Correct</div></div>
        <div class="mc-rm"><div class="mc-rm-val">{wrong_c}</div><div class="mc-rm-lbl">Wrong</div></div>
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
        strength,weakness = sw(result["topic_breakdown"])
        st.markdown(bars + f"""
        <div class="mc-insight-good"><div class="mc-insight-lbl">Strength</div><div class="mc-insight-text">{strength}</div></div>
        <div class="mc-insight-bad"><div class="mc-insight-lbl">Needs work</div><div class="mc-insight-text">{weakness}</div></div>
        """, unsafe_allow_html=True)

    st.divider()

    # ── AI Performance Analysis ──────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,#EEF3FF,#FDF2F8);
                border:1.5px solid #C8D8FF;border-radius:16px;padding:20px 24px;margin-bottom:4px;">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
        <span style="font-size:24px;">🤖</span>
        <div>
          <div style="font-size:15px;font-weight:600;color:#1B2B6B;">AI Performance Analysis</div>
          <div style="font-size:12px;color:#8898CC;">Powered by Claude · Personalized coaching report</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Run analysis automatically or on button press
    if "ai_analysis" not in st.session_state:
        st.session_state["ai_analysis"] = None
        st.session_state["ai_analysis_loading"] = False

    if st.session_state.get("ai_analysis"):
        # Show cached analysis
        st.markdown(
            f'<div style="background:#fff;border:1.5px solid #E8ECF8;border-radius:12px;'
            f'padding:24px 28px;line-height:1.8;">{st.session_state["ai_analysis"]}</div>',
            unsafe_allow_html=True
        )
        if st.button("🔄  Regenerate analysis", key="regen_ai"):
            st.session_state["ai_analysis"] = None
            st.rerun()
    else:
        col_ai1, col_ai2 = st.columns([3, 1])
        col_ai1.markdown(
            "<p style='color:#5060A0;font-size:14px;margin:8px 0;'>"
            "Get a personalized coaching report — strengths, weaknesses, and study recommendations.</p>",
            unsafe_allow_html=True
        )
        if col_ai2.button("✨  Analyse my results", type="primary", key="run_ai", use_container_width=True):
            with st.spinner("Claude is analysing your performance…"):
                analysis = ai_analyze_performance(
                    name        = st.session_state.get("display_name", "Student"),
                    competition = competition,
                    level       = level,
                    result      = result,
                    questions   = qs,
                    duration    = duration,
                )
                st.session_state["ai_analysis"] = analysis
            st.rerun()

    st.divider()
    st.subheader("Question review")
    st.caption(f"✅ {correct_c} correct  ❌ {wrong_c} wrong  ⬜ {blank_c} blank")

    for i,(q,pq) in enumerate(zip(qs,result["per_question"])):
        chosen=pq["chosen"] or "—"; correct=pq["right_answer"] or "—"
        icon="✅" if pq["correct"] else ("⬜" if pq["chosen"] is None else "❌")
        with st.expander(f"{icon}  Q{i+1} · {q.get('topic','—')} · Your answer: **{chosen}** · Correct: **{correct}**"):
            if q.get("question_image_url"): st.image(q["question_image_url"],use_container_width=True)
            if q.get("question_text"):      st.markdown(q["question_text"])
            st.divider()
            if settings.get("show_answer_after_submit",True):
                if q.get("solution_image_url"): st.image(q["solution_image_url"],caption="Solution",use_container_width=True)
                if q.get("solution_text"):      st.markdown("**Solution:**"); st.markdown(q["solution_text"])
                if not q.get("solution_text") and not q.get("solution_image_url"): st.caption("No solution available.")
            else: st.caption("Solutions are not shown for this competition.")

    st.markdown("</div>", unsafe_allow_html=True)
    st.divider()
    _CLR = ("questions","answers","flagged","current_idx","start_time","time_limit",
            "result","session_id","duration","confirm_submit","exam_settings",
            "ai_analysis","ai_analysis_loading")
    b1,b2 = st.columns(2)
    if b1.button("← Back to dashboard", use_container_width=True):
        for k in _CLR: st.session_state.pop(k,None)
        st.session_state["page"]="dashboard"; st.rerun()
    if b2.button("Take another exam →", type="primary", use_container_width=True):
        for k in _CLR: st.session_state.pop(k,None)
        st.session_state["page"]="dashboard"; st.rerun()
    footer()

# ══════════════════════════════════════════════
# Page: Admin
# ══════════════════════════════════════════════
def page_history():
    require_auth(); inject_css()
    uid  = st.session_state["uid"]
    name = st.session_state.get("display_name","Student")
    topbar("My History")

    try:
        sessions = [s.to_dict() for s in
                    db.collection("users").document(uid)
                    .collection("exam_sessions")
                    .order_by("timestamp_start",direction=firestore.Query.DESCENDING)
                    .limit(100).stream()]
    except Exception as e:
        st.error(f"Error loading history: {e}"); sessions=[]

    st.markdown(f"""
    <div class="mc-hero">
      <div class="mc-hero-eyebrow">Performance history</div>
      <div class="mc-hero-title">{name}'s <em>results</em></div>
      <div class="mc-metrics">
        <div class="mc-metric"><div class="mc-metric-label">Sessions</div>
          <div class="mc-metric-val">{len(sessions)}</div></div>
        <div class="mc-metric"><div class="mc-metric-label">Avg Accuracy</div>
          <div class="mc-metric-val">{round(sum(s.get("pct",0) for s in sessions)/len(sessions),1) if sessions else 0}%</div></div>
        <div class="mc-metric"><div class="mc-metric-label">Best Score</div>
          <div class="mc-metric-val">{max((s.get("pct",0) for s in sessions),default=0)}%</div></div>
        <div class="mc-metric"><div class="mc-metric-label">Competitions</div>
          <div class="mc-metric-val">{len(set(s.get("competition","") for s in sessions))}</div></div>
      </div>
    </div>
    <div class="mc-body">""", unsafe_allow_html=True)

    # Download buttons
    col_dl1, col_dl2, _ = st.columns([1,1,2])
    with col_dl1:
        if sessions:
            html_bytes = generate_pdf_report(name, sessions)
            st.download_button(
                "📄  Download HTML Report",
                data=html_bytes,
                file_name=f"mathcomp_report_{name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True,
            )
    with col_dl2:
        if sessions:
            # CSV export — collect all fieldnames first across all sessions
            base_fields = ["date","competition","level","difficulty",
                           "score","max","pct","duration_sec"]
            all_topic_keys = []
            for s in sessions:
                for t in s.get("topic_breakdown",{}).keys():
                    key = t.lower().replace(" ","_") + "_pct"
                    if key not in all_topic_keys:
                        all_topic_keys.append(key)
            all_fields = base_fields + sorted(all_topic_keys)

            rows_csv = []
            for s in sessions:
                ts  = s.get("timestamp_start")
                tbd = s.get("topic_breakdown",{})
                row = {
                    "date":         ts.strftime("%Y-%m-%d") if ts else "",
                    "competition":  s.get("competition",""),
                    "level":        s.get("level",""),
                    "difficulty":   s.get("difficulty",""),
                    "score":        s.get("raw_score",""),
                    "max":          s.get("max_score",""),
                    "pct":          s.get("pct",""),
                    "duration_sec": s.get("duration_sec",""),
                }
                # Fill topic columns — blank if topic not in this session
                for t, v in tbd.items():
                    key = t.lower().replace(" ","_") + "_pct"
                    row[key] = round(v["correct"]/v["total"]*100) if v.get("total",0)>0 else 0
                rows_csv.append(row)

            buf = io.StringIO()
            w   = csv.DictWriter(buf, fieldnames=all_fields, extrasaction="ignore")
            w.writeheader()
            for row in rows_csv:
                # Fill missing topic columns with empty string
                for f in all_fields:
                    row.setdefault(f, "")
                w.writerow(row)

            st.download_button(
                "📊  Download CSV",
                data=buf.getvalue().encode(),
                file_name=f"mathcomp_scores_{name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.divider()

    # Filter
    comps = sorted(set(s.get("competition","") for s in sessions))
    flt   = st.selectbox("Filter by competition", ["All"] + comps, key="hist_filter")
    show  = [s for s in sessions if flt=="All" or s.get("competition","")==flt]

    if not show:
        st.info("No sessions found.")
    else:
        for s in show:
            ts   = s.get("timestamp_start"); dt = ts.strftime("%d %b %Y  %H:%M") if ts else "—"
            pct  = s.get("pct",0)
            tbd  = s.get("topic_breakdown",{})
            dot  = "🟢" if pct>=70 else ("🟡" if pct>=50 else "🔴")
            with st.expander(f"{dot}  {s.get('competition','')} · {s.get('level','')} · {s.get('difficulty','').capitalize()} · **{s.get('raw_score','')} / {s.get('max_score','')}** ({pct}%) · {dt}"):
                c1,c2 = st.columns(2)
                with c1:
                    st.markdown("**Topic breakdown**")
                    for topic,v in tbd.items():
                        tp = round(v["correct"]/v["total"]*100) if v["total"]>0 else 0
                        color = "#4A7CF7" if tp>=50 else "#F472B6"
                        st.markdown(
                            f'<div class="mc-topic-row"><span class="mc-topic-name">{topic}</span>'
                            f'<div class="mc-bar-bg"><div class="mc-bar-fill" style="width:{tp}%;background:{color};"></div></div>'
                            f'<span class="mc-bar-pct">{tp}%</span></div>',
                            unsafe_allow_html=True)
                with c2:
                    dur = s.get("duration_sec",0)
                    st.markdown(f"**Duration:** {dur//60}m {dur%60}s")
                    st.markdown(f"**Questions:** {s.get('total_questions','—')}")
                    answers_map = s.get("answers",{})
                    correct = sum(1 for a in answers_map.values() if a.get("is_correct"))
                    wrong   = sum(1 for a in answers_map.values() if not a.get("is_correct") and a.get("chosen"))
                    blank   = sum(1 for a in answers_map.values() if not a.get("chosen"))
                    st.markdown(f"✅ {correct} correct &nbsp; ❌ {wrong} wrong &nbsp; ⬜ {blank} blank")

                # ── Per-question answer log ───────────────────────
                if answers_map:
                    st.divider()
                    st.markdown("**Answer log**")
                    # Table header
                    h1,h2,h3,h4,h5,h6 = st.columns([1,4,2,2,2,2])
                    for col,lbl in zip([h1,h2,h3,h4,h5,h6],
                                       ["Q","Topic","Your answer","Correct","Result","Time"]):
                        col.markdown(f"<span style='font-size:11px;color:#8898CC;text-transform:uppercase;"
                                     f"letter-spacing:.06em;font-family:monospace;'>{lbl}</span>",
                                     unsafe_allow_html=True)
                    st.markdown("<hr style='margin:4px 0;border-color:#E8ECF8;'>", unsafe_allow_html=True)
                    for i, (qid, ans) in enumerate(sorted(answers_map.items()), 1):
                        ok     = ans.get("is_correct", False)
                        chosen = ans.get("chosen") or "—"
                        right  = ans.get("correct") or "—"
                        topic  = ans.get("topic","—")
                        tsec   = ans.get("time_sec", 0)
                        icon   = "✅" if ok else ("⬜" if not ans.get("chosen") else "❌")
                        r1,r2,r3,r4,r5,r6 = st.columns([1,4,2,2,2,2])
                        r1.markdown(f"**{i}**")
                        r2.markdown(f"<span style='font-size:13px;'>{topic}</span>",
                                    unsafe_allow_html=True)
                        r3.markdown(f"`{chosen}`")
                        r4.markdown(f"`{right}`")
                        r5.markdown(icon)
                        r6.markdown(f"{tsec}s" if tsec else "—")

    st.markdown("</div>", unsafe_allow_html=True)
    footer()


# ══════════════════════════════════════════════
# Page: Leaderboard (student)
# ══════════════════════════════════════════════
def page_leaderboard():
    require_auth(); inject_css()
    topbar("Leaderboard")

    st.markdown("""
    <div class="mc-hero">
      <div class="mc-hero-eyebrow">Global ranking</div>
      <div class="mc-hero-title">Student <em>Leaderboard</em></div>
    </div>
    <div class="mc-body">""", unsafe_allow_html=True)

    comp_options = ["All"] + list(get_all_competitions().keys())
    c1,c2 = st.columns(2)
    lb_comp   = c1.selectbox("Competition", comp_options, key="lb_comp")
    lb_metric = c2.selectbox("Rank by", ["Best accuracy (%)","Best raw score","Most sessions"], key="lb_metric")

    if st.button("🔄  Load leaderboard", type="primary"):
        st.session_state["lb_loaded"] = True

    if st.session_state.get("lb_loaded"):
        with st.spinner("Loading…"):
            try:
                scores = []
                for u in db.collection("users").stream():
                    uid  = u.id; prof = u.to_dict()
                    if prof.get("role") == "admin": continue
                    name = prof.get("display_name","—")
                    sref = db.collection("users").document(uid).collection("exam_sessions")
                    if lb_comp != "All":
                        sref = sref.where("competition","==",lb_comp)
                    sess = [s.to_dict() for s in sref.stream()]
                    if not sess: continue
                    best_pct   = max(s.get("pct",0) for s in sess)
                    best_score = max(s.get("raw_score",0) for s in sess)
                    n_sess     = len(sess)
                    avg_pct    = round(sum(s.get("pct",0) for s in sess)/n_sess,1)
                    scores.append({"name":name,"best_pct":best_pct,"best_score":best_score,
                                   "n_sess":n_sess,"avg_pct":avg_pct,"uid":uid})

                # Sort
                if lb_metric == "Best accuracy (%)":
                    scores.sort(key=lambda x:x["best_pct"], reverse=True)
                elif lb_metric == "Best raw score":
                    scores.sort(key=lambda x:x["best_score"], reverse=True)
                else:
                    scores.sort(key=lambda x:x["n_sess"], reverse=True)

                if not scores:
                    st.info("No data found.")
                else:
                    my_uid = st.session_state.get("uid","")
                    st.markdown(f"**{len(scores)} students ranked**")
                    st.divider()
                    for rank, s in enumerate(scores, 1):
                        medal = "🥇" if rank==1 else ("🥈" if rank==2 else ("🥉" if rank==3 else f"**#{rank}**"))
                        is_me = s["uid"] == my_uid
                        bg    = "background:#EEF3FF;border-radius:8px;padding:4px 8px;" if is_me else ""
                        c1,c2,c3,c4,c5 = st.columns([1,4,2,2,2])
                        c1.markdown(medal)
                        c2.markdown(f'<span style="{bg}">{"**" if is_me else ""}{s["name"]}{"** ← You" if is_me else ""}</span>', unsafe_allow_html=True)
                        c3.markdown(f"Best: **{s['best_pct']}%**")
                        c4.markdown(f"Avg: {s['avg_pct']}%")
                        c5.markdown(f"{s['n_sess']} session{'s' if s['n_sess']!=1 else ''}")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
    footer()


# ══════════════════════════════════════════════
# Page: Admin Analytics Dashboard
# ══════════════════════════════════════════════
def page_realtime():
    """
    Dedicated page for students joining via a realtime competition link.
    Shows waiting room if not open, exam setup if open, closed message if closed.
    """
    require_auth(); inject_css()
    comp_name = st.session_state.get("rt_comp","")
    uid       = st.session_state["uid"]
    name      = st.session_state.get("display_name","Student")

    # Load realtime session status
    rt_doc_id = comp_name.replace(" ","_").replace("/","_")
    try:
        rt_doc  = db.collection("realtime_sessions").document(rt_doc_id).get()
        rt_data = rt_doc.to_dict() if rt_doc.exists else {}
        status  = rt_data.get("status","not started")
    except Exception as e:
        st.error(f"Error loading competition status: {e}")
        status = "not started"

    # ── Roster check ──────────────────────────
    require_roster = rt_data.get("require_roster", False)
    roster         = rt_data.get("roster", [])
    if require_roster and roster and uid not in roster:
        topbar(comp_name)
        st.markdown(f"""
        <div class="mc-hero">
          <div class="mc-hero-eyebrow">Realtime Competition</div>
          <div class="mc-hero-title"><em>{comp_name}</em></div>
        </div>
        <div class="mc-body" style="text-align:center;padding:60px 28px;">
          <div style="font-size:64px;margin-bottom:16px;">🚫</div>
          <div style="font-family:'Fraunces',serif;font-size:26px;font-weight:300;
                      color:#1B2B6B;margin-bottom:12px;">You are not registered for this competition</div>
          <div style="font-size:15px;color:#8898CC;margin-bottom:24px;">
            <strong>{name}</strong>, your account is not on the roster for <strong>{comp_name}</strong>.<br>
            Please contact your administrator to be added.
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button("← Back to Dashboard"):
            st.session_state["page"] = "dashboard"; st.rerun()
        footer(); return

    topbar(comp_name)

    # ── CLOSED ────────────────────────────────
    if status == "closed":
        st.markdown(f"""
        <div class="mc-hero">
          <div class="mc-hero-eyebrow">Realtime Competition</div>
          <div class="mc-hero-title"><em>{comp_name}</em></div>
        </div>
        <div class="mc-body" style="text-align:center;padding:60px 28px;">
          <div style="font-size:64px;margin-bottom:16px;">🔒</div>
          <div style="font-family:'Fraunces',serif;font-size:28px;font-weight:300;
                      color:#1B2B6B;margin-bottom:12px;">This competition has closed</div>
          <div style="font-size:15px;color:#8898CC;margin-bottom:32px;">
            The exam window for <strong>{comp_name}</strong> has ended.<br>
            Thank you for participating!
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button("← Back to Dashboard", use_container_width=False):
            st.session_state["page"] = "dashboard"; st.rerun()
        footer(); return

    # ── NOT STARTED / WAITING ─────────────────
    if status != "open":
        # RELIABLE APPROACH: Use a Streamlit checkbox that JS toggles.
        # Toggling a checkbox value triggers a widget state change
        # which causes st.rerun() WITHOUT any page reload.
        # Session state (uid, rt_comp, page) is fully preserved.

        cb_key = f"rt_cb_{rt_doc_id}"
        cb_val = st.session_state.get(cb_key, False)

        # Render the checkbox (will be hidden by CSS)
        new_cb = st.checkbox("poll_trigger", value=cb_val, key=cb_key)
        if new_cb != cb_val:
            # Checkbox was toggled by JS — rerun to re-read Firestore status
            st.rerun()

        # JS: toggle the checkbox every 6 seconds
        components.html("""
<script>
(function() {
  function toggleCheckbox() {
    try {
      var cbs = window.parent.document.querySelectorAll('input[type="checkbox"]');
      for (var i = 0; i < cbs.length; i++) {
        var label = cbs[i].closest('label');
        if (label && label.innerText.trim() === 'poll_trigger') {
          cbs[i].click();
          return;
        }
      }
    } catch(e) {}
  }
  // Start polling after 6 seconds, repeat every 6 seconds
  setTimeout(function poll() {
    toggleCheckbox();
    setTimeout(poll, 6000);
  }, 6000);
})();
</script>""", height=0, scrolling=False)

        # Hide the poll checkbox completely
        st.markdown("""
<style>
div[data-testid="stCheckbox"]:has(label p) { display: none !important; }
</style>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="mc-hero">
          <div class="mc-hero-eyebrow">Realtime Competition · Waiting Room</div>
          <div class="mc-hero-title"><em>{comp_name}</em></div>
        </div>
        <div class="mc-body" style="text-align:center;padding:48px 28px;">
          <div style="font-size:64px;margin-bottom:16px;
                      animation:pulse_wait 2s ease-in-out infinite;">⏳</div>
          <div style="font-family:'Fraunces',serif;font-size:26px;font-weight:300;
                      color:#1B2B6B;margin-bottom:10px;">Waiting for competition to start…</div>
          <div style="font-size:15px;color:#5060A0;margin-bottom:8px;">
            Welcome, <strong>{name}</strong>
          </div>
          <div style="font-size:20px;font-weight:700;color:#1B2B6B;margin-bottom:24px;">
            {comp_name}
          </div>
          <div style="background:#EEF3FF;border:1.5px solid #C8D8FF;border-radius:12px;
                      padding:14px 24px;display:inline-block;margin-bottom:20px;">
            <div style="font-size:12px;color:#8898CC;margin-bottom:4px;letter-spacing:.08em;
                        text-transform:uppercase;font-family:monospace;">Status</div>
            <div style="font-size:17px;font-weight:600;color:#F5A623;">
              🟡 Waiting for admin to open the exam
            </div>
          </div>
          <div style="font-size:13px;color:#8898CC;margin-top:8px;line-height:1.8;">
            ✅ You are logged in as <strong>{name}</strong><br>
            🔄 Auto-checks every 6 seconds — no re-login needed<br>
            ▶️ Exam will appear on this screen the moment admin opens it
          </div>
        </div>
        <style>
        @keyframes pulse_wait {{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
        </style>""", unsafe_allow_html=True)

        _, mid, _ = st.columns([2,1,2])
        if mid.button("🔄  Check now", use_container_width=True, type="primary"):
            st.rerun()

        footer()
        return

    # ── OPEN — show exam setup ─────────────────
    st.markdown(f"""
    <div class="mc-hero">
      <div class="mc-hero-eyebrow">🟢 Competition is LIVE</div>
      <div class="mc-hero-title"><em>{comp_name}</em></div>
    </div>
    <div class="mc-body">""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#F0FFF9,#EEF3FF);border:1.5px solid #A7F3D0;
                border-radius:12px;padding:16px 24px;margin-bottom:20px;display:flex;
                align-items:center;gap:12px;">
      <span style="font-size:28px;">🟢</span>
      <div>
        <div style="font-size:15px;font-weight:600;color:#1B2B6B;">The competition is now open!</div>
        <div style="font-size:13px;color:#5060A0;">
          Configure your exam below and click <strong>Start Exam</strong> to begin.
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Get competition info
    all_comps = get_all_competitions()
    if comp_name not in all_comps:
        st.error(f"Competition '{comp_name}' not found in catalog.")
        footer(); return

    comp_info = all_comps[comp_name]
    st.caption(comp_info.get("description",""))

    # Level + difficulty + questions
    c1,c2,c3 = st.columns(3)
    level       = c1.selectbox("Level / Division", comp_info["levels"], key="rt_level")
    difficulty  = c2.selectbox("Difficulty", DIFFICULTY_OPTIONS, key="rt_diff")
    n_questions = c3.slider("Number of questions", 1, 100, 20, key="rt_nq")

    suggested = n_questions * comp_info["secs_per_q"]
    st.caption(f"Suggested time: **{suggested//60} min** ({comp_info['secs_per_q']}s per question)")

    rules = comp_info["scoring"]
    if rules.get("wrong",0) < 0:
        st.markdown(
            f'<div class="mc-penalty">⚠️ Penalty scoring: '
            f'Correct +{rules["correct"]} · Wrong {rules["wrong"]} · Blank {rules["blank"]}</div>',
            unsafe_allow_html=True)

    # Show AI-resistant settings for this competition
    settings = load_settings(comp_name)
    ai_layers = [k for k in ["anti_copy_text","noise_canvas","block_ctrl_c",
                              "block_text_selection","block_paste_answer","block_drag",
                              "block_right_click","tab_switch_warning","block_printscreen",
                              "clipboard_api_override","devtools_detection","screen_capture_block"]
                 if settings.get(k)]
    if ai_layers:
        st.markdown(
            f'<div style="background:#FDF2F8;border:1px solid #FBCFE8;border-radius:8px;'
            f'padding:10px 14px;font-size:12px;color:#9D174D;margin-bottom:12px;">'
            f'🛡️ <strong>AI-resistant mode active</strong> · {len(ai_layers)}/12 layers enabled</div>',
            unsafe_allow_html=True)

    if st.button("🚀  Start Competition Exam", type="primary", use_container_width=True):
        with st.spinner("Loading questions…"):
            qs = fetch_questions(comp_name, level, difficulty, n_questions)
        if not qs:
            st.error("No questions found for this selection. Please try a different difficulty or level.")
        else:
            st.session_state.update({
                "page":          "exam",
                "competition":   comp_name,
                "level":         level,
                "difficulty":    difficulty,
                "questions":     qs,
                "answers":       {},
                "flagged":       set(),
                "current_idx":   0,
                "start_time":    time.time(),
                "time_limit":    suggested,
                "exam_settings": settings,   # ← includes all AI-resistant settings
                "from_realtime": True,
            })
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    footer()


# ══════════════════════════════════════════════
# Page: Admin View Student History
# ══════════════════════════════════════════════

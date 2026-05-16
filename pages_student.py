"""
MathComp — pages_student.py
Student portal, exam taking interface, and analytics rendering
"""
import streamlit as st
import time, random
import plotly.graph_objects as go
from shared import get_all_competitions, DIFFICULTY_OPTIONS, compute_score, get_anti_ai_js, load_settings, db

def page_login():
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("""
        <div class="premium-card" style="text-align: center; padding: 3rem 2rem;">
            <div style="width: 64px; height: 64px; background: #EEF2FF; border-radius: 16px; margin: 0 auto 1.5rem; display: flex; align-items: center; justify-content: center; font-size: 32px;">📐</div>
            <h2 style="margin-bottom: 0.5rem;">Math Mission Thailand</h2>
            <p style="color: #64748B; margin-bottom: 2rem;">Platform การสอบคณิตศาสตร์มาตรฐานสากล</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("อีเมลผู้ใช้งาน", placeholder="student@example.com")
            pwd = st.text_input("รหัสผ่าน", type="password", placeholder="••••••••")
            role_mock = st.selectbox("โหมดเข้าสู่ระบบ (จำลอง)", ["Student", "Admin"])
            
            submit = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True, type="primary")
            if submit:
                if email and pwd:
                    st.session_state.update({
                        "uid": f"user_{int(time.time())}",
                        "display_name": email.split("@")[0].title(),
                        "role": role_mock.lower(),
                        "page": "dashboard"
                    })
                    st.rerun()
                else:
                    st.error("กรุณากรอกข้อมูลให้ครบถ้วน")

def page_dashboard():
    name = st.session_state.get("display_name", "Student")
    
    st.markdown(f"""
    <div style="margin-bottom: 2rem;">
        <h1 style="font-size: 2rem; margin-bottom: 0.5rem;">สวัสดี, {name} 👋</h1>
        <p style="color: #64748B; font-size: 1.1rem;">เลือกชุดข้อสอบและเริ่มต้นการทดสอบของคุณ</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("คะแนนสูงสุด", "85%", "+5% จากครั้งก่อน")
    c2.metric("จำนวนข้อสอบที่ทำ", "120 ข้อ")
    c3.metric("เวลาฝึกซ้อมสะสม", "14 ชม.")
    
    st.markdown("<hr style='margin: 2rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)
    
    # Exam Configurator
    with st.container():
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("<h3>🎯 สร้างชุดข้อสอบ (Exam Configurator)</h3>", unsafe_allow_html=True)
        
        comps = get_all_competitions()
        col_a, col_b = st.columns(2)
        
        with col_a:
            comp_name = st.selectbox("รายการสอบ", list(comps.keys()))
            level = st.selectbox("ระดับชั้น", comps[comp_name]["levels"])
            
        with col_b:
            diff = st.selectbox("ความยาก", DIFFICULTY_OPTIONS)
            n_q = st.number_input("จำนวนข้อ", min_value=1, max_value=50, value=15)
            
        est_time = (n_q * comps[comp_name].get("secs_per_q", 120)) // 60
        st.info(f"⏱️ **เวลาที่แนะนำ:** {est_time} นาที (อ้างอิงจากมาตรฐานการสอบ {comp_name})")
        
        if st.button("เริ่มทำข้อสอบทันที 🚀", type="primary", use_container_width=True):
            # Fetch questions from DB or generate mock
            st.session_state.update({
                "page": "exam", "competition": comp_name, "level": level, "difficulty": diff,
                "questions": _generate_mock_questions(n_q), # Replace with actual DB fetch
                "answers": {}, "flagged": set(), "current_idx": 0,
                "start_time": time.time(), "time_limit": est_time * 60,
                "settings": load_settings(comp_name)
            })
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

def page_exam():
    if "questions" not in st.session_state:
        st.session_state["page"] = "dashboard"
        st.rerun()
        
    qs = st.session_state["questions"]
    ans = st.session_state["answers"]
    idx = st.session_state["current_idx"]
    flg = st.session_state["flagged"]
    
    # Anti-cheat injection
    components.html(get_anti_ai_js(st.session_state.get("settings", {})), height=0)
    
    # Timer logic
    elapsed = time.time() - st.session_state["start_time"]
    remaining = max(0.0, st.session_state["time_limit"] - elapsed)
    mins, secs = divmod(int(remaining), 60)
    
    if remaining == 0:
        st.toast("หมดเวลา! กำลังส่งคำตอบอัตโนมัติ...", icon="⏳")
        time.sleep(1)
        _submit_exam()
        return

    # Sticky Header
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; background: white; padding: 1rem 2rem; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 1.5rem; position: sticky; top: 0; z-index: 999; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
        <div>
            <div style="font-weight: 600; font-size: 1.1rem; color: #1E3A8A;">{st.session_state['competition']}</div>
            <div style="font-size: 0.85rem; color: #64748B;">{st.session_state['level']} • ข้อที่ {idx+1}/{len(qs)}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase; font-weight: 600;">Time Remaining</div>
            <div style="font-size: 1.5rem; font-weight: 700; color: {'#EF4444' if remaining < 300 else '#1E3A8A'}; font-family: monospace;">
                {mins:02d}:{secs:02d}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress Bar
    progress = len(ans) / len(qs)
    st.progress(progress)
    
    # Question Card
    q = qs[idx]
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown(f"""
    <span style="background: #EEF2FF; color: #3B82F6; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; margin-bottom: 1rem; display: inline-block;">
        {q.get('topic', 'General')}
    </span>
    """, unsafe_allow_html=True)
    
    # Safe LaTeX rendering
    st.markdown(f"<div class='math-box'>{q['question_text']}</div>", unsafe_allow_html=True)
    
    # Options Rendering
    st.markdown("<br><strong style='color:#0F172A;'>เลือกคำตอบ:</strong>", unsafe_allow_html=True)
    
    options = [f"{chr(65+i)}. {c}" for i, c in enumerate(q.get("choices", []))]
    current_val = ans.get(q["id"])
    sel_idx = [chr(65+i) for i in range(len(options))].index(current_val) if current_val else None
    
    # Clean radio buttons
    choice = st.radio("Options", options, index=sel_idx, label_visibility="collapsed")
    if choice:
        ans[q["id"]] = choice[0] # Save just the letter (A, B, C, D)
        st.session_state["answers"] = ans

    st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer Navigation Controls
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if idx > 0:
            if st.button("← ข้อก่อนหน้า", use_container_width=True):
                st.session_state["current_idx"] -= 1
                st.rerun()
    with col2:
        is_flagged = q["id"] in flg
        if st.button("🏳️ ยกเลิกปักหมุด" if is_flagged else "🚩 ปักหมุดไว้ทบทวน", use_container_width=True):
            if is_flagged: flg.remove(q["id"])
            else: flg.add(q["id"])
            st.session_state["flagged"] = flg
            st.rerun()
    with col3:
        if idx < len(qs) - 1:
            if st.button("ข้อถัดไป →", type="primary", use_container_width=True):
                st.session_state["current_idx"] += 1
                st.rerun()
        else:
            if st.button("ส่งข้อสอบ ✅", type="primary", use_container_width=True):
                _submit_exam()

def _submit_exam():
    res = compute_score(st.session_state["competition"], st.session_state["questions"], st.session_state["answers"])
    st.session_state.update({"page": "result", "result": res})
    st.rerun()

def page_result():
    res = st.session_state.get("result", {})
    
    st.markdown("<div class='premium-card' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h2>สรุปผลการประเมิน</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='font-size: 4rem; font-weight: 700; color: #3B82F6; line-height: 1;'>{res.get('score', 0)}<span style='font-size: 2rem; color: #94A3B8;'> / {res.get('total', 0)}</span></div>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size: 1.2rem; color: #64748B;'>ความถูกต้อง: <strong>{res.get('pct', 0)}%</strong></p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Radar Chart
    tbd = res.get("topic_breakdown", {})
    if tbd:
        topics = list(tbd.keys())
        scores = [round((v["correct"] / max(1, v["total"])) * 100) for v in tbd.values()]
        
        fig = go.Figure(data=go.Scatterpolar(
            r=scores + [scores[0]], theta=topics + [topics[0]], 
            fill='toself', line_color='#3B82F6', fillcolor='rgba(59, 130, 246, 0.2)'
        ))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, margin=dict(t=20, b=20))
        
        st.markdown("<h3>🎯 การวิเคราะห์รายหัวข้อ (Skill Breakdown)</h3>", unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
    
    if st.button("กลับสู่หน้าหลัก", use_container_width=True, type="primary"):
        st.session_state["page"] = "dashboard"
        st.rerun()

def _generate_mock_questions(n):
    """Helper to generate mock questions if DB is offline"""
    qs = []
    for i in range(n):
        qs.append({
            "id": f"q_mock_{i}",
            "topic": random.choice(["Algebra", "Geometry", "Number Theory"]),
            "question_text": f"พิจารณาสมการ $\\int_{{0}}^{{\\infty}} e^{{-x^2}} dx$. ค่าของสมการนี้ตรงกับตัวเลือกใด?",
            "choices": ["$\\frac{\\sqrt{\\pi}}{2}$", "$\\sqrt{\\pi}$", "$\\frac{\\pi}{2}$", "$1$"],
            "correct_answer": "A"
        })
    return qs

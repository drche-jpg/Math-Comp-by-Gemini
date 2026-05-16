"""
MathComp — pages_student.py
Student flows: Adaptive question configuration, secure exam, and Radar analytics reports
© Math Mission Thailand 2026
"""
import streamlit as st
import time, random
import plotly.graph_objects as go
from shared import (
    inject_css, topbar, footer, db, get_all_competitions,
    DIFFICULTY_OPTIONS, compute_score, save_session, get_advanced_anti_ai_js,
    COLOR_PRIMARY, COLOR_SECONDARY, TOPICS
)

def page_login():
    inject_css()
    topbar("เข้าสู่ระบบจัดสอบออนไลน์", show_user=False)
    
    st.markdown("""
    <div style='max-width: 420px; margin: 40px auto; background: white; border-radius: 16px; padding: 35px; box-shadow: 0 10px 25px rgba(27,43,107,0.08);'>
        <div style='text-align: center; margin-bottom: 25px;'>
            <h2 style='margin: 0; font-size:24px;'>Math Mission Thailand</h2>
            <p style='color:#64748B; font-size:13px; margin-top:5px;'>Premium Assessment Portal</p>
        </div>
    """, unsafe_allow_html=True)
    
    u = st.text_input("ชื่อผู้ใช้งาน (Username / Email)", placeholder="เช่น chatawut_admin")
    p = st.text_input("รหัสผ่าน (Password)", type="password", placeholder="••••••••")
    
    role_sel = st.radio("ระดับสิทธิ์การเข้าถึง", ["นักเรียนในคลาส (Member)", "ผู้ดูแลระบบ (Admin)"], horizontal=True)
    
    if st.button("🔒 ยืนยันการลงชื่อเข้าใช้", type="primary", use_container_width=True):
        if u and p:
            role = "admin" if "Admin" in role_sel else "student"
            st.session_state.update({"uid": f"uid_{u}", "display_name": u.capitalize(), "role": role, "page": "dashboard"})
            st.rerun()
        else:
            st.error("กรุณากรอกข้อมูลบัญชีผู้ใช้ให้ครบถ้วน")
    st.markdown("</div>", unsafe_allow_html=True)
    footer()

def page_dashboard():
    inject_css()
    topbar("แผงควบคุมระบบคัดเลือกชุดข้อสอบ")
    
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<h3>🎯 ปรับแต่งและสร้างชุดข้อสอบรายบุคคล</h3>", unsafe_allow_html=True)
    
    comps = get_all_competitions()
    sc = st.selectbox("เลือกรายการสอบแข่งขันคณิตศาสตร์", list(comps.keys()))
    
    c_info = comps[sc]
    lvl = st.selectbox("เลือกระดับชั้นเรียน (Grade / Year)", c_info["levels"])
    diff = st.selectbox("เลือกระดับความยากของข้อสอบ", DIFFICULTY_OPTIONS)
    nq = st.slider("จำนวนข้อสอบที่ต้องการทดสอบ", 5, 30, 10, step=5)
    
    # Calculate algorithmic dynamic time suggestion
    t_per_q = c_info.get("default_time_per_q", 120)
    suggested_mins = (nq * t_per_q) // 60
    
    st.markdown(f"""
    <div style='background:#EEF3FF; border-left:4px solid {COLOR_SECONDARY}; padding:15px; border-radius:8px; margin: 20px 0;'>
        ℹ️ <strong>เวลาทำข้อสอบแนะนำ:</strong> ระบบสุ่มข้อสอบอัจฉริยะวิเคราะห์ว่ารายการนี้ควรใช้เวลาทำ <strong>{suggested_mins} นาที</strong>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 เริ่มต้นเข้าทำข้อสอบ (Start Assessment)", type="primary", use_container_width=True):
        mqs = []
        for i in range(nq):
            mqs.append({
                "id": f"q_{i+1}",
                "topic": random.choice(c_info["topics"]),
                "question_text": f"โจทย์ข้อที่ {i+1}: พิจารณาสมการพหุนาม $x^2 - 5x + 6 = 0$ จงคำนวณหาค่าของผลบวกของรากทั้งหมด",
                "choices": ["3", "5", "6", "2"],
                "correct_answer": "B"
            })
            
        st.session_state.update({
            "page": "exam", "competition": sc, "level": lvl, "difficulty": diff,
            "questions": mqs, "answers": {}, "flagged": set(), "current_idx": 0,
            "start_time": time.time(), "time_limit": suggested_mins * 60,
            "exam_settings": {"block_right_click": True, "block_ctrl_c": True}
        })
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    footer()

def page_exam():
    if "questions" not in st.session_state:
        st.warning("ไม่พบเซสชันการสอบที่ทำงานอยู่")
        return

    qs = st.session_state["questions"]
    ans = st.session_state["answers"]
    flg = st.session_state["flagged"]
    idx = st.session_state["current_idx"]
    setts = st.session_state.get("exam_settings", {})
    
    # Safety JS injection layer
    st.markdown(get_advanced_anti_ai_js(setts), unsafe_allow_html=True)
    
    rem = max(0.0, st.session_state["time_limit"] - (time.time() - st.session_state["start_time"]))
    mins, secs = divmod(int(rem), 60)
    
    if rem <= 0:
        st.error("⏱ หมดเวลาการทำข้อสอบแล้ว! กำลังนำส่งกระดาษคำตอบอัตโนมัติ...")
        time.sleep(1)
        _submit_final_exam()
        return

    warn = rem < 300
    t_bg = "linear-gradient(135deg, #FEE2E2, #FEF2F2)" if warn else "linear-gradient(135deg, #EEF3FF, #F4F7FF)"
    t_color = "#EF4444" if warn else "#1B2B6B"

    # Header Testing Panel Style
    st.markdown(f"""
    <div style='background:{COLOR_PRIMARY}; padding:20px 30px; border-radius:12px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;'>
        <div>
            <h3 style='color:white !important; margin:0; font-size:18px;'>{st.session_state['competition']}</h3>
            <span style='color:#93C5FD; font-size:12px;'>ระดับชั้น: {st.session_state['level']}</span>
        </div>
        <div style='background:{t_bg}; padding:8px 20px; border-radius:8px; border:1px solid #CBD5E1; text-align:center;'>
            <div style='font-size:10px; color:#64748B;'>เวลาที่เหลือ</div>
            <div style='font-size:20px; font-weight:700; color:{t_color}; font-family:monospace;'>{mins:02d}:{secs:02d}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Question Grid Navigation bar
    cols = st.columns(len(qs) if len(qs) <= 15 else 15)
    for i, item in enumerate(qs):
        c_idx = i % 15
        with cols[c_idx]:
            if i == idx: lbl = f"🎯 {i+1}"
            elif item["id"] in flg: lbl = "🚩"
            elif item["id"] in ans: lbl = f"✓ {i+1}"
            else: lbl = str(i+1)
            
            if st.button(lbl, key=f"n_s_{i}", use_container_width=True):
                st.session_state["current_idx"] = i
                st.rerun()

    q = qs[idx]
    st.markdown(f"""
    <div class='premium-card' style='margin-top:20px;'>
        <div style='display:flex; gap:10px; margin-bottom:12px;'>
            <span style='background:#EEF3FF; color:#4A7CF7; padding:2px 10px; border-radius:12px; font-size:11px; font-weight:600;'>หัวข้อ: {q.get('topic')}</span>
            <span style='background:#F1F5F9; color:#475569; padding:2px 10px; border-radius:12px; font-size:11px;'>คำถามข้อที่ {idx+1}/{len(qs)}</span>
        </div>
        <div class='math-container'>{q['question_text']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Choice handling matrix
    opts = [f"{lbl}. {txt}" for lbl, txt in zip(["A","B","C","D"], q["choices"])]
    curr_choice = ans.get(q["id"], "")
    sel_idx = ["A","B","C","D"].index(curr_choice) if curr_choice in ["A","B","C","D"] else None
    
    sel = st.radio("โปรดทำเครื่องหมายเลือกคำตอบ:", opts, index=sel_idx, key=f"r_ch_{q['id']}")
    if sel:
        ans[q["id"]] = sel[0]
        st.session_state["answers"] = ans

    # Nav footer control
    st.markdown("<br>", unsafe_allow_html=True)
    lc, mc, rc = st.columns(3)
    with lc:
        if idx > 0:
            if st.button("← ย้อนกลับข้อก่อนหน้า", use_container_width=True):
                st.session_state["current_idx"] = idx - 1
                st.rerun()
    with mc:
        is_f = q["id"] in flg
        if st.button("🏳️ เอาปักหมุดออก" if is_f else "🚩 ปักหมุดทบทวน", use_container_width=True):
            if is_f: flg.remove(q["id"])
            else: flg.add(q["id"])
            st.session_state["flagged"] = flg
            st.rerun()
    with rc:
        if idx < len(qs) - 1:
            if st.button("ข้อต่อไป →", type="primary", use_container_width=True):
                st.session_state["current_idx"] = idx + 1
                st.rerun()
        else:
            if st.button("🎉 ส่งกระดาษคำตอบ", type="primary", use_container_width=True):
                _submit_final_exam()

def _submit_final_exam():
    qs = st.session_state["questions"]
    ans = st.session_state["answers"]
    res = compute_score(st.session_state["competition"], qs, ans)
    save_session(st.session_state["uid"], st.session_state["competition"], st.session_state["level"], st.session_state["difficulty"], qs, ans, res, 120)
    st.session_state.update({"page": "result", "result": res})
    st.rerun()

def page_result():
    inject_css()
    topbar("รายงานผลและบทวิเคราะห์คะแนนสอบ")
    
    res = st.session_state.get("result", {})
    st.markdown("<div class='premium-card' style='text-align:center;'>", unsafe_allow_html=True)
    st.markdown(f"""
        <h2 style='margin:0;'>คะแนนรวมของคุณได้</h2>
        <div style='font-size:56px; font-weight:700; color:{COLOR_SECONDARY}; margin:10px 0;'>{res.get('score')} / {res.get('total')}</div>
        <p style='color:#64748B;'>เปอร์เซ็นต์ความสำเร็จของชุดข้อสอบ: <strong>{res.get('pct'):.1f}%</strong></p>
    """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Render Radar graph using Plotly
    bd = res.get("breakdown", {})
    cats = list(bd.keys())
    values = [(bd[c]["correct"]/max(1, bd[c]["total"]))*100 for c in cats]
    
    fig = go.Figure(data=go.Scatterpolar(r=values, theta=cats, fill='toself', line_color=COLOR_SECONDARY))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=350)
    
    st.markdown("<h3>📊 แผนภูมิเรดาร์วิเคราะห์ความแข็งแกร่งจำแนกตามรายวิชา</h3>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    
    if st.button("กลับไปยังหน้า Dashboard หลัก", use_container_width=True):
        st.session_state["page"] = "dashboard"
        st.rerun()
    footer()

def page_history(): inject_css(); topbar("ประวัติการทำข้อสอบย้อนหลัง"); st.info("ไม่พบรายการข้อมูลในฐานระบบขณะนี้"); footer()
def page_leaderboard(): inject_css(); topbar("ตารางคะแนนสูงสุดยอดนักคณิตศาสตร์"); st.info("จะเปิดเผยคะแนนทันทีเมื่อการแข่งขันสดสิ้นสุด"); footer()
def page_realtime(): inject_css(); topbar("ห้องสอบระบบเรียลไทม์"); st.info("กำลังรอสัญญาณเปิดระบบข้อสอบจากอาจารย์ผู้คุมสอบ..."); footer()

"""
MathComp — pages_admin.py
Admin panel: competition settings, members, analytics, student history
© Math Mission Thailand 2026
"""
from shared import *

def page_admin():
    require_auth(); require_admin(); inject_css()
    topbar("Admin Panel")

    tab1,tab2,tab3,tab4 = st.tabs([
        "⚙️  Competition Settings",
        "📥  Import Questions",
        "👥  Members",
        "🏆  Competitions",
    ])

    # ── Tab 1: Settings ────────────────────────
    with tab1:
        st.subheader("Competition Settings")
        competition = st.selectbox("Select competition to configure", list(get_all_competitions(include_disabled=True).keys()), key="adm_comp")
        settings    = load_settings(competition)
        st.divider()
        st.markdown("#### ⚙️  Behavior Settings")

        def brow(label,caption,key,sk):
            c1,c2=st.columns([3,1]); c1.markdown(f"**{label}**"); c1.caption(caption)
            settings[sk]=c2.toggle(f"##{key}",value=settings[sk],key=key)

        brow("Load questions from Firebase","On — Firebase · Off — local JSON fallback","s_lfb","load_from_firebase")
        brow("Load student list from Firebase","Pulls student names for dropdown","s_lsl","load_student_list")
        brow("Require Competitor ID verification","Forces ID entry before exam","s_rid","require_competitor_id")
        brow("Show answer after submit","Shows correct answer and solution after submission","s_sas","show_answer_after_submit")
        brow("Allow bilingual (TH/EN) toggle","Requires both EN and TH content","s_bil","allow_bilingual")

        st.markdown("**⏱  Per-question time limit (optional)**")
        c_tpq1, c_tpq2 = st.columns([3,1])
        c_tpq1.caption("Set a time limit per question in seconds. 0 = disabled (students can take as long as needed).")
        settings["time_per_question"] = c_tpq2.number_input(
            "Seconds per question", min_value=0, max_value=600,
            value=int(settings.get("time_per_question",0)), step=10, key="s_tpq")
        if settings["time_per_question"] > 0:
            st.caption(f"Each question auto-advances after **{settings['time_per_question']} seconds** ({settings['time_per_question']//60}m {settings['time_per_question']%60}s).")

        st.divider()
        ec = sum(1 for k in ["anti_copy_text","noise_canvas","block_ctrl_c","block_text_selection",
                              "block_paste_answer","block_drag","block_right_click","tab_switch_warning",
                              "block_printscreen","clipboard_api_override","devtools_detection","screen_capture_block"] if settings.get(k))
        st.markdown(f"#### 🛡️  Anti-AI Protection &nbsp;&nbsp; `{ec} / 12 layers enabled`")

        cl,cr = st.columns(2)
        def arow(col,label,caption,key,sk):
            c1,c2=col.columns([3,1]); c1.markdown(f"**{label}**"); c1.caption(caption)
            settings[sk]=c2.toggle(f"##{key}",value=settings[sk],key=key)

        with cl:
            st.markdown("**Content Protection**")
            arow(cl,"Anti-copy text rendering","Clipboard content becomes garbled when pasted into AI","s_act","anti_copy_text")
            arow(cl,"Noise canvas overlay","Degrades screenshot quality for OCR/AI","s_nc","noise_canvas")
            arow(cl,"Block Ctrl+C / V / X / A","Disables clipboard keyboard shortcuts","s_bcc","block_ctrl_c")
            arow(cl,"Block text selection (>10 chars)","Prevents select-all then copy","s_bts","block_text_selection")
            arow(cl,"Block paste in answer boxes","Students must type answers manually","s_bpa","block_paste_answer")
            arow(cl,"Block drag","Prevents dragging question images","s_bdg","block_drag")
        with cr:
            st.markdown("**Browser / System**")
            arow(cr,"Block right-click","Prevents Inspect, Save image, etc.","s_brc","block_right_click")
            arow(cr,"Tab / window switch warning","Warns when student leaves exam tab","s_tsw","tab_switch_warning")
            arow(cr,"Block PrintScreen","Intercepts PrintScreen key","s_bps","block_printscreen")
            arow(cr,"Clipboard API override","Stops AI extensions from reading clipboard","s_cao","clipboard_api_override")
            arow(cr,"DevTools detection","Detects open developer tools","s_dvd","devtools_detection")
            arow(cr,"Screen Capture API block","Blocks browser-based screen recording","s_scb","screen_capture_block")

        st.divider()
        if st.button("💾  Save settings", type="primary", use_container_width=True):
            save_settings(competition, settings)
            st.success(f"Settings saved for **{competition}**")

    # ── Tab 2: Import Questions ────────────────
    with tab2:
        st.subheader("Import Questions")
        st.caption("Add questions to the database using any of the 4 methods below.")

        method = st.radio("Import method",
            ["✏️  Type directly","🖼️  Upload image","🤖  AI-OCR from image","📄  PDF batch import"],
            horizontal=True, key="import_method")
        st.divider()

        # ── AI helpers ────────────────────────────
        API_KEY = st.secrets.get("ANTHROPIC_API_KEY","")
        AI_HEADERS = {
            "Content-Type":    "application/json",
            "x-api-key":       API_KEY,
            "anthropic-version":"2023-06-01",
        }

        def ai_call(messages:list, max_tokens:int=1500):
            """Make a Claude API call; return text or None."""
            if not API_KEY: return None
            try:
                resp = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=AI_HEADERS,
                    json={"model":"claude-sonnet-4-5","max_tokens":max_tokens,"messages":messages},
                    timeout=45,
                )
                if resp.ok: return resp.json()["content"][0]["text"].strip()
                st.warning(f"AI call failed: {resp.status_code}")
            except Exception as e:
                st.warning(f"AI error: {e}")
            return None

        def ai_assess_question(q_text:str="", img_b64:str="", img_mime:str="", competition:str="") -> dict:
            """Ask Claude to identify difficulty and topic for a question."""
            parts = []
            if img_b64: parts.append({"type":"image","source":{"type":"base64","media_type":img_mime,"data":img_b64}})
            if q_text:  parts.append({"type":"text","text":q_text})
            parts.append({"type":"text","text":
                f"""You are an expert mathematics competition coach.
Analyse this question for {competition or "a math competition"}.
Respond ONLY with a JSON object with exactly these fields:
{{
  "difficulty": "easy" | "intermediate" | "advanced",
  "topic": "Algebra" | "Number Theory" | "Geometry" | "Combinatorics" | "Word Problem" | "Other",
  "difficulty_reason": "one sentence",
  "topic_reason": "one sentence"
}}"""
            })
            raw = ai_call([{"role":"user","content":parts}], max_tokens=200)
            if raw:
                try:
                    return json.loads(raw.replace("```json","").replace("```","").strip())
                except: pass
            return {}

        def ai_full_extract(img_b64:str, img_mime:str, competition:str, answer_type:str) -> dict:
            """
            Full extraction from a question image:
            - question text (LaTeX)
            - multiple choice options (if present)
            - correct answer
            - topic + difficulty
            - worked solution
            Returns a dict with all fields.
            """
            n_choices = 4 if answer_type=="mc4" else (5 if answer_type=="mc5" else 0)
            choice_instruction = (
                f"Extract the {n_choices} multiple choice options labelled A–{chr(64+n_choices)} exactly as written."
                if n_choices > 0 else
                "There are no multiple choice options — the answer is a number."
            )
            prompt = f"""You are an expert mathematics competition coach for {competition or "math competitions"}.

Read this question image carefully and extract EVERYTHING.

{choice_instruction}

Respond ONLY with a valid JSON object (no markdown, no extra text):
{{
  "question_text": "full question in LaTeX — use $...$ inline, $$...$$ for display",
  "choices": ["choice A text", "choice B text", ...],
  "correct_answer": "A" or "B" ... or numeric string if no choices,
  "topic": "Algebra" | "Number Theory" | "Geometry" | "Combinatorics" | "Word Problem" | "Other",
  "difficulty": "easy" | "intermediate" | "advanced",
  "difficulty_reason": "one sentence",
  "topic_reason": "one sentence",
  "solution_text": "full worked solution in LaTeX — step by step, show all working"
}}

Rules:
- Use LaTeX for ALL mathematical expressions
- For choices: include ONLY the text/expression, NOT the letter label
- solution_text must be a complete worked solution showing every step
- If the image is unclear about any field, make your best educated guess"""

            raw = ai_call([{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":img_mime,"data":img_b64}},
                {"type":"text","text":prompt}
            ]}], max_tokens=2000)

            if raw:
                try:
                    return json.loads(raw.replace("```json","").replace("```","").strip())
                except Exception as e:
                    st.warning(f"Could not parse AI response: {e}")
                    # Return partial result with raw text
                    return {"question_text": raw, "choices":[], "correct_answer":"",
                            "topic":"Other","difficulty":"intermediate","solution_text":""}
            return {}

        def ai_generate_solution(q_text:str, choices:list, correct:str, competition:str):
            """Generate a worked solution for a typed/existing question."""
            choices_str = ""
            if choices:
                labels = [chr(65+i) for i in range(len(choices))]
                choices_str = "\n".join(f"{labels[i]}. {choices[i]}" for i in range(len(choices)))
                choices_str = f"\n\nAnswer choices:\n{choices_str}\n\nCorrect answer: {correct}"
            prompt = f"""You are an expert mathematics competition coach.

Write a complete, step-by-step worked solution for this competition mathematics question.
Use LaTeX for all mathematical expressions ($...$ inline, $$...$$ display).
Show every step clearly. Competition: {competition or "math competition"}.

Question:
{q_text}{choices_str}

Provide a thorough solution that a student can learn from."""

            return ai_call([{"role":"user","content":prompt}], max_tokens=1500) or ""

        def meta_fields(p="", q_text_for_ai="", img_b64_for_ai="", img_mime_for_ai=""):
            c1,c2 = st.columns(2)
            comp  = c1.selectbox("Competition",list(get_all_competitions(include_disabled=True).keys()),key=f"{p}comp")
            level = c2.selectbox("Level",get_all_competitions().get(comp,{}).get("levels",["General"]),key=f"{p}level")

            # AI assess button
            ai_result = st.session_state.get(f"{p}ai_assess",{})
            ai_col1, ai_col2 = st.columns([3,1])
            with ai_col2:
                if st.button("🤖 AI assess difficulty & topic", key=f"{p}ai_btn", use_container_width=True):
                    with st.spinner("Claude is analysing the question…"):
                        result = ai_assess_question(q_text_for_ai, img_b64_for_ai, img_mime_for_ai, comp)
                        if result:
                            st.session_state[f"{p}ai_assess"] = result
                            st.rerun()
                        else:
                            st.warning("AI assessment unavailable — fill in manually.")
            with ai_col1:
                if ai_result:
                    st.markdown(
                        f"<div style='background:#EEF3FF;border:1px solid #C8D8FF;border-radius:8px;"
                        f"padding:8px 14px;font-size:13px;'>"
                        f"🤖 AI suggests: <strong>Topic — {ai_result.get('topic','?')}</strong> · "
                        f"<strong>Difficulty — {ai_result.get('difficulty','?')}</strong><br>"
                        f"<span style='color:#8898CC;font-size:11px;'>{ai_result.get('topic_reason','')} "
                        f"· {ai_result.get('difficulty_reason','')}</span></div>",
                        unsafe_allow_html=True)

            c3,c4,c5,c6 = st.columns(4)
            # Use AI suggestion as default if available
            ai_topic = ai_result.get("topic","Algebra")
            ai_diff  = ai_result.get("difficulty","easy")
            topic_opts = TOPICS+["Other"]
            diff_opts  = ["easy","intermediate","advanced"]
            t_idx = topic_opts.index(ai_topic) if ai_topic in topic_opts else 0
            d_idx = diff_opts.index(ai_diff)   if ai_diff  in diff_opts  else 0

            topic = c3.selectbox("Topic",    topic_opts, index=t_idx, key=f"{p}topic")
            diff  = c4.selectbox("Difficulty",diff_opts, index=d_idx, key=f"{p}diff")
            year  = c5.number_input("Year",2000,2030,datetime.now().year,key=f"{p}year")
            atype = c6.selectbox("Answer type",["mc4","mc5","integer","decimal"],key=f"{p}atype")
            return comp,level,topic,diff,int(year),atype

        def ans_fields(atype,p=""):
            choices=[]
            if atype in ("mc4","mc5"):
                n=4 if atype=="mc4" else 5
                st.markdown("**Answer choices**")
                cols=st.columns(n)
                for i in range(n): choices.append(cols[i].text_input(chr(65+i),key=f"{p}ch{i}"))
                correct=st.selectbox("Correct answer",[chr(65+i) for i in range(n)],key=f"{p}correct")
            else:
                correct=st.text_input("Correct answer (number)",key=f"{p}correct")
            return choices,correct

        def sol_fields(p=""):
            st.markdown("**Solution (optional)**")
            st_text=st.text_area("Solution text / LaTeX",height=100,key=f"{p}sol_text")
            st_img =st.file_uploader("Solution image",type=["png","jpg","jpeg"],key=f"{p}sol_img")
            return st_text,st_img

        # Method 1 — Type
        if method == "✏️  Type directly":
            st.markdown("#### Type question with LaTeX support")
            st.caption("Use `$...$` for inline math and `$$...$$` for display math.")
            q_text_pre = st.session_state.get('t_qtext','')
            comp,level,topic,diff,year,atype = meta_fields("t_",q_text_for_ai=q_text_pre)
            q_text = st.text_area("Question text (LaTeX supported)", height=120, key="t_qtext")
            q_img  = st.file_uploader("Question figure (optional)", type=["png","jpg","jpeg"], key="t_qimg")
            if q_text:
                with st.expander("Preview"): st.markdown(q_text)
            choices,correct = ans_fields(atype,"t_")

            # AI generate solution
            st.markdown("**Solution**")
            sc1,sc2 = st.columns([3,1])
            t_sol = sc1.text_area("Solution text / LaTeX (optional)", height=100, key="t_sol_text")
            t_sol_img = sc2.file_uploader("Solution image", type=["png","jpg","jpeg"], key="t_sol_img")
            if q_text and st.button("🤖  AI generate solution", key="t_gen_sol"):
                with st.spinner("Claude is writing a solution…"):
                    ch_list = [st.session_state.get(f"t_ch{i}","") for i in range(4 if atype=="mc4" else 5)] if atype in ("mc4","mc5") else []
                    sol_generated = ai_generate_solution(q_text, ch_list, st.session_state.get("t_correct",""), comp)
                    if sol_generated:
                        st.session_state["t_sol_generated"] = sol_generated
                        st.rerun()
            if st.session_state.get("t_sol_generated") and not t_sol:
                t_sol = st.session_state["t_sol_generated"]
                st.markdown("**Generated solution preview:**")
                st.markdown(t_sol)

            if st.button("💾  Save question", type="primary", key="t_save"):
                if not q_text: st.error("Question text is required.")
                else:
                    with st.spinner("Saving…"):
                        q_url = upload_img(q_img,f"questions/{datetime.now().timestamp()}_q.{q_img.name.split('.')[-1]}") if q_img else ""
                        s_url = upload_img(sol_img,f"solutions/{datetime.now().timestamp()}_s.{sol_img.name.split('.')[-1]}") if sol_img else ""
                        final_sol = t_sol or st.session_state.pop("t_sol_generated","")  
                        save_question({"competition":comp,"level":level,"topic":topic,"difficulty":diff,"year":year,
                                       "answer_type":atype,"question_text":q_text,"question_image_url":q_url,
                                       "choices":choices,"correct_answer":correct,"solution_text":final_sol,"solution_image_url":s_url})
                    st.success("✅  Question saved!")

        # Method 2 — Image
        elif method == "🖼️  Upload image":
            st.markdown("#### Upload question as image")
            comp,level,topic,diff,year,atype = meta_fields("i_")
            q_img = st.file_uploader("Question image", type=["png","jpg","jpeg"], key="i_qimg")
            if q_img: st.image(q_img, caption="Preview", use_container_width=True)
            choices,correct = ans_fields(atype,"i_")
            sol_text,sol_img = sol_fields("i_")
            if st.button("💾  Save question", type="primary", key="i_save"):
                if not q_img: st.error("Please upload an image.")
                else:
                    with st.spinner("Uploading…"):
                        q_url = upload_img(q_img,f"questions/{datetime.now().timestamp()}_q.{q_img.name.split('.')[-1]}")
                        s_url = upload_img(sol_img,f"solutions/{datetime.now().timestamp()}_s.{sol_img.name.split('.')[-1]}") if sol_img else ""
                        save_question({"competition":comp,"level":level,"topic":topic,"difficulty":diff,"year":year,
                                       "answer_type":atype,"question_text":"","question_image_url":q_url,
                                       "choices":choices,"correct_answer":correct,"solution_text":sol_text,"solution_image_url":s_url})
                    st.success("✅  Question saved!")

        # Method 3 — AI-OCR (full extract: question + choices + solution)
        elif method == "🤖  AI-OCR from image":
            st.markdown("#### AI reads image — extracts question, choices, correct answer & solution")
            st.caption("Claude reads the full image and fills in all fields automatically. Review and edit before saving.")

            comp,level,topic,diff,year,atype = meta_fields("ai_")

            q_img = st.file_uploader("Question image", type=["png","jpg","jpeg"], key="ai_qimg")

            # ── Clear stale results when a new image is uploaded ──
            if q_img:
                # Track filename+size to detect a new upload
                img_sig = f"{q_img.name}_{q_img.size}"
                if st.session_state.get("ai_img_sig") != img_sig:
                    # New image — clear all previous extraction results
                    for k in ("ai_full","ai_ocr_result","ai_topic_override",
                              "ai_diff_override","ai_img_sig"):
                        st.session_state.pop(k, None)
                    st.session_state["ai_img_sig"] = img_sig
                st.image(q_img, caption=f"Uploaded: {q_img.name}", use_container_width=True)
            else:
                # No image — also clear stale data
                for k in ("ai_full","ai_ocr_result","ai_topic_override",
                          "ai_diff_override","ai_img_sig"):
                    st.session_state.pop(k, None)

            if q_img and st.button("🤖  Full AI Extract (question + choices + solution)", type="primary", key="ai_ocr"):
                with st.spinner("Claude is reading the image — extracting everything…"):
                    try:
                        q_img.seek(0)
                        img_b64 = base64.b64encode(q_img.read()).decode()
                        ext  = q_img.name.split(".")[-1].lower()
                        mime = "image/jpeg" if ext in ("jpg","jpeg") else f"image/{ext}"
                        result = ai_full_extract(img_b64, mime, comp, atype)
                        if result:
                            st.session_state["ai_full"] = result
                            st.success("✅  Extraction complete — review fields below and edit if needed.")
                            st.rerun()
                        else:
                            st.error("Extraction failed. Check your ANTHROPIC_API_KEY.")
                    except Exception as e:
                        st.error(f"Error: {e}")

            # Pull extracted values (or empty defaults)
            extracted = st.session_state.get("ai_full", {})
            if extracted:
                st.markdown("""
                <div style='background:#EEF3FF;border:1.5px solid #C8D8FF;border-radius:10px;
                            padding:12px 16px;margin-bottom:12px;font-size:13px;color:#1B2B6B;'>
                🤖 <strong>AI extracted all fields below.</strong>
                Review each field carefully — edit anything that needs correction before saving.
                </div>""", unsafe_allow_html=True)

            # ── Editable fields pre-filled by AI ──
            q_text = st.text_area(
                "Question text (LaTeX)",
                value=extracted.get("question_text", st.session_state.get("ai_ocr_result","")),
                height=140, key="ai_qtext")
            if q_text:
                with st.expander("Preview question"): st.markdown(q_text)

            # Override topic/diff from AI extraction
            if extracted.get("topic") and extracted["topic"] in TOPICS+["Other"]:
                st.session_state["ai_topic_override"] = extracted["topic"]
            if extracted.get("difficulty") and extracted["difficulty"] in ["easy","intermediate","advanced"]:
                st.session_state["ai_diff_override"] = extracted["difficulty"]

            topic_opts = TOPICS+["Other"]
            diff_opts  = ["easy","intermediate","advanced"]
            ov_topic = st.session_state.get("ai_topic_override", extracted.get("topic","Algebra"))
            ov_diff  = st.session_state.get("ai_diff_override",  extracted.get("difficulty","intermediate"))
            ti = topic_opts.index(ov_topic) if ov_topic in topic_opts else 0
            di = diff_opts.index(ov_diff)   if ov_diff  in diff_opts  else 1

            tc1,tc2 = st.columns(2)
            topic_final = tc1.selectbox("Topic",    topic_opts, index=ti, key="ai_topic_sel")
            diff_final  = tc2.selectbox("Difficulty",diff_opts, index=di, key="ai_diff_sel")
            if extracted.get("topic_reason") or extracted.get("difficulty_reason"):
                st.caption(f"🤖 {extracted.get('topic_reason','')} · {extracted.get('difficulty_reason','')}")

            # ── Answer choices from AI ──
            ai_choices  = extracted.get("choices", [])
            ai_correct  = str(extracted.get("correct_answer",""))
            choices, correct = [], ""

            if atype in ("mc4","mc5"):
                n = 4 if atype=="mc4" else 5
                st.markdown("**Answer choices** (AI-filled — edit if needed)")
                ch_cols = st.columns(n)
                for i in range(n):
                    pre = ai_choices[i] if i < len(ai_choices) else ""
                    choices.append(ch_cols[i].text_input(chr(65+i), value=pre, key=f"ai_ch{i}"))
                labels = [chr(65+i) for i in range(n)]
                idx_c = labels.index(ai_correct.upper()) if ai_correct.upper() in labels else 0
                correct = st.selectbox("Correct answer", labels, index=idx_c, key="ai_correct_mc")
            else:
                correct = st.text_input("Correct answer (number)", value=ai_correct, key="ai_correct_num")

            # ── Solution from AI ──
            st.markdown("**Solution** (AI-generated — edit if needed)")
            sol_text = st.text_area(
                "Solution text (LaTeX)",
                value=extracted.get("solution_text",""),
                height=180, key="ai_sol_text")
            if sol_text:
                with st.expander("Preview solution"): st.markdown(sol_text)
            sol_img = st.file_uploader("Solution image (optional)", type=["png","jpg","jpeg"], key="ai_sol_img")

            # ── Generate solution separately if needed ──
            if q_text and st.button("🔄  Re-generate solution only", key="ai_regen_sol"):
                with st.spinner("Claude is writing a solution…"):
                    new_sol = ai_generate_solution(q_text, choices, correct, comp)
                    if new_sol:
                        extracted["solution_text"] = new_sol
                        st.session_state["ai_full"] = extracted
                        st.rerun()

            if st.button("💾  Save question", type="primary", key="ai_save"):
                if not q_text: st.error("Question text is required.")
                else:
                    with st.spinner("Saving…"):
                        ts = datetime.now().timestamp()
                        if q_img: q_img.seek(0)
                        q_url   = upload_img(q_img,     f"questions/{ts}_q.{q_img.name.split('.')[-1]}")     if q_img     else ""
                        s_url   = upload_img(sol_img,   f"solutions/{ts}_s.{sol_img.name.split('.')[-1]}")   if sol_img   else ""
                        save_question({
                            "competition":        comp,   "level":     level,
                            "topic":              topic_final,           "difficulty": diff_final,
                            "year":               year,   "answer_type":atype,
                            "question_text":      q_text, "question_image_url": q_url,
                            "choices":            choices,"correct_answer":     str(correct),
                            "solution_text":      sol_text,"solution_image_url":s_url,
                        })
                        for k in ("ai_ocr_result","ai_full","ai_topic_override","ai_diff_override"):
                            st.session_state.pop(k,None)
                    st.success("✅  Question saved!")

        # Method 4 — PDF batch
        elif method == "📄  PDF batch import":
            st.markdown("#### PDF → AI segments each question")
            comp   = st.selectbox("Competition",list(COMPETITIONS.keys()),key="pdf_comp")
            level  = st.selectbox("Level",COMPETITIONS[comp]["levels"],key="pdf_level")
            c1,c2  = st.columns(2)
            diff   = c1.selectbox("Difficulty (all)",["easy","intermediate","advanced"],key="pdf_diff")
            year   = c2.number_input("Year",2000,2030,datetime.now().year,key="pdf_year")
            atype  = st.selectbox("Answer type (all)",["mc5","mc4","integer","decimal"],key="pdf_atype")
            pdf_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_upload")

            # Clear stale results when a new PDF is uploaded
            if pdf_file:
                pdf_sig = f"{pdf_file.name}_{pdf_file.size}"
                if st.session_state.get("pdf_sig") != pdf_sig:
                    st.session_state.pop("pdf_questions", None)
                    st.session_state["pdf_sig"] = pdf_sig
            else:
                st.session_state.pop("pdf_questions", None)
                st.session_state.pop("pdf_sig", None)

            if pdf_file and st.button("🤖  Extract questions from PDF", key="pdf_extract", type="primary"):
                with st.spinner("Claude is reading the PDF — extracting questions, choices, answers and solutions…"):
                    try:
                        pdf_b64 = base64.b64encode(pdf_file.read()).decode()
                        n_choices_info = (
                            f"Each question has {4 if atype=='mc4' else 5} multiple choice options labelled A–{'D' if atype=='mc4' else 'E'}."
                            if atype in ("mc4","mc5") else
                            "Questions have numeric answers (no multiple choice)."
                        )
                        pdf_prompt = f"""You are an expert mathematics competition coach.

Extract ALL mathematics questions from this PDF for {comp} competition.
{n_choices_info}

For EACH question, provide:
1. The full question text in LaTeX
2. All answer choices exactly as written (if multiple choice)
3. The correct answer (letter A-E or numeric)
4. Topic classification
5. Difficulty assessment
6. A complete step-by-step worked solution in LaTeX

Return ONLY a valid JSON array. Each element must have exactly these fields:
{{
  "question_text": "full question in LaTeX ($...$ inline, $$...$$ display)",
  "choices": ["option A", "option B", ...],
  "correct_answer": "A" or numeric string,
  "topic": "Algebra" | "Number Theory" | "Geometry" | "Combinatorics" | "Word Problem" | "Other",
  "difficulty": "easy" | "intermediate" | "advanced",
  "solution_text": "complete worked solution in LaTeX"
}}

No markdown, no explanation — ONLY the JSON array."""

                        raw = ai_call([{"role":"user","content":[
                            {"type":"document","source":{"type":"base64","media_type":"application/pdf","data":pdf_b64}},
                            {"type":"text","text":pdf_prompt}
                        ]}], max_tokens=6000)

                        if raw:
                            clean = raw.replace("```json","").replace("```","").strip()
                            qs_extracted = json.loads(clean)
                            st.session_state["pdf_questions"] = qs_extracted
                            n_with_sol = sum(1 for q in qs_extracted if q.get("solution_text","").strip())
                            st.success(f"✅  Extracted **{len(qs_extracted)}** questions — "
                                       f"{n_with_sol} with solutions, "
                                       f"{sum(1 for q in qs_extracted if q.get('choices'))} with choices.")
                        else:
                            st.error("Extraction failed. Check your ANTHROPIC_API_KEY.")
                    except json.JSONDecodeError as e:
                        st.error(f"JSON parse error: {e}. Try again — Claude sometimes adds extra text.")
                    except Exception as e:
                        st.error(f"Error: {e}")

            if "pdf_questions" in st.session_state:
                pdf_qs = st.session_state["pdf_questions"]
                st.markdown(f"**{len(pdf_qs)} questions extracted — review each one:**")

                for i,q in enumerate(pdf_qs):
                    qt_preview = q.get("question_text","")[:55]
                    sol_icon   = "✅" if q.get("solution_text","").strip() else "⚠️"
                    ch_icon    = f"🔤{len(q.get('choices',[]))}" if q.get("choices") else "🔢"
                    with st.expander(
                        f"Q{i+1} {ch_icon} [{q.get('difficulty','?')}] [{q.get('topic','?')}] {sol_icon} — {qt_preview}…"
                    ):
                        # Question text
                        pdf_qs[i]["question_text"] = st.text_area(
                            "Question text (LaTeX)", value=q.get("question_text",""),
                            height=100, key=f"pdf_qt_{i}")
                        with st.expander("Preview question"):
                            st.markdown(pdf_qs[i]["question_text"])

                        # Topic + difficulty
                        pc1,pc2 = st.columns(2)
                        t_opts = TOPICS+["Other"]
                        d_opts = ["easy","intermediate","advanced"]
                        pdf_qs[i]["topic"] = pc1.selectbox("Topic", t_opts,
                            index=t_opts.index(q.get("topic","Other")) if q.get("topic") in t_opts else 0,
                            key=f"pdf_tp_{i}")
                        pdf_qs[i]["difficulty"] = pc2.selectbox("Difficulty", d_opts,
                            index=d_opts.index(q.get("difficulty","intermediate")) if q.get("difficulty") in d_opts else 1,
                            key=f"pdf_df_{i}")

                        # Choices
                        if atype in ("mc4","mc5"):
                            n = 4 if atype=="mc4" else 5
                            existing = q.get("choices",[""]*n)
                            st.markdown("**Answer choices**")
                            cols = st.columns(n); new_ch = []
                            for j in range(n):
                                new_ch.append(cols[j].text_input(
                                    chr(65+j),
                                    value=existing[j] if j < len(existing) else "",
                                    key=f"pdf_ch_{i}_{j}"))
                            pdf_qs[i]["choices"] = new_ch
                            labels = [chr(65+j) for j in range(n)]
                            ca = str(q.get("correct_answer","A")).upper()
                            pdf_qs[i]["correct_answer"] = st.selectbox(
                                "Correct answer", labels,
                                index=labels.index(ca) if ca in labels else 0,
                                key=f"pdf_ca_{i}")
                        else:
                            pdf_qs[i]["correct_answer"] = st.text_input(
                                "Correct answer", value=str(q.get("correct_answer","")),
                                key=f"pdf_ca_{i}")

                        # Solution
                        st.markdown("**Solution** (AI-generated)")
                        pdf_qs[i]["solution_text"] = st.text_area(
                            "Solution (LaTeX)", value=q.get("solution_text",""),
                            height=150, key=f"pdf_sol_{i}")
                        if pdf_qs[i]["solution_text"]:
                            with st.expander("Preview solution"):
                                st.markdown(pdf_qs[i]["solution_text"])

                        # Re-generate solution for this question
                        if st.button(f"🔄  Re-generate solution for Q{i+1}", key=f"pdf_regen_{i}"):
                            with st.spinner("Generating solution…"):
                                new_sol = ai_generate_solution(
                                    pdf_qs[i]["question_text"],
                                    pdf_qs[i].get("choices",[]),
                                    str(pdf_qs[i].get("correct_answer","")),
                                    comp
                                )
                                if new_sol:
                                    pdf_qs[i]["solution_text"] = new_sol
                                    st.session_state["pdf_questions"] = pdf_qs
                                    st.rerun()

                st.session_state["pdf_questions"] = pdf_qs
                st.divider()

                # Summary before saving
                n_sol = sum(1 for q in pdf_qs if q.get("solution_text","").strip())
                n_ch  = sum(1 for q in pdf_qs if q.get("choices"))
                st.info(f"📊  Ready to save: **{len(pdf_qs)}** questions · "
                        f"**{n_ch}** with choices · **{n_sol}** with solutions")

                if st.button(f"💾  Save all {len(pdf_qs)} questions to Firestore",
                             type="primary", key="pdf_save"):
                    with st.spinner(f"Saving {len(pdf_qs)} questions…"):
                        for q in pdf_qs:
                            save_question({
                                "competition":   comp,   "level":      level,
                                "topic":         q.get("topic","Other"),
                                "difficulty":    q.get("difficulty",diff),
                                "year":          int(year), "answer_type": atype,
                                "question_text": q.get("question_text",""),
                                "question_image_url": "",
                                "choices":       q.get("choices",[]),
                                "correct_answer":str(q.get("correct_answer","")),
                                "solution_text": q.get("solution_text",""),
                                "solution_image_url": "",
                            })
                    st.session_state.pop("pdf_questions",None)
                    st.success(f"✅  {len(pdf_qs)} questions saved to Firestore!")

        # ── Question Bank Browser (Editable) ───────
        st.divider()
        st.markdown("#### 📚  Question Bank — Browse & Edit")
        f1,f2,f3 = st.columns(3)
        qb_comp  = f1.selectbox("Filter competition", ["All"]+list(COMPETITIONS.keys()), key="qb_comp")
        qb_topic = f2.selectbox("Filter topic",       ["All"]+TOPICS+["Other"],          key="qb_topic")
        qb_diff  = f3.selectbox("Filter difficulty",  ["All","easy","intermediate","advanced"], key="qb_diff")

        if st.button("🔍  Browse questions", key="qb_browse", type="primary"):
            try:
                ref = db.collection("questions")
                if qb_comp  != "All": ref = ref.where("competition","==",qb_comp)
                if qb_topic != "All": ref = ref.where("topic","==",qb_topic)
                if qb_diff  != "All": ref = ref.where("difficulty","==",qb_diff)
                docs = list(ref.limit(100).stream())
                st.session_state["qb_docs"] = [(doc.id, doc.to_dict()) for doc in docs]
            except Exception as e:
                st.error(f"Error: {e}")

        qb_docs = st.session_state.get("qb_docs", [])
        if qb_docs:
            st.caption(f"**{len(qb_docs)} questions found** (max 100) — expand any to edit and save")
            for doc_id, d in qb_docs:
                qt  = d.get("question_text","(image only)")[:70]
                hdr = (f"[{d.get('competition','')}] "
                       f"[{d.get('level','')}] "
                       f"[{d.get('difficulty','')}] "
                       f"[{d.get('topic','')}] — {qt}…")
                with st.expander(hdr):
                    # ── Preview ──────────────────────────────
                    if d.get("question_image_url"):
                        st.image(d["question_image_url"], use_container_width=True)

                    ec1, ec2 = st.columns(2)
                    # ── Editable fields ───────────────────────
                    new_comp  = ec1.selectbox("Competition", list(COMPETITIONS.keys()),
                        index=list(COMPETITIONS.keys()).index(d.get("competition","AMC 8"))
                              if d.get("competition") in COMPETITIONS else 0,
                        key=f"e_comp_{doc_id}")
                    new_level = ec2.selectbox("Level", COMPETITIONS[new_comp]["levels"],
                        index=COMPETITIONS[new_comp]["levels"].index(d.get("level",""))
                              if d.get("level","") in COMPETITIONS[new_comp]["levels"] else 0,
                        key=f"e_level_{doc_id}")

                    ec3,ec4,ec5,ec6 = st.columns(4)
                    topic_opts = TOPICS+["Other"]
                    diff_opts  = ["easy","intermediate","advanced"]
                    new_topic = ec3.selectbox("Topic", topic_opts,
                        index=topic_opts.index(d.get("topic","Other"))
                              if d.get("topic") in topic_opts else 0,
                        key=f"e_topic_{doc_id}")
                    new_diff  = ec4.selectbox("Difficulty", diff_opts,
                        index=diff_opts.index(d.get("difficulty","easy"))
                              if d.get("difficulty") in diff_opts else 0,
                        key=f"e_diff_{doc_id}")
                    new_year  = ec5.number_input("Year", 2000, 2030,
                        value=int(d.get("year", datetime.now().year)),
                        key=f"e_year_{doc_id}")
                    atype_opts = ["mc4","mc5","integer","decimal"]
                    new_atype = ec6.selectbox("Answer type", atype_opts,
                        index=atype_opts.index(d.get("answer_type","mc4"))
                              if d.get("answer_type") in atype_opts else 0,
                        key=f"e_atype_{doc_id}")

                    new_qtext = st.text_area("Question text (LaTeX)",
                        value=d.get("question_text",""), height=100,
                        key=f"e_qtext_{doc_id}")

                    # Choices
                    new_choices = d.get("choices",[])
                    new_correct = d.get("correct_answer","")
                    if new_atype in ("mc4","mc5"):
                        n = 4 if new_atype=="mc4" else 5
                        st.markdown("**Answer choices**")
                        ch_cols = st.columns(n)
                        new_choices = []
                        for i in range(n):
                            existing_val = d.get("choices",[""]*(n))[i] if i < len(d.get("choices",[])) else ""
                            new_choices.append(ch_cols[i].text_input(
                                chr(65+i), value=existing_val, key=f"e_ch_{doc_id}_{i}"))
                        new_correct = st.selectbox("Correct answer",
                            [chr(65+i) for i in range(n)],
                            index=[chr(65+i) for i in range(n)].index(d.get("correct_answer","A"))
                                  if d.get("correct_answer","A") in [chr(65+i) for i in range(n)] else 0,
                            key=f"e_correct_{doc_id}")
                    else:
                        new_correct = st.text_input("Correct answer",
                            value=str(d.get("correct_answer","")),
                            key=f"e_correct_{doc_id}")

                    st.markdown("**Solution**")
                    esl1, esl2 = st.columns(2)
                    new_sol = esl1.text_area("Solution text / LaTeX",
                        value=d.get("solution_text",""), height=80,
                        key=f"e_sol_{doc_id}")
                    new_sol_img_file = esl2.file_uploader(
                        "Replace solution image",
                        type=["png","jpg","jpeg"], key=f"e_sol_img_{doc_id}")
                    if d.get("solution_image_url") and not new_sol_img_file:
                        st.image(d["solution_image_url"], caption="Current solution image", width=200)
                    elif new_sol_img_file:
                        st.image(new_sol_img_file, caption="New solution image preview", width=200)

                    # ── AI re-assess button ───────────────────
                    ai_key = f"e_ai_{doc_id}"
                    if st.button("🤖  AI re-assess difficulty & topic", key=f"e_ai_btn_{doc_id}"):
                        with st.spinner("Claude is re-analysing…"):
                            ai_r = ai_assess_question(new_qtext, "", "", new_comp)
                            if ai_r:
                                st.session_state[ai_key] = ai_r
                                st.rerun()
                    if ai_key in st.session_state:
                        ar = st.session_state[ai_key]
                        st.info(
                            f"🤖 AI suggests — **Topic: {ar.get('topic','?')}** · "
                            f"**Difficulty: {ar.get('difficulty','?')}** · "
                            f"{ar.get('topic_reason','')} · {ar.get('difficulty_reason','')}"
                        )

                    # ── Save / Delete buttons ─────────────────
                    sb1, sb2 = st.columns(2)
                    if sb1.button("💾  Save changes", type="primary",
                                  key=f"save_{doc_id}", use_container_width=True):
                        # Use AI suggestion if available
                        ar = st.session_state.get(ai_key, {})
                        final_topic = ar.get("topic", new_topic) if ar else new_topic
                        final_diff  = ar.get("difficulty", new_diff) if ar else new_diff
                        ts_now = datetime.now().timestamp()
                        new_sol_url = d.get("solution_image_url","")
                        if new_sol_img_file:
                            new_sol_url = upload_img(
                                new_sol_img_file,
                                f"solutions/{ts_now}_s.{new_sol_img_file.name.split('.')[-1]}"
                            )
                        updates = {
                            "competition":        new_comp,
                            "level":              new_level,
                            "topic":              final_topic,
                            "difficulty":         final_diff,
                            "year":               int(new_year),
                            "answer_type":        new_atype,
                            "question_text":      new_qtext,
                            "choices":            new_choices,
                            "correct_answer":     str(new_correct),
                            "solution_text":      new_sol,
                            "solution_image_url": new_sol_url,
                        }
                        db.collection("questions").document(doc_id).update(updates)
                        # Refresh cache
                        idx = next((i for i,(did,_) in enumerate(qb_docs) if did==doc_id), None)
                        if idx is not None:
                            st.session_state["qb_docs"][idx] = (doc_id, {**d, **updates})
                        st.success("✅  Question updated!")
                        st.rerun()

                    if sb2.button("🗑️  Delete", key=f"del_{doc_id}", use_container_width=True):
                        db.collection("questions").document(doc_id).delete()
                        st.session_state["qb_docs"] = [(did,dd) for did,dd in qb_docs if did!=doc_id]
                        st.warning("Question deleted.")
                        st.rerun()
        elif "qb_docs" in st.session_state:
            st.info("No questions found for this filter.")

    # ── Tab 3: Members ─────────────────────────
    with tab3:
        st.subheader("Member Management")
        mem1,mem2,mem_csv,mem3 = st.tabs(["👥  All Members","➕  Add Member","📤  Bulk CSV Upload","📊  Export"])

        with mem1:
            if st.button("🔄  Load members", key="load_members"):
                try: st.session_state["members"]=[{"uid":d.id,**d.to_dict()} for d in db.collection("users").stream()]
                except Exception as e: st.error(f"Error: {e}")
            members = st.session_state.get("members",[])
            if members:
                search = st.text_input("Search name or email",key="mem_search")
                filtered = [m for m in members if search.lower() in m.get("display_name","").lower() or search.lower() in m.get("email","").lower()] if search else members
                st.caption(f"{len(filtered)} members")
                for m in filtered:
                    c1,c2,c3,c4,c5 = st.columns([3,3,1,1,1])
                    c1.markdown(f"**{m.get('display_name','—')}**")
                    c2.caption(m.get("email","—"))
                    c3.caption(m.get("role","student"))
                    try: c4.caption(f"{len(list(db.collection('users').document(m['uid']).collection('exam_sessions').limit(99).stream()))} sessions")
                    except: c4.caption("—")
                    new_role = "admin" if m.get("role")=="student" else "student"
                    if c5.button(f"→ {new_role}",key=f"role_{m['uid']}"):
                        db.collection("users").document(m["uid"]).update({"role":new_role}); st.rerun()
            else: st.info("Click 'Load members' to view all users.")

        with mem2:
            st.markdown("#### Create new member account")
            with st.form("add_member"):
                c1,c2 = st.columns(2)
                nm = c1.text_input("Display name"); ne = c2.text_input("Email")
                c3,c4 = st.columns(2)
                np = c3.text_input("Password",type="password"); nr = c4.selectbox("Role",["student","admin"])
                sub_add = st.form_submit_button("Create account",type="primary",use_container_width=True)
            # Email settings for Add Member
            with st.expander("⚙️  Email notification settings"):
                send_email_toggle = st.toggle("Send welcome email to new member", value=True, key="add_send_email")
                app_url_add = st.text_input("App URL (for login link in email)",
                    value=st.secrets.get("APP_URL","https://share.streamlit.io"),
                    key="add_app_url")

            if sub_add:
                if not nm or not ne or not np: st.error("All fields required.")
                else:
                    try:
                        from firebase_admin import auth as fb_auth
                        user = fb_auth.create_user(email=ne, password=np, display_name=nm)
                        db.collection("users").document(user.uid).set({
                            "display_name":nm,"email":ne,"role":nr,
                            "created_at":datetime.now(timezone.utc)
                        })
                        st.success(f"✅  Account created for **{nm}** ({ne}) as **{nr}**")

                        # Send welcome email
                        if send_email_toggle:
                            with st.spinner(f"Sending welcome email to {ne}…"):
                                ok, msg = send_welcome_email(ne, nm, np, nr, app_url_add)
                            if ok:
                                st.success(f"📧  Welcome email sent to **{ne}**")
                            else:
                                st.warning(f"⚠️  Account created but email failed: {msg}")
                    except Exception as e: st.error(f"Error: {e}")

        with mem_csv:
            st.markdown("#### Bulk create accounts from CSV")
            st.caption("Upload a CSV file with columns: **display_name, email, password, role**")
            st.markdown("""
**CSV format example:**
```
display_name,email,password,role
Napat Suwan,napat@example.com,Pass1234!,student
Mint Charoenpol,mint@example.com,Pass5678!,student
Admin2,admin2@example.com,AdminPass!,admin
```
""")
            csv_template = "display_name,email,password,role\nNapat Suwan,napat@example.com,Pass1234!,student\nMint Charoenpol,mint@example.com,Pass5678!,student"
            st.download_button("⬇️  Download CSV template", csv_template.encode(), "members_template.csv", "text/csv")
            st.divider()
            csv_file = st.file_uploader("Upload members CSV", type=["csv"], key="bulk_csv")
            if csv_file:
                import io as _io
                import csv as _csv
                rows = list(_csv.DictReader(_io.StringIO(csv_file.read().decode("utf-8-sig"))))
                st.markdown(f"**{len(rows)} accounts found in CSV — preview:**")
                for i,r in enumerate(rows[:5]):
                    st.markdown(f"`{r.get('display_name','?')}` · `{r.get('email','?')}` · role: `{r.get('role','student')}`")
                if len(rows) > 5: st.caption(f"… and {len(rows)-5} more")
                st.divider()
                with st.expander("⚙️  Email notification settings"):
                    bulk_send_email = st.toggle("Send welcome email to each member", value=True, key="bulk_send_email")
                    bulk_app_url    = st.text_input("App URL (for login link in email)",
                        value=st.secrets.get("APP_URL","https://share.streamlit.io"),
                        key="bulk_app_url")
                    if bulk_send_email:
                        st.info("📧  Each member will receive a welcome email with their login credentials.")

                if st.button(f"🚀  Create {len(rows)} accounts", type="primary", key="bulk_create"):
                    from firebase_admin import auth as _fb_auth
                    success, failed = 0, []
                    prog = st.progress(0, text="Creating accounts…")
                    for i,r in enumerate(rows):
                        name  = r.get("display_name","").strip()
                        email = r.get("email","").strip()
                        pwd   = r.get("password","").strip()
                        role  = r.get("role","student").strip().lower()
                        if not name or not email or not pwd:
                            failed.append(f"{email} — missing fields"); continue
                        try:
                            user = _fb_auth.create_user(email=email, password=pwd, display_name=name)
                            db.collection("users").document(user.uid).set({
                                "display_name": name, "email": email,
                                "role": role, "created_at": datetime.now(timezone.utc)
                            })
                            success += 1
                            # Send welcome email per account
                            if bulk_send_email:
                                send_welcome_email(email, name, pwd, role, bulk_app_url)
                        except Exception as e:
                            failed.append(f"{email} — {e}")
                        prog.progress((i+1)/len(rows), text=f"Creating accounts… {i+1}/{len(rows)}")
                    prog.empty()
                    st.success(f"✅  {success} accounts created successfully!")
                    if failed:
                        st.warning(f"⚠️  {len(failed)} failed:")
                        for f in failed: st.caption(f"  • {f}")
                    # Generate summary CSV
                    summary = "display_name,email,role,status\n"
                    for r in rows:
                        email = r.get("email","")
                        status = "failed" if any(email in f for f in failed) else "created"
                        summary += f"{r.get('display_name','')},{email},{r.get('role','student')},{status}\n"
                    st.download_button("⬇️  Download result summary", summary.encode(),
                                       f"bulk_create_result_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", "text/csv")

        with mem3:
            st.markdown("#### Export student data")
            exp_comp = st.selectbox("Competition filter",["All"]+list(COMPETITIONS.keys()),key="exp_comp")
            c_a,c_b = st.columns(2)
            with c_a:
                st.markdown("**Scores CSV** — 1 row per session")
                if st.button("📥  Generate scores CSV",key="exp_csv",use_container_width=True):
                    try:
                        rows=[]
                        for u in db.collection("users").stream():
                            uid=u.id; prof=u.to_dict(); sref=db.collection("users").document(uid).collection("exam_sessions")
                            if exp_comp!="All": sref=sref.where("competition","==",exp_comp)
                            for s in sref.stream():
                                sd=s.to_dict(); ts=sd.get("timestamp_start"); tbd=sd.get("topic_breakdown",{})
                                rows.append({"name":prof.get("display_name",""),"email":prof.get("email",""),
                                             "competition":sd.get("competition",""),"level":sd.get("level",""),
                                             "date":ts.strftime("%Y-%m-%d") if ts else "","score":sd.get("raw_score",""),
                                             "max":sd.get("max_score",""),"pct":sd.get("pct",""),"duration_sec":sd.get("duration_sec",""),
                                             **{f"{t.lower().replace(' ','_')}_pct":round(tbd.get(t,{}).get("correct",0)/max(tbd.get(t,{}).get("total",1),1)*100) if tbd.get(t) else "" for t in TOPICS}})
                        if rows:
                            buf=io.StringIO(); w=csv.DictWriter(buf,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
                            st.download_button(f"⬇️  Download ({len(rows)} rows)",buf.getvalue().encode(),f"mathcomp_scores_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")
                        else: st.info("No data.")
                    except Exception as e: st.error(f"Error: {e}")
            with c_b:
                st.markdown("**Answer log CSV** — 1 row per answer")
                if st.button("📥  Generate answer log",key="exp_ans",use_container_width=True):
                    try:
                        rows=[]
                        for u in db.collection("users").stream():
                            uid=u.id; prof=u.to_dict(); sref=db.collection("users").document(uid).collection("exam_sessions")
                            if exp_comp!="All": sref=sref.where("competition","==",exp_comp)
                            for s in sref.stream():
                                sd=s.to_dict(); ts=sd.get("timestamp_start")
                                for qid,ans in sd.get("answers",{}).items():
                                    rows.append({"name":prof.get("display_name",""),"email":prof.get("email",""),
                                                 "competition":sd.get("competition",""),"level":sd.get("level",""),
                                                 "date":ts.strftime("%Y-%m-%d") if ts else "","question_id":qid,
                                                 "topic":ans.get("topic",""),"chosen":ans.get("chosen",""),
                                                 "correct":ans.get("correct",""),"is_correct":ans.get("is_correct",""),"time_sec":ans.get("time_sec","")})
                        if rows:
                            buf=io.StringIO(); w=csv.DictWriter(buf,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
                            st.download_button(f"⬇️  Download ({len(rows)} rows)",buf.getvalue().encode(),f"mathcomp_answers_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")
                        else: st.info("No data.")
                    except Exception as e: st.error(f"Error: {e}")

    # ── Tab 4: Competitions ────────────────────
    with tab4:
        st.subheader("Competition Management")
        ct1,ct2,ct3,ct4,ct5 = st.tabs([
            "➕  Add Competition",
            "✅  Enable / Disable",
            "📝  Edit / Delete",
            "🔗  Add Questions",
            "⚡  Realtime Contest",
        ])

        # ── ct1: Add new competition ──────────────
        with ct1:
            st.markdown("#### Add a new competition to the catalog")
            st.caption("Once added, it will appear in the student exam selection dropdown.")

            with st.form("add_comp_catalog"):
                c1,c2 = st.columns(2)
                cn_name = c1.text_input("Competition name *", placeholder="e.g. Singapore Mathematical Olympiad")
                cn_code = c2.text_input("Short code *", placeholder="e.g. SMO_Junior")
                cn_desc = st.text_input("Description", placeholder="e.g. Junior level · 35 questions · 90 min")

                c3,c4,c5 = st.columns(3)
                cn_spq   = c3.number_input("Seconds per question", 30, 600, 120, step=10)
                cn_score_c = c4.number_input("Score correct",  0.0, 10.0, 1.0, step=0.5)
                cn_score_w = c5.number_input("Score wrong (negative = penalty)", -5.0, 0.0, 0.0, step=0.5)

                st.markdown("**Levels / Divisions** (one per line)")
                cn_levels_raw = st.text_area("Levels", value="Junior\nSenior\nOpen", height=80)

                sub_cn = st.form_submit_button("➕  Add to catalog", type="primary", use_container_width=True)

            if sub_cn:
                if not cn_name or not cn_code:
                    st.error("Name and code are required.")
                else:
                    levels = [l.strip() for l in cn_levels_raw.strip().splitlines() if l.strip()]
                    if not levels: levels = ["General"]
                    try:
                        db.collection("competition_catalog").document(cn_code).set({
                            "name":       cn_name,
                            "code":       cn_code,
                            "description":cn_desc,
                            "levels":     levels,
                            "secs_per_q": int(cn_spq),
                            "scoring":    {"correct":cn_score_c,"wrong":cn_score_w,"blank":0},
                            "created_at": datetime.now(timezone.utc),
                        })
                        _invalidate_custom_cache()  # clear cache
                        st.success(f"✅  **{cn_name}** added to catalog!")
                        st.info(f"Students can now select it from the exam dropdown. "
                                f"Add questions via the **🔗 Add Questions** tab.")
                    except Exception as e:
                        st.error(f"Error: {e}")

            # Show pre-built suggestions
            st.divider()
            st.markdown("#### 💡 Quick-add popular competitions")
            SUGGESTIONS = [
                ("SMO Junior",       "SMO_Junior",    "Singapore Mathematical Olympiad · Junior",         ["Open","Short List"],          180, 1, 0),
                ("SMO Senior",       "SMO_Senior",    "Singapore Mathematical Olympiad · Senior",         ["Open","Short List"],          180, 1, 0),
                ("SMO Open",         "SMO_Open",      "Singapore Mathematical Olympiad · Open",           ["Open","Short List"],          180, 1, 0),
                ("IMO",              "IMO",           "International Mathematical Olympiad",              ["Day 1","Day 2"],              600, 7, 0),
                ("APMO",             "APMO",          "Asian Pacific Mathematics Olympiad",               ["General"],                    480, 7, 0),
                ("SASMO",            "SASMO",         "Singapore & Asian Schools Math Olympiad",          ["Grade 2","Grade 3","Grade 4","Grade 5","Grade 6","Grade 7","Grade 8","Grade 9","Grade 10"], 90, 4, -1),
                ("SEAMO",            "SEAMO",         "South East Asian Mathematical Olympiad",           ["Paper A","Paper B","Paper C","Paper D","Paper E","Paper F"], 90, 1, 0),
                ("Thailand ONET",    "ONET",          "O-NET คณิตศาสตร์",                                 ["Grade 6","Grade 9","Grade 12"], 90, 1, 0),
                ("Thailand PAT 1",   "PAT1",          "PAT 1 คณิตศาสตร์",                                ["PAT 1"],                      120, 1, 0),
                ("Kangaroo Math",    "KANGAROO",      "Math Kangaroo / Känguru der Mathematik",           ["Pre-Ecolier","Ecolier","Benjamin","Cadet","Junior","Student"], 90, 1, 0),
                ("IMAS",             "IMAS",          "International Mathematics Assessment for Schools", ["Grade 2-4","Grade 5-6","Grade 7-8"], 90, 1, 0),
                ("HIMCM",            "HIMCM",         "High School Mathematical Contest in Modeling",     ["General"],                    300, 1, 0),
            ]
            existing_codes = set()
            try:
                existing_codes = {d.id for d in db.collection("competition_catalog").stream()}
            except: pass

            cols = st.columns(3)
            for i, (name,code,desc,levels,spq,sc,sw) in enumerate(SUGGESTIONS):
                with cols[i%3]:
                    already = code in existing_codes
                    btn_label = f"✅ {name}" if already else f"➕ {name}"
                    if st.button(btn_label, key=f"qa_{code}",
                                 use_container_width=True, disabled=already):
                        try:
                            db.collection("competition_catalog").document(code).set({
                                "name":cn_name if False else name,"code":code,"description":desc,
                                "levels":levels,"secs_per_q":spq,
                                "scoring":{"correct":sc,"wrong":sw,"blank":0},
                                "created_at":datetime.now(timezone.utc),
                            })
                            _invalidate_custom_cache()
                            st.success(f"Added {name}!"); st.rerun()
                        except Exception as e: st.error(str(e))

        # ── ct2: Enable / Disable ────────────────
        with ct2:
            st.markdown("#### Enable / Disable competitions")
            st.caption("Disabled competitions are hidden from students but remain in the database.")

            all_comps_full = get_all_competitions(include_disabled=True)
            disabled_set   = load_disabled_competitions()

            # Group: built-in vs custom
            builtin_names = list(COMPETITIONS_BUILTIN.keys())
            custom_names  = [k for k in all_comps_full if k not in builtin_names]

            def comp_toggle_row(name, info):
                is_enabled = name not in disabled_set
                c1, c2, c3 = st.columns([4, 2, 1])
                c1.markdown(f"**{name}**")
                c2.caption(info.get("description",""))
                new_val = c3.toggle(
                    "##tog", value=is_enabled,
                    key=f"tog_{name.replace(' ','_').replace('(','').replace(')','')}"
                )
                if new_val != is_enabled:
                    set_competition_enabled(name, new_val)
                    st.rerun()

            st.markdown("**Built-in competitions**")
            for name in builtin_names:
                comp_toggle_row(name, COMPETITIONS_BUILTIN[name])

            if custom_names:
                st.divider()
                st.markdown("**Custom competitions**")
                for name in custom_names:
                    comp_toggle_row(name, all_comps_full[name])

            st.divider()
            enabled_count  = len(all_comps_full) - len(disabled_set)
            disabled_count = len(disabled_set)
            c1, c2 = st.columns(2)
            c1.metric("Enabled",  enabled_count)
            c2.metric("Disabled", disabled_count)
            if disabled_set:
                st.caption(f"Disabled: {', '.join(sorted(disabled_set))}")

        # ── ct3: Edit / Delete ────────────────────
        with ct3:
            st.markdown("#### Edit or delete competitions in the catalog")
            try:
                cat_docs = list(db.collection("competition_catalog").stream())
                if not cat_docs:
                    st.info("No custom competitions added yet.")
                else:
                    for doc in cat_docs:
                        d = doc.to_dict()
                        with st.expander(f"**{d.get('name','')}** · {d.get('description','')}"):
                            ef1,ef2 = st.columns(2)
                            e_name = ef1.text_input("Name",  value=d.get("name",""),  key=f"en_{doc.id}")
                            e_desc = ef2.text_input("Desc",  value=d.get("description",""), key=f"ed_{doc.id}")
                            e_levels = st.text_area("Levels (one per line)",
                                value="\n".join(d.get("levels",[])), height=80, key=f"el_{doc.id}")
                            ef3,ef4,ef5 = st.columns(3)
                            e_spq = ef3.number_input("Sec/q", 10, 600, int(d.get("secs_per_q",120)), key=f"es_{doc.id}")
                            e_sc  = ef4.number_input("Score correct", 0.0, 10.0,
                                float(d.get("scoring",{}).get("correct",1)), key=f"esc_{doc.id}")
                            e_sw  = ef5.number_input("Score wrong", -5.0, 0.0,
                                float(d.get("scoring",{}).get("wrong",0)), key=f"esw_{doc.id}")
                            sb1,sb2 = st.columns(2)
                            if sb1.button("💾  Save", key=f"ecsave_{doc.id}", type="primary", use_container_width=True):
                                lvls = [l.strip() for l in e_levels.splitlines() if l.strip()] or ["General"]
                                db.collection("competition_catalog").document(doc.id).update({
                                    "name":e_name,"description":e_desc,"levels":lvls,
                                    "secs_per_q":int(e_spq),
                                    "scoring":{"correct":e_sc,"wrong":e_sw,"blank":0},
                                })
                                _invalidate_custom_cache()
                                st.success("Updated!"); st.rerun()
                            if sb2.button("🗑️  Delete", key=f"ecdel_{doc.id}", use_container_width=True):
                                db.collection("competition_catalog").document(doc.id).delete()
                                _invalidate_custom_cache()
                                st.warning(f"Deleted {d.get('name','')}"); st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

        # ── ct4: Add questions to competition ─────
        with ct4:
            st.markdown("#### Add questions to a competition")
            all_comps = get_all_competitions(include_disabled=True)

            aq_comp = st.selectbox("Select competition", list(get_all_competitions(include_disabled=True).keys()), key="aq_comp")
            aq_level = st.selectbox("Level", all_comps[aq_comp]["levels"], key="aq_level")
            st.divider()

            aq_tab1, aq_tab2 = st.tabs(["✏️  Add new question", "📥  Select from existing bank"])

            # ── Add new question directly ─────────
            with aq_tab1:
                st.caption("Write a new question and save it directly to this competition.")
                aq_topic = st.selectbox("Topic", TOPICS+["Other"], key="aq_topic")
                aq_diff  = st.selectbox("Difficulty", ["easy","intermediate","advanced"], key="aq_diff")
                aq_year  = st.number_input("Year", 2000, 2030, datetime.now().year, key="aq_year")
                aq_atype = st.selectbox("Answer type", ["mc4","mc5","integer","decimal"], key="aq_atype")

                aq_text = st.text_area("Question text (LaTeX supported)", height=120, key="aq_qtext")
                aq_img  = st.file_uploader("Question image (optional)", type=["png","jpg","jpeg"], key="aq_qimg")
                if aq_text:
                    with st.expander("Preview"): st.markdown(aq_text)

                # AI assess
                if aq_text and st.button("🤖  AI assess difficulty & topic", key="aq_ai_btn"):
                    with st.spinner("Analysing…"):
                        ai_r = ai_assess_question(aq_text, "", "", aq_comp)
                        if ai_r: st.session_state["aq_ai"] = ai_r; st.rerun()
                if "aq_ai" in st.session_state:
                    ar = st.session_state["aq_ai"]
                    st.info(f"🤖 AI suggests — **{ar.get('topic','?')}** · **{ar.get('difficulty','?')}** · {ar.get('topic_reason','')} · {ar.get('difficulty_reason','')}")
                    if st.button("Apply AI suggestion", key="aq_apply_ai"):
                        st.session_state["aq_topic"] = ar.get("topic", aq_topic)
                        st.session_state["aq_diff"]  = ar.get("difficulty", aq_diff)
                        st.session_state.pop("aq_ai",None); st.rerun()

                # Choices
                aq_choices = []; aq_correct = ""
                if aq_atype in ("mc4","mc5"):
                    n = 4 if aq_atype=="mc4" else 5
                    st.markdown("**Answer choices**")
                    ch_cols = st.columns(n)
                    for i in range(n):
                        aq_choices.append(ch_cols[i].text_input(chr(65+i), key=f"aq_ch{i}"))
                    aq_correct = st.selectbox("Correct answer",
                        [chr(65+i) for i in range(n)], key="aq_correct_mc")
                else:
                    aq_correct = st.text_input("Correct answer (number)", key="aq_correct_num")

                st.divider()
                st.markdown("**Solution (optional)**")
                sc1, sc2 = st.columns(2)
                aq_sol     = sc1.text_area("Solution text / LaTeX", height=80, key="aq_sol")
                aq_sol_img = sc2.file_uploader("Solution image", type=["png","jpg","jpeg"], key="aq_sol_img")
                if aq_sol_img:
                    st.image(aq_sol_img, caption="Solution preview", use_container_width=True)

                if st.button("💾  Save question to this competition", type="primary", key="aq_save"):
                    if not aq_text and not aq_img:
                        st.error("Question text or image is required.")
                    else:
                        with st.spinner("Saving…"):
                            ar = st.session_state.get("aq_ai",{})
                            ts = datetime.now().timestamp()
                            q_url   = upload_img(aq_img,     f"questions/{ts}_q.{aq_img.name.split('.')[-1]}")     if aq_img     else ""
                            sol_url = upload_img(aq_sol_img, f"solutions/{ts}_s.{aq_sol_img.name.split('.')[-1]}") if aq_sol_img else ""
                            save_question({
                                "competition":        aq_comp,
                                "level":              aq_level,
                                "topic":              ar.get("topic",    aq_topic) if ar else aq_topic,
                                "difficulty":         ar.get("difficulty",aq_diff)  if ar else aq_diff,
                                "year":               int(aq_year),
                                "answer_type":        aq_atype,
                                "question_text":      aq_text,
                                "question_image_url": q_url,
                                "choices":            aq_choices,
                                "correct_answer":     str(aq_correct),
                                "solution_text":      aq_sol,
                                "solution_image_url": sol_url,
                            })
                            st.session_state.pop("aq_ai",None)
                        st.success(f"✅  Question saved to **{aq_comp} · {aq_level}**!")

            # ── Select from existing bank ─────────
            with aq_tab2:
                st.caption("Copy questions from the existing bank into this competition.")

                src_comp  = st.selectbox("Source competition", list(get_all_competitions(include_disabled=True).keys()), key="src_comp")
                src_topic = st.selectbox("Topic filter", ["All"]+TOPICS+["Other"], key="src_topic")
                src_diff  = st.selectbox("Difficulty filter", ["All","easy","intermediate","advanced"], key="src_diff")

                if st.button("🔍  Browse source questions", key="src_browse"):
                    try:
                        ref = db.collection("questions").where("competition","==",src_comp)
                        if src_topic != "All": ref = ref.where("topic","==",src_topic)
                        if src_diff  != "All": ref = ref.where("difficulty","==",src_diff)
                        docs = list(ref.limit(100).stream())
                        st.session_state["src_docs"] = [(d.id, d.to_dict()) for d in docs]
                    except Exception as e:
                        st.error(f"Error: {e}")

                src_docs = st.session_state.get("src_docs",[])
                if src_docs:
                    st.caption(f"{len(src_docs)} questions found — tick the ones to copy")
                    selected_ids = []
                    for did, d in src_docs:
                        qt = d.get("question_text","(image only)")[:70]
                        label = f"[{d.get('difficulty','')}] [{d.get('topic','')}] {qt}…"
                        if st.checkbox(label, key=f"src_sel_{did}"):
                            selected_ids.append((did, d))

                    if selected_ids:
                        st.markdown(f"**{len(selected_ids)} question(s) selected**")
                        keep_original = st.toggle(
                            "Keep original competition tag (copy as-is)",
                            value=False, key="src_keep_orig",
                            help="Off = re-tag to target competition/level. On = keep original tags.")

                        if st.button(f"📥  Copy {len(selected_ids)} question(s) → {aq_comp} · {aq_level}",
                                     type="primary", key="src_copy"):
                            copied = 0
                            for did, d in selected_ids:
                                new_q = dict(d)
                                new_q.pop("id", None)
                                if not keep_original:
                                    new_q["competition"] = aq_comp
                                    new_q["level"]       = aq_level
                                db.collection("questions").add(new_q)
                                copied += 1
                            st.success(f"✅  {copied} question(s) copied to **{aq_comp} · {aq_level}**!")
                            st.session_state.pop("src_docs",None)
                            st.rerun()

        # ── ct5: Realtime contest ─────────────────
        with ct5:
            st.markdown("#### ⚡ Realtime Contest Control")
            st.caption("Preset student roster, open/close exam window, and monitor live submissions.")

            # Load all competitions
            all_rt_comps = {}
            try:
                for doc in db.collection("competition_catalog").stream():
                    d = doc.to_dict()
                    n = d.get("name","")
                    if n: all_rt_comps[n] = d
            except: pass
            for n, info in get_all_competitions(include_disabled=True).items():
                if n not in all_rt_comps:
                    all_rt_comps[n] = info

            if not all_rt_comps:
                st.warning("No competitions found. Create one in the ➕ Add Competition tab first.")
            else:
                sel_name = st.selectbox("Select competition to run",
                    list(all_rt_comps.keys()), key="rt_sel")

                rt_doc_id  = sel_name.replace(" ","_").replace("/","_")
                rt_doc_ref = db.collection("realtime_sessions").document(rt_doc_id)
                rt_doc     = rt_doc_ref.get()
                rt_data    = rt_doc.to_dict() if rt_doc.exists else {}
                status     = rt_data.get("status","not started")
                roster     = rt_data.get("roster",[])        # list of UIDs
                require_roster = rt_data.get("require_roster", False)

                # ── Tabs inside realtime ────────────
                rt1, rt2, rt3 = st.tabs(["📋  Roster", "⚡  Controls", "🏆  Live Monitor"])

                # ── rt1: Roster management ───────────
                with rt1:
                    st.markdown("#### Student Roster")
                    st.caption("Only students on the roster can enter this competition. Leave roster empty to allow all students.")

                    # Require roster toggle
                    new_require = st.toggle(
                        "Restrict to roster only (block students not on list)",
                        value=require_roster, key="rt_require_roster")
                    if new_require != require_roster:
                        rt_doc_ref.set({"require_roster": new_require}, merge=True)
                        st.rerun()

                    st.divider()

                    # Load all students for selection
                    try:
                        all_students = [
                            {"uid": d.id, **d.to_dict()}
                            for d in db.collection("users").stream()
                            if d.to_dict().get("role","student") != "admin"
                        ]
                    except:
                        all_students = []

                    # Current roster display
                    roster_uids = set(roster)
                    roster_members = [s for s in all_students if s["uid"] in roster_uids]
                    non_roster    = [s for s in all_students if s["uid"] not in roster_uids]

                    st.markdown(f"**Current roster: {len(roster_members)} student(s)**")
                    if roster_members:
                        for s in roster_members:
                            c1,c2,c3 = st.columns([4,3,1])
                            c1.markdown(f"**{s.get('display_name','—')}**")
                            c2.caption(s.get("email","—"))
                            if c3.button("✕", key=f"rm_{s['uid']}_{rt_doc_id}",
                                         use_container_width=True):
                                new_roster = [u for u in roster if u != s["uid"]]
                                rt_doc_ref.set({"roster": new_roster}, merge=True)
                                st.rerun()
                    else:
                        if require_roster:
                            st.warning("Roster is empty — no students can enter yet. Add students below.")
                        else:
                            st.info("No roster set — all students can enter.")

                    st.divider()

                    # Add students
                    st.markdown("**Add students to roster**")

                    # Option 1: Search and add individually
                    search_r = st.text_input("Search by name or email", key="rt_roster_search")
                    filtered_r = [s for s in non_roster
                                  if search_r.lower() in s.get("display_name","").lower()
                                  or search_r.lower() in s.get("email","").lower()
                                  ] if search_r else non_roster

                    if filtered_r:
                        st.caption(f"{len(filtered_r)} student(s) not on roster")
                        add_selected = []
                        for s in filtered_r[:20]:
                            if st.checkbox(
                                f"{s.get('display_name','—')} · {s.get('email','—')}",
                                key=f"add_{s['uid']}_{rt_doc_id}"
                            ):
                                add_selected.append(s["uid"])
                        if add_selected:
                            if st.button(f"➕  Add {len(add_selected)} student(s) to roster",
                                         type="primary", key="rt_add_sel"):
                                new_roster = list(set(roster) | set(add_selected))
                                rt_doc_ref.set({"roster": new_roster}, merge=True)
                                st.success(f"Added {len(add_selected)} student(s)!")
                                st.rerun()

                    st.divider()

                    # Option 2: Add ALL students at once
                    c_all1, c_all2 = st.columns(2)
                    if c_all1.button("➕  Add ALL students to roster",
                                     use_container_width=True, key="rt_add_all"):
                        all_uids = [s["uid"] for s in all_students]
                        rt_doc_ref.set({"roster": all_uids}, merge=True)
                        st.success(f"Added all {len(all_uids)} students!")
                        st.rerun()
                    if c_all2.button("🗑️  Clear entire roster",
                                     use_container_width=True, key="rt_clear_roster"):
                        rt_doc_ref.set({"roster": []}, merge=True)
                        st.warning("Roster cleared.")
                        st.rerun()

                    # Option 3: CSV upload for roster
                    st.divider()
                    st.markdown("**Import roster from CSV** (column: `email`)")
                    roster_csv = st.file_uploader("Upload roster CSV",
                        type=["csv"], key="rt_roster_csv")
                    if roster_csv and st.button("📥  Import roster from CSV",
                                                key="rt_import_csv"):
                        import io as _io, csv as _csv
                        reader = _csv.DictReader(_io.StringIO(
                            roster_csv.read().decode("utf-8-sig")))
                        csv_emails = {row.get("email","").strip().lower()
                                      for row in reader if row.get("email")}
                        matched_uids = [
                            s["uid"] for s in all_students
                            if s.get("email","").lower() in csv_emails
                        ]
                        not_found = csv_emails - {
                            s.get("email","").lower() for s in all_students
                        }
                        new_roster = list(set(roster) | set(matched_uids))
                        rt_doc_ref.set({"roster": new_roster}, merge=True)
                        st.success(f"✅  Added {len(matched_uids)} students from CSV!")
                        if not_found:
                            st.warning(f"⚠️  {len(not_found)} email(s) not found in system: "
                                       f"{', '.join(list(not_found)[:5])}")
                        st.rerun()

                # ── rt2: Controls ────────────────────
                with rt2:
                    st.markdown("#### Exam Controls")

                    badge_color = {"open":"#22C55E","closed":"#EF4444",
                                   "not started":"#8898CC"}.get(status,"#8898CC")
                    st.markdown(
                        f"<div style='display:inline-flex;align-items:center;gap:8px;"
                        f"background:#F8F9FF;border:1.5px solid #E8ECF8;border-radius:8px;"
                        f"padding:8px 16px;margin-bottom:16px;'>"
                        f"<span style='width:10px;height:10px;border-radius:50%;"
                        f"background:{badge_color};display:inline-block;'></span>"
                        f"<span style='font-weight:600;color:#1B2B6B;'>"
                        f"Status: {status.upper()}</span></div>",
                        unsafe_allow_html=True)
                    if rt_data.get("opened_at"):
                        st.caption(f"Opened: {rt_data['opened_at'].strftime('%d %b %Y %H:%M')}")
                    if rt_data.get("closed_at"):
                        st.caption(f"Closed: {rt_data['closed_at'].strftime('%d %b %Y %H:%M')}")

                    # Roster summary
                    if require_roster:
                        st.info(f"🔒 Restricted to roster: **{len(roster)} student(s)** registered")
                    else:
                        st.info("🔓 Open to all students (no roster restriction)")

                    c1,c2,c3 = st.columns(3)
                    if c1.button("▶️  Open exam", type="primary", use_container_width=True):
                        rt_doc_ref.set({
                            "competition": sel_name,
                            "status":      "open",
                            "opened_at":   datetime.now(timezone.utc),
                            "closed_at":   None,
                        }, merge=True)
                        st.success(f"✅  **{sel_name}** is now OPEN!")
                        st.rerun()
                    if c2.button("⏹️  Close exam", use_container_width=True):
                        rt_doc_ref.set({
                            "status":    "closed",
                            "closed_at": datetime.now(timezone.utc),
                        }, merge=True)
                        st.warning(f"🔒  **{sel_name}** is now CLOSED.")
                        st.rerun()
                    if c3.button("🔄  Reset", use_container_width=True):
                        rt_doc_ref.set({
                            "competition":"not started",
                            "status":     "not started",
                            "opened_at":  None,
                            "closed_at":  None,
                        }, merge=True)
                        st.info("Reset.")
                        st.rerun()

                    st.divider()
                    app_url   = st.secrets.get("APP_URL","https://share.streamlit.io")
                    share_url = f"{app_url}?comp={sel_name.replace(' ','+')}"
                    st.markdown("**📎 Share this link with students:**")
                    st.code(share_url, language=None)
                    st.caption("Students click the link → login → waiting room → auto-enters when you open the exam")

                # ── rt3: Live monitor ────────────────
                with rt3:
                    st.markdown("#### 🏆 Live Monitor")
                    st.caption("Shows submitted results AND live progress of students currently in the exam.")

                    if st.button("🔄  Refresh", key="rt_refresh", type="primary"):
                        st.session_state["rt_lb_show"] = True

                    if st.session_state.get("rt_lb_show"):
                        try:
                            # Get all submissions for this competition
                            # Note: no order_by to avoid needing a composite Firestore index
                            submissions = {}
                            for u in db.collection("users").stream():
                                uid  = u.id
                                prof = u.to_dict()
                                if prof.get("role") == "admin": continue
                                ss_all = list(
                                    db.collection("users").document(uid)
                                    .collection("exam_sessions")
                                    .where("competition","==",sel_name)
                                    .stream()
                                )
                                if ss_all:
                                    # Pick best score — sort in Python, no index needed
                                    best = max(ss_all,
                                               key=lambda d: d.to_dict().get("raw_score",0))
                                    s  = best.to_dict()
                                    ts = s.get("timestamp_start")
                                    submissions[uid] = {
                                        "name":  prof.get("display_name","—"),
                                        "email": prof.get("email","—"),
                                        "score": s.get("raw_score",0),
                                        "max":   s.get("max_score",0),
                                        "pct":   s.get("pct",0),
                                        "time":  ts.strftime("%H:%M:%S") if ts else "—",
                                        "dur":   f"{s.get('duration_sec',0)//60}m "
                                                 f"{s.get('duration_sec',0)%60}s",
                                    }

                            # Determine who to show
                            if roster and require_roster:
                                # Show roster students only
                                roster_students = {
                                    s["uid"]: s for s in all_students
                                    if s["uid"] in roster_uids
                                }
                                submitted_uids = set(submissions.keys())
                                waiting_uids   = roster_uids - submitted_uids

                                submitted_list = sorted(
                                    [submissions[uid] for uid in submitted_uids if uid in roster_uids],
                                    key=lambda x:x["score"], reverse=True
                                )
                                waiting_list = [
                                    roster_students[uid]
                                    for uid in waiting_uids
                                    if uid in roster_students
                                ]
                            else:
                                # Show all who submitted
                                submitted_list = sorted(
                                    submissions.values(),
                                    key=lambda x:x["score"], reverse=True
                                )
                                waiting_list = []

                            # Load live progress from Firestore sub-collection
                            try:
                                prog_docs = list(
                                    db.collection("realtime_sessions")
                                    .document(rt_doc_id)
                                    .collection("progress")
                                    .stream()
                                )
                                progress_map = {d.id: d.to_dict() for d in prog_docs}
                            except:
                                progress_map = {}

                            in_progress = {
                                uid: p for uid, p in progress_map.items()
                                if p.get("status") == "in_progress"
                            }

                            # Summary
                            sc1,sc2,sc3,sc4 = st.columns(4)
                            sc1.metric("Submitted",   len(submitted_list))
                            sc2.metric("In progress", len(in_progress))
                            sc3.metric("Waiting",     len(waiting_list))
                            sc4.metric("Total",       len(submitted_list)+len(in_progress)+len(waiting_list))

                            # Live progress table
                            if in_progress:
                                st.divider()
                                st.markdown("#### 📝 Currently in exam")
                                ph1,ph2,ph3,ph4,ph5 = st.columns([3,2,2,2,3])
                                for col,lbl in zip([ph1,ph2,ph3,ph4,ph5],
                                    ["Name","Current Q","Answered","Progress",""]):
                                    col.markdown(f"**{lbl}**")
                                st.markdown("<hr style='margin:4px 0;border-color:#E8ECF8;'>",
                                            unsafe_allow_html=True)
                                for p_uid, p in sorted(
                                    in_progress.items(),
                                    key=lambda x: x[1].get("pct_done",0), reverse=True
                                ):
                                    pname   = p.get("display_name","—")
                                    cur_q   = p.get("current_q",0)
                                    ans     = p.get("answered",0)
                                    total_q = p.get("total",0)
                                    pct     = p.get("pct_done",0)
                                    updated = p.get("updated_at")
                                    ago     = ""
                                    if updated:
                                        secs = int((datetime.now(timezone.utc)-updated).total_seconds())
                                        ago  = f"{secs}s ago"

                                    pr1,pr2,pr3,pr4,pr5 = st.columns([3,2,2,2,3])
                                    pr1.markdown(f"**{pname}**")
                                    pr2.markdown(f"Q{cur_q} / {total_q}")
                                    pr3.markdown(f"{ans} answered")
                                    pr4.progress(pct/100 if pct<=100 else 1.0,
                                                 text=f"{pct}%")
                                    pr5.caption(ago)

                            # Submitted table
                            if submitted_list:
                                st.markdown("#### ✅ Submitted")
                                h1,h2,h3,h4,h5,h6 = st.columns([1,3,2,2,2,2])
                                for col,lbl in zip(
                                    [h1,h2,h3,h4,h5,h6],
                                    ["#","Name","Score","Accuracy","Time","Duration"]
                                ):
                                    col.markdown(f"**{lbl}**")
                                st.divider()
                                for rank,s in enumerate(submitted_list,1):
                                    medal = ("🥇" if rank==1 else
                                             "🥈" if rank==2 else
                                             "🥉" if rank==3 else f"**{rank}**")
                                    r1,r2,r3,r4,r5,r6 = st.columns([1,3,2,2,2,2])
                                    r1.markdown(medal)
                                    r2.markdown(f"**{s['name']}**")
                                    r3.markdown(f"{s['score']} / {s['max']}")
                                    pct_color = ("🟢" if s["pct"]>=70 else
                                                 "🟡" if s["pct"]>=50 else "🔴")
                                    r4.markdown(f"{pct_color} {s['pct']}%")
                                    r5.markdown(s["time"])
                                    r6.markdown(s["dur"])

                            # Waiting table
                            if waiting_list:
                                st.divider()
                                st.markdown(f"#### ⏳ Not yet submitted ({len(waiting_list)})")
                                for s in waiting_list:
                                    c1,c2 = st.columns([4,4])
                                    c1.markdown(f"**{s.get('display_name','—')}**")
                                    c2.caption(s.get("email","—"))

                            if not submitted_list and not waiting_list:
                                st.info("No submissions yet. Waiting for students…")

                        except Exception as e:
                            st.error(f"Monitor error: {e}")

    footer()


# ══════════════════════════════════════════════
# PDF Report generator (student personal report)
# ══════════════════════════════════════════════

# ══════════════════════════════════════════════
# Page: My History (student)
# ══════════════════════════════════════════════
def page_admin_analytics():
    require_auth(); require_admin(); inject_css()
    topbar("Analytics Dashboard")

    st.markdown("""
    <div class="mc-hero">
      <div class="mc-hero-eyebrow">Admin overview</div>
      <div class="mc-hero-title">Analytics <em>Dashboard</em></div>
    </div>
    <div class="mc-body">""", unsafe_allow_html=True)

    if st.button("🔄  Load analytics", type="primary", key="load_analytics"):
        st.session_state["analytics_loaded"] = True

    if not st.session_state.get("analytics_loaded"):
        st.info("Click 'Load analytics' to fetch data from Firestore.")
        st.markdown("</div>", unsafe_allow_html=True)
        footer(); return

    with st.spinner("Loading all student data…"):
        try:
            all_users    = [{"uid":d.id,**d.to_dict()} for d in db.collection("users").stream()]
            students     = [u for u in all_users if u.get("role")!="admin"]
            all_sessions = []
            for u in students:
                for s in db.collection("users").document(u["uid"]).collection("exam_sessions").stream():
                    sd = s.to_dict()
                    sd["student_name"]  = u.get("display_name","—")
                    sd["student_email"] = u.get("email","—")
                    all_sessions.append(sd)
        except Exception as e:
            st.error(f"Error: {e}"); st.markdown("</div>",unsafe_allow_html=True); footer(); return

    # ── Summary metrics ────────────────────────
    n_students  = len(students)
    n_sessions  = len(all_sessions)
    avg_pct     = round(sum(s.get("pct",0) for s in all_sessions)/n_sessions,1) if all_sessions else 0
    completion  = round(sum(1 for s in all_sessions if s.get("pct",0)>0)/n_sessions*100) if all_sessions else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total Students",   n_students)
    c2.metric("Total Sessions",   n_sessions)
    c3.metric("Avg Accuracy",     f"{avg_pct}%")
    c4.metric("Completion Rate",  f"{completion}%")
    st.divider()

    # ── Topic weakness heatmap ─────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown("#### 📊 Class average by topic")
        topic_totals = {t:{"correct":0,"total":0} for t in TOPICS}
        for s in all_sessions:
            for t,v in s.get("topic_breakdown",{}).items():
                if t in topic_totals:
                    topic_totals[t]["correct"] += v.get("correct",0)
                    topic_totals[t]["total"]   += v.get("total",0)
        fig_bar = go.Figure()
        labels, vals, colors = [],[],[]
        for t,v in topic_totals.items():
            pct = round(v["correct"]/v["total"]*100) if v["total"]>0 else 0
            labels.append(t); vals.append(pct)
            colors.append("#4A7CF7" if pct>=60 else ("#F5A623" if pct>=40 else "#F472B6"))
        fig_bar.add_trace(go.Bar(x=labels,y=vals,marker_color=colors,text=[f"{v}%" for v in vals],textposition="outside"))
        fig_bar.update_layout(yaxis=dict(range=[0,110],title="Accuracy %"),
                              xaxis_title="Topic",showlegend=False,
                              paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(248,249,255,1)",
                              height=320,margin=dict(t=20,b=20))
        st.plotly_chart(fig_bar,use_container_width=True)

    with col_r:
        st.markdown("#### 📈 Sessions over time")
        from collections import Counter
        date_counts = Counter()
        for s in all_sessions:
            ts = s.get("timestamp_start")
            if ts: date_counts[ts.strftime("%Y-%m-%d")] += 1
        if date_counts:
            dates = sorted(date_counts.keys())
            counts= [date_counts[d] for d in dates]
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=dates,y=counts,mode="lines+markers",
                line=dict(color="#4A7CF7",width=2),marker=dict(size=6,color="#4A7CF7"),fill="tozeroy",
                fillcolor="rgba(74,124,247,0.08)"))
            fig_line.update_layout(xaxis_title="Date",yaxis_title="Sessions",
                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(248,249,255,1)",
                height=320,margin=dict(t=20,b=20))
            st.plotly_chart(fig_line,use_container_width=True)
        else:
            st.info("No session timeline data yet.")

    st.divider()

    # ── At-risk students ───────────────────────
    st.markdown("#### ⚠️ Students needing attention (accuracy < 50%)")
    at_risk = {}
    for s in all_sessions:
        nm = s.get("student_name","—")
        if nm not in at_risk: at_risk[nm] = []
        at_risk[nm].append(s.get("pct",0))

    at_risk_list = [(nm, round(sum(v)/len(v),1), len(v))
                    for nm,v in at_risk.items() if sum(v)/len(v)<50]
    at_risk_list.sort(key=lambda x:x[1])

    if at_risk_list:
        for nm,avg,n in at_risk_list:
            c1,c2,c3 = st.columns([4,2,2])
            c1.markdown(f"**{nm}**")
            c2.markdown(f"Avg accuracy: 🔴 **{avg}%**")
            c3.markdown(f"{n} session{'s' if n!=1 else ''}")
    else:
        st.success("All students are performing at 50%+ — great job! 🎉")

    st.divider()

    # ── Competition popularity ─────────────────
    st.markdown("#### 🏆 Most popular competitions")
    from collections import Counter as _Counter
    comp_counts = _Counter(s.get("competition","?") for s in all_sessions)
    for comp,count in comp_counts.most_common():
        avg = round(sum(s.get("pct",0) for s in all_sessions if s.get("competition","")==comp)
                    / count, 1)
        c1,c2,c3 = st.columns([4,2,2])
        c1.markdown(f"**{comp}**")
        c2.markdown(f"{count} sessions")
        c3.markdown(f"Avg accuracy: {avg}%")

    st.markdown("</div>", unsafe_allow_html=True)
    footer()


# ══════════════════════════════════════════════
# Page: Realtime Competition
# ══════════════════════════════════════════════
def page_admin_student_history():
    require_auth(); require_admin(); inject_css()
    uid   = st.session_state.get("admin_view_uid","")
    name  = st.session_state.get("admin_view_name","Student")
    topbar(f"History — {name}")

    if not uid:
        st.error("No student selected."); return

    try:
        sessions = [s.to_dict() for s in
                    db.collection("users").document(uid)
                    .collection("exam_sessions")
                    .order_by("timestamp_start",
                              direction=firestore.Query.DESCENDING)
                    .limit(100).stream()]
    except Exception as e:
        st.error(f"Error: {e}"); sessions = []

    st.markdown(f"""
    <div class="mc-hero">
      <div class="mc-hero-eyebrow">Admin view · Student history</div>
      <div class="mc-hero-title"><em>{name}</em>'s answers</div>
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

    if st.button("← Back to Members", use_container_width=False):
        st.session_state["page"] = "admin"; st.rerun()

    if not sessions:
        st.info("No sessions recorded yet.")
        st.markdown("</div>", unsafe_allow_html=True); footer(); return

    # Filter
    comps = sorted(set(s.get("competition","") for s in sessions))
    flt   = st.selectbox("Filter by competition", ["All"]+comps, key="adm_hist_filter")
    show  = [s for s in sessions if flt=="All" or s.get("competition","")==flt]

    for s in show:
        ts  = s.get("timestamp_start")
        dt  = ts.strftime("%d %b %Y  %H:%M") if ts else "—"
        pct = s.get("pct",0)
        dot = "🟢" if pct>=70 else ("🟡" if pct>=50 else "🔴")
        answers_map = s.get("answers",{})
        correct = sum(1 for a in answers_map.values() if a.get("is_correct"))
        wrong   = sum(1 for a in answers_map.values() if not a.get("is_correct") and a.get("chosen"))
        blank   = sum(1 for a in answers_map.values() if not a.get("chosen"))

        with st.expander(
            f"{dot}  {s.get('competition','')} · {s.get('level','')} · "
            f"{s.get('difficulty','').capitalize()} · "
            f"**{s.get('raw_score','')} / {s.get('max_score','')}** ({pct}%) · {dt}"
        ):
            # Summary row
            c1,c2,c3 = st.columns(3)
            dur = s.get("duration_sec",0)
            c1.markdown(f"**Duration:** {dur//60}m {dur%60}s")
            c2.markdown(f"**Questions:** {s.get('total_questions','—')}")
            c3.markdown(f"✅ {correct} &nbsp; ❌ {wrong} &nbsp; ⬜ {blank}")

            # Topic breakdown
            tbd = s.get("topic_breakdown",{})
            if tbd:
                st.markdown("**Topic breakdown**")
                for topic,v in tbd.items():
                    tp    = round(v["correct"]/v["total"]*100) if v["total"]>0 else 0
                    color = "#4A7CF7" if tp>=50 else "#F472B6"
                    st.markdown(
                        f'<div class="mc-topic-row">'
                        f'<span class="mc-topic-name">{topic}</span>'
                        f'<div class="mc-bar-bg"><div class="mc-bar-fill" '
                        f'style="width:{tp}%;background:{color};"></div></div>'
                        f'<span class="mc-bar-pct">{tp}%</span></div>',
                        unsafe_allow_html=True)

            # Per-question answer log
            if answers_map:
                st.divider()
                st.markdown("**Per-question answer log**")
                h1,h2,h3,h4,h5,h6 = st.columns([1,4,2,2,2,2])
                for col,lbl in zip([h1,h2,h3,h4,h5,h6],
                                   ["Q","Topic","Chosen","Correct","Result","Time(s)"]):
                    col.markdown(
                        f"<span style='font-size:11px;color:#8898CC;text-transform:uppercase;"
                        f"letter-spacing:.06em;font-family:monospace;'>{lbl}</span>",
                        unsafe_allow_html=True)
                st.markdown("<hr style='margin:4px 0;border-color:#E8ECF8;'>",
                            unsafe_allow_html=True)
                for i,(qid,ans) in enumerate(sorted(answers_map.items()),1):
                    ok     = ans.get("is_correct",False)
                    chosen = ans.get("chosen") or "—"
                    right  = ans.get("correct") or "—"
                    topic  = ans.get("topic","—")
                    tsec   = ans.get("time_sec",0)
                    icon   = "✅" if ok else ("⬜" if not ans.get("chosen") else "❌")
                    r1,r2,r3,r4,r5,r6 = st.columns([1,4,2,2,2,2])
                    r1.markdown(f"**{i}**")
                    r2.markdown(f"<span style='font-size:13px;'>{topic}</span>",
                                unsafe_allow_html=True)
                    r3.markdown(f"`{chosen}`")
                    r4.markdown(f"`{right}`")
                    r5.markdown(icon)
                    r6.markdown(f"{tsec}" if tsec else "—")

    st.markdown("</div>", unsafe_allow_html=True)
    footer()



    if "uid" not in st.session_state: return
    with st.sidebar:
        st.markdown(f"**{st.session_state.get('display_name','')}**")
        st.caption(st.session_state.get("role","student").capitalize())
        st.divider()
        if st.button("🏠  Dashboard",       use_container_width=True):
            for k in ("rt_comp","rt_status"): st.session_state.pop(k,None)
            st.session_state["page"]="dashboard"; st.rerun()
        if st.button("📋  My History",       use_container_width=True): st.session_state["page"]="history";     st.rerun()
        if st.button("🏆  Leaderboard",      use_container_width=True): st.session_state["page"]="leaderboard"; st.rerun()
        if st.session_state.get("role")=="admin":
            st.divider()
            if st.button("⚙️  Admin Panel",      use_container_width=True): st.session_state["page"]="admin";            st.rerun()
            if st.button("📊  Analytics",        use_container_width=True): st.session_state["page"]="admin_analytics";  st.rerun()
        st.divider()
        if st.button("Log out", use_container_width=True): st.session_state.clear(); st.rerun()
        st.markdown("---")
        st.markdown("<div style='font-size:10px;color:rgba(255,255,255,.3);font-family:monospace;line-height:1.7;'>"
                    "© Math Mission Thailand 2026<br>MathComp Platform</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# Router
# ══════════════════════════════════════════════

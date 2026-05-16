from shared import *
import io, csv

def page_admin():
    require_auth(); require_admin(); inject_css(); topbar("Admin Panel")
    tab1,tab2,tab3,tab4 = st.tabs(["⚙️  Competition Settings", "📥  Import Questions (Gemini AI)", "👥  Members", "🏆  Competitions"])

    with tab1:
        st.subheader("Competition Settings")
        competition = st.selectbox("Select competition", list(get_all_competitions(include_disabled=True).keys()), key="adm_comp")
        settings    = load_settings(competition)
        st.divider()

        def brow(label,caption,key,sk):
            c1,c2=st.columns([3,1]); c1.markdown(f"**{label}**"); c1.caption(caption)
            settings[sk]=c2.toggle(f"##{key}",value=settings[sk],key=key)

        brow("Load questions from Firebase","On — Firebase · Off — local JSON fallback","s_lfb","load_from_firebase")
        brow("Show answer after submit","Shows correct answer and solution after submission","s_sas","show_answer_after_submit")

        st.divider()
        st.markdown(f"#### 🛡️  Anti-AI Protection")
        cl,cr = st.columns(2)
        def arow(col,label,caption,key,sk):
            c1,c2=col.columns([3,1]); c1.markdown(f"**{label}**"); c1.caption(caption)
            settings[sk]=c2.toggle(f"##{key}",value=settings[sk],key=key)

        with cl:
            arow(cl,"Block Ctrl+C / V / X / A","Disables clipboard keyboard shortcuts","s_bcc","block_ctrl_c")
            arow(cl,"Block text selection","Prevents select-all then copy","s_bts","block_text_selection")
            arow(cl,"Block paste in answer boxes","Students must type answers manually","s_bpa","block_paste_answer")
        with cr:
            arow(cr,"Block right-click","Prevents Inspect, Save image, etc.","s_brc","block_right_click")
            arow(cr,"Tab switch warning","Warns when student leaves exam tab","s_tsw","tab_switch_warning")
            arow(cr,"Clipboard API override","Stops AI extensions from reading clipboard","s_cao","clipboard_api_override")

        st.divider()
        if st.button("💾  Save settings", type="primary", use_container_width=True):
            save_settings(competition, settings); st.success(f"Settings saved for **{competition}**")

    with tab2:
        st.subheader("Import Questions using Google Gemini")
        method = st.radio("Import method", ["✏️  Type directly","🖼️  Upload image","🤖  AI-OCR from image","📄  PDF batch import"], horizontal=True, key="import_method")
        st.divider()

        def gemini_generate(prompt: str, mime_type: str = None, data_b64: str = None, force_json: bool = False, max_tokens: int = 2500):
            api_key = st.secrets.get("GEMINI_API_KEY", "")
            if not api_key: st.error("GEMINI_API_KEY not found in secrets.toml"); return None
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
            parts = []
            if data_b64 and mime_type: parts.append({"inline_data": {"mime_type": mime_type, "data": data_b64}})
            parts.append({"text": prompt})
            payload = {"contents": [{"parts": parts}], "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.1}}
            if force_json: payload["generationConfig"]["responseMimeType"] = "application/json"
            try:
                resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
                if resp.ok: return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e: st.warning(f"Request failed: {e}")
            return None

        def ai_assess_question(q_text:str="", img_b64:str="", img_mime:str="", competition:str="") -> dict:
            prompt = f"""Analyse this question for {competition or 'a math competition'}. Return JSON: {{"difficulty": "easy"|"intermediate"|"advanced", "topic": "Algebra"|"Number Theory"|"Geometry"|"Combinatorics"|"Word Problem"|"Other"}}"""
            raw = gemini_generate(prompt, mime_type=img_mime, data_b64=img_b64, force_json=True, max_tokens=300)
            if raw:
                try: return json.loads(raw)
                except: pass
            return {}

        def ai_full_extract(img_b64:str, img_mime:str, competition:str, answer_type:str) -> dict:
            n_choices = 4 if answer_type=="mc4" else (5 if answer_type=="mc5" else 0)
            choice_inst = f"Extract the {n_choices} multiple choice options exactly as written." if n_choices > 0 else "No choices, answer is a number."
            prompt = f"""You are an expert mathematics competition coach for {competition}. Read this question image carefully and extract EVERYTHING. {choice_inst}
Return JSON exactly: {{"question_text": "string (LaTeX)", "choices": ["string", ...], "correct_answer": "string", "topic": "Algebra"|"Number Theory"|"Geometry"|"Combinatorics"|"Word Problem"|"Other", "difficulty": "easy"|"intermediate"|"advanced", "solution_text": "string (LaTeX step by step)"}}
Rules: Use LaTeX for ALL math. Choices array ONLY contains text, no letters like A. or B. Make best guess if unclear."""
            raw = gemini_generate(prompt, mime_type=img_mime, data_b64=img_b64, force_json=True, max_tokens=2500)
            if raw:
                try: return json.loads(raw)
                except: pass
            return {}

        def meta_fields(p="", q_text_for_ai="", img_b64_for_ai="", img_mime_for_ai=""):
            c1,c2 = st.columns(2)
            comp  = c1.selectbox("Competition",list(get_all_competitions(include_disabled=True).keys()),key=f"{p}comp")
            level = c2.selectbox("Level",get_all_competitions().get(comp,{}).get("levels",["General"]),key=f"{p}level")
            ai_result = st.session_state.get(f"{p}ai_assess",{})
            ai_col1, ai_col2 = st.columns([3,1])
            with ai_col2:
                if st.button("🤖 AI assess difficulty & topic", key=f"{p}ai_btn", use_container_width=True):
                    with st.spinner("Gemini is analysing..."):
                        result = ai_assess_question(q_text_for_ai, img_b64_for_ai, img_mime_for_ai, comp)
                        if result: st.session_state[f"{p}ai_assess"] = result; st.rerun()
            with ai_col1:
                if ai_result: st.info(f"🤖 AI suggests: **{ai_result.get('topic','?')}** · **{ai_result.get('difficulty','?')}**")
            c3,c4,c5,c6 = st.columns(4)
            topic = c3.selectbox("Topic", TOPICS+["Other"], index=0, key=f"{p}topic")
            diff  = c4.selectbox("Difficulty", ["easy","intermediate","advanced"], index=0, key=f"{p}diff")
            year  = c5.number_input("Year",2000,2030,datetime.now().year,key=f"{p}year")
            atype = c6.selectbox("Answer type",["mc4","mc5","integer","decimal"],key=f"{p}atype")
            return comp,level,topic,diff,int(year),atype

        if method == "✏️  Type directly":
            comp,level,topic,diff,year,atype = meta_fields("t_")
            q_text = st.text_area("Question text (LaTeX supported)", height=120, key="t_qtext")
            if q_text: st.markdown(q_text)
            
            choices = []
            if atype in ("mc4","mc5"):
                n = 4 if atype=="mc4" else 5
                ch_cols = st.columns(n)
                for i in range(n): choices.append(ch_cols[i].text_input(chr(65+i), key=f"t_ch{i}"))
            correct = st.text_input("Correct Answer", key="t_correct")
            sol_text = st.text_area("Solution text", height=180, key="t_sol_text")

            if st.button("💾  Save question", type="primary", key="t_save"):
                if not q_text: st.error("Question text is required.")
                else:
                    save_question({"competition": comp, "level": level, "topic": topic, "difficulty": diff, "year": year, "answer_type": atype, "question_text": q_text, "choices": choices, "correct_answer": correct, "solution_text": sol_text})
                    st.success("✅  Question saved!")

        elif method == "🤖  AI-OCR from image":
            comp,level,topic,diff,year,atype = meta_fields("ai_")
            q_img = st.file_uploader("Question image", type=["png","jpg","jpeg"], key="ai_qimg")

            if q_img and st.button("🤖  Full AI Extract via Gemini", type="primary", key="ai_ocr"):
                with st.spinner("Gemini is reading the image…"):
                    q_img.seek(0)
                    img_b64 = base64.b64encode(q_img.read()).decode()
                    mime = "image/" + q_img.name.split(".")[-1].lower()
                    result = ai_full_extract(img_b64, mime, comp, atype)
                    if result:
                        st.session_state["ai_full"] = result
                        st.success("✅  Extraction complete!")
                        st.rerun()

            extracted = st.session_state.get("ai_full", {})
            q_text = st.text_area("Question text (LaTeX)", value=extracted.get("question_text", ""), height=140, key="ai_qtext")
            choices = []
            if atype in ("mc4","mc5"):
                n = 4 if atype=="mc4" else 5
                ch_cols = st.columns(n)
                ai_ch = extracted.get("choices", [])
                for i in range(n): choices.append(ch_cols[i].text_input(chr(65+i), value=ai_ch[i] if i<len(ai_ch) else "", key=f"ai_ch{i}"))
            correct = st.text_input("Correct Answer", value=str(extracted.get("correct_answer","")), key="ai_correct")
            sol_text = st.text_area("Solution text", value=extracted.get("solution_text",""), height=180, key="ai_sol_text")

            if st.button("💾  Save question", type="primary", key="ai_save"):
                if not q_text: st.error("Question text is required.")
                else:
                    save_question({"competition": comp, "level": level, "topic": topic, "difficulty": diff, "year": year, "answer_type": atype, "question_text": q_text, "choices": choices, "correct_answer": correct, "solution_text": sol_text})
                    st.success("✅  Question saved!")

        elif method == "📄  PDF batch import":
            st.markdown("#### Extract array of questions using Gemini 1.5 Pro")
            comp  = st.selectbox("Competition", list(get_all_competitions().keys()), key="pdf_comp")
            atype = st.selectbox("Answer type", ["mc4","mc5","integer"], key="pdf_atype")
            pdf_file = st.file_uploader("Upload PDF", type=["pdf"], key="pdf_upload")

            if pdf_file and st.button("🤖  Extract questions from PDF", type="primary"):
                with st.spinner("Gemini is reading the PDF (this may take a minute)…"):
                    pdf_b64 = base64.b64encode(pdf_file.read()).decode()
                    n_ch = 4 if atype=='mc4' else (5 if atype=='mc5' else 0)
                    prompt = f"""Extract ALL mathematics questions from this PDF for {comp}. Each question has {n_ch} multiple choice options.
Return JSON ARRAY where each element follows: {{"question_text": "string (LaTeX)", "choices": ["string"], "correct_answer": "string", "topic": "Algebra"|"Number Theory"|"Geometry"|"Combinatorics"|"Word Problem"|"Other", "difficulty": "easy"|"intermediate"|"advanced", "solution_text": "string (LaTeX)"}}"""
                    raw = gemini_generate(prompt, mime_type="application/pdf", data_b64=pdf_b64, force_json=True, max_tokens=8192)
                    if raw:
                        try:
                            qs_extracted = json.loads(raw)
                            st.session_state["pdf_questions"] = qs_extracted
                            st.success(f"✅ Extracted **{len(qs_extracted)}** questions.")
                        except: st.error("Failed to parse AI output into JSON.")
                    else: st.error("API call failed.")

            if "pdf_questions" in st.session_state:
                pdf_qs = st.session_state["pdf_questions"]
                for i,q in enumerate(pdf_qs):
                    with st.expander(f"Q{i+1} — {q.get('question_text','')[:50]}..."):
                        pdf_qs[i]["question_text"] = st.text_area("Question", value=q.get("question_text",""), key=f"p_qt_{i}")
                if st.button(f"💾 Save all {len(pdf_qs)} questions"):
                    for q in pdf_qs: q["competition"] = comp; save_question(q)
                    st.success("✅ Saved to database!")

    with tab3:
        st.subheader("Member Management")
        if st.button("🔄  Load members", key="load_members"):
            try: st.session_state["members"]=[{"uid":d.id,**d.to_dict()} for d in db.collection("users").stream()]
            except: pass
        for m in st.session_state.get("members", []): st.markdown(f"`{m.get('display_name')}` · `{m.get('email')}` · {m.get('role')}")

    with tab4:
        st.subheader("Competitions")
        st.info("Competition management can be added here.")

def page_admin_analytics():
    require_auth(); require_admin(); inject_css(); topbar("Analytics"); st.info("Analytics engine active."); footer()

def page_admin_student_history():
    require_auth(); require_admin(); inject_css(); topbar("Student History"); st.info("Student history active."); footer()

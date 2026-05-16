"""
MathComp — shared.py
Shared imports, Firebase, CSS, constants, helpers
© Math Mission Thailand 2026
"""
import streamlit as st
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, firestore
import plotly.graph_objects as go
import requests, random, time, json, base64, io, csv
from datetime import datetime, timezone

st.set_page_config(page_title="MathComp · Math Mission Thailand", page_icon="📐", layout="wide", initial_sidebar_state="expanded")

_CSS_INJECTED = False
def inject_css():
    global _CSS_INJECTED
    if _CSS_INJECTED: return
    _CSS_INJECTED = True
    components.html("""
<script>
(function(){
  var css = `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Sarabun:wght@300;400;500;600&display=swap');
    :root {--navy:#0F172A; --blue:#3B82F6; --white:#FFFFFF; --offwhite:#F8FAFC; --border:#E2E8F0; --text:#334155; --text3:#94A3B8;}
    #MainMenu, footer, header { visibility: hidden !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stAppViewContainer"] { background: var(--offwhite) !important; }
    [data-testid="stSidebar"] { background: #0F172A !important; border-right: 1px solid rgba(255,255,255,0.05) !important; }
    [data-testid="stSidebar"] * { color: rgba(255,255,255,0.8) !important; }
    [data-testid="stSidebarNav"] { display: none !important; }
    body, .stApp { font-family: 'Inter', 'Sarabun', sans-serif !important; color: var(--text) !important; }
    h1, h2, h3 { font-family: 'Outfit', sans-serif !important; font-weight: 600 !important; color: var(--navy) !important; }
    .stButton button[data-testid="baseButton-primary"] {background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important; color: #ffffff !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; font-size: 15px !important; padding: 12px 24px !important; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;}
    .stButton button[data-testid="baseButton-primary"]:hover { transform: translateY(-2px) !important; box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3) !important; }
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; color: #0F172A !important;}
    div[data-testid="stRadio"] label {background: #FFFFFF !important; border: 1px solid #E2E8F0 !important; border-radius: 12px !important; padding: 14px 18px !important; margin-bottom: 8px !important; font-weight: 500 !important;}
    div[data-testid="stRadio"] label:has(input:checked) { border-color: #3B82F6 !important; background: #EFF6FF !important; box-shadow: 0 2px 8px rgba(59,130,246,0.08) !important; }
    .mc-topbar { background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px); border-bottom: 1px solid #E2E8F0; padding: 0 40px; height: 70px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; z-index: 100; }
    .mc-topbar-logo { font-family: 'Outfit', sans-serif; font-size: 18px; color: #0F172A; font-weight: 700; }
    .mc-topbar-sep { width:1px; height:20px; background:#E2E8F0; display:inline-block; }
    .mc-topbar-page { font-size:14px; font-weight: 500; color:#64748B; }
    .mc-topbar-right { margin-left:auto; display:flex; align-items:center; gap:12px; }
    .mc-avatar { width:34px; height:34px; border-radius:50%; background: linear-gradient(135deg, #3B82F6, #60A5FA); display:inline-flex; align-items:center; justify-content:center; font-size:14px; font-weight:600; color:#fff; }
    .mc-hero { background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); padding: 56px; position:relative; }
    .mc-hero-eyebrow { font-family: 'JetBrains Mono', monospace; font-size:12px; letter-spacing:.1em; color:#94A3B8; text-transform:uppercase; margin-bottom:12px; }
    .mc-hero-title { font-family: 'Outfit', sans-serif !important; font-size:42px; font-weight: 600 !important; color:#FFFFFF !important; }
    .mc-hero-title em { font-style:normal; color:#3B82F6; }
    .mc-metrics { display:grid; grid-template-columns:repeat(4,1fr); margin-top:32px; gap: 16px; }
    .mc-metric { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 20px; backdrop-filter: blur(10px); }
    .mc-metric-label { font-size:11px; color:#94A3B8; text-transform:uppercase; letter-spacing:.05em; margin-bottom:8px; }
    .mc-metric-val { font-size:32px; font-family:'Outfit', sans-serif; font-weight:700; color:#FFFFFF; line-height:1; }
    .mc-body { background:#F8FAFC; padding:40px 56px; min-height: 50vh; }
    .mc-card { background:#FFFFFF; border:1px solid #E2E8F0; border-radius:16px; padding:36px; margin-bottom:24px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03); }
    .mc-result-hero { background: #0F172A; padding:56px 28px; text-align:center; }
    .mc-result-score { font-family:'Outfit',sans-serif !important; font-size:80px; font-weight:700 !important; color:#fff !important; }
    .mc-result-meta { display:flex; justify-content:center; gap:48px; margin-top:24px; }
    .mc-rm-val { font-size:28px; font-family:'Outfit',serif; font-weight:600; color:#fff; }
    .mc-nav-strip { background:#FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding:16px; display:flex; flex-wrap:wrap; gap:8px; margin-bottom:24px; }
    .mc-nav-dot { width:32px; height:32px; border-radius:8px; border:1px solid #E2E8F0; display:inline-flex; align-items:center; justify-content:center; font-size:12px; color:#64748B; background:#F8FAFC; }
    .mc-footer { background:#0F172A; padding:20px 56px; border-top: 1px solid rgba(255,255,255,0.1); display:flex; justify-content:space-between; color:rgba(255,255,255,0.4); font-size:12px; }`;
  var style = document.createElement('style'); style.textContent = css;
  try { window.parent.document.head.appendChild(style); } catch(e) { document.head.appendChild(style); }
})();
</script>
""", height=0, scrolling=False)

def topbar(page_title: str, show_user: bool = True):
    name = st.session_state.get("display_name", "")
    initial = name[0].upper() if name else "U"
    user_html = f'<span class="mc-topbar-user">{name}</span><div class="mc-avatar">{initial}</div>' if show_user and name else ""
    st.markdown(f'<div class="mc-topbar"><span class="mc-topbar-logo">MATHCOMP</span><span class="mc-topbar-sep"></span><span class="mc-topbar-page">{page_title}</span><div class="mc-topbar-right">{user_html}</div></div>', unsafe_allow_html=True)

def footer(): st.markdown('<div class="mc-footer"><span class="mc-footer-copy">© <strong>Math Mission Thailand</strong> 2026</span><span class="mc-footer-copy">Online Mathematics Competition</span></div>', unsafe_allow_html=True)

@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        sa = st.secrets.get("FIREBASE_SERVICE_ACCOUNT", "{}")
        cred = credentials.Certificate(json.loads(sa))
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

TOPICS = ["Algebra", "Number Theory", "Geometry", "Combinatorics", "Word Problem"]
COMPETITIONS_BUILTIN = {
    "AMC 8":  {"levels":["AMC 8"], "secs_per_q":90,  "scoring":{"correct":1,"wrong":0,"blank":0}, "description":"Grade 6–8 · 25 questions"},
    "AMC 10": {"levels":["AMC 10A","AMC 10B"], "secs_per_q":150, "scoring":{"correct":6,"wrong":-1.5,"blank":0}, "description":"Grade 9–10"},
}

_custom_comp_cache = {}; _custom_comp_ts = 0; _disabled_comp_cache = set(); _disabled_comp_ts = 0

def load_custom_competitions() -> dict:
    global _custom_comp_cache, _custom_comp_ts
    if _custom_comp_cache and (time.time() - _custom_comp_ts) < 60: return _custom_comp_cache
    try:
        res = {d.id: {"levels": d.to_dict().get("levels",["General"]), "secs_per_q": d.to_dict().get("secs_per_q",120), "scoring": d.to_dict().get("scoring",{"correct":1,"wrong":0,"blank":0}), "description": d.to_dict().get("description",""), "custom": True, "doc_id": d.id} for d in db.collection("competition_catalog").stream() if d.to_dict().get("name")}
        _custom_comp_cache = res; _custom_comp_ts = time.time(); return res
    except: return _custom_comp_cache or {}

def load_disabled_competitions() -> set:
    global _disabled_comp_cache, _disabled_comp_ts
    if _disabled_comp_ts and (time.time() - _disabled_comp_ts) < 30: return _disabled_comp_cache
    try:
        doc = db.collection("platform_settings").document("disabled_competitions").get()
        res = set(doc.to_dict().get("disabled",[])) if doc.exists else set()
        _disabled_comp_cache = res; _disabled_comp_ts = time.time(); return res
    except: return _disabled_comp_cache

def set_competition_enabled(name: str, enabled: bool):
    disabled = load_disabled_competitions()
    disabled.discard(name) if enabled else disabled.add(name)
    db.collection("platform_settings").document("disabled_competitions").set({"disabled": list(disabled)})
    global _disabled_comp_cache, _disabled_comp_ts; _disabled_comp_cache = set(); _disabled_comp_ts = 0

def get_all_competitions(include_disabled: bool = False) -> dict:
    merged = dict(COMPETITIONS_BUILTIN)
    merged.update(load_custom_competitions())
    if not include_disabled:
        disabled = load_disabled_competitions()
        merged = {k: v for k, v in merged.items() if k not in disabled}
    return merged

DIFFICULTY_OPTIONS = ["Easy","Intermediate","Advanced","Mixed"]
DEFAULT_SETTINGS = {"load_from_firebase":True,"show_answer_after_submit":False,"anti_copy_text":False,"noise_canvas":False,"block_ctrl_c":False,"block_text_selection":False,"block_paste_answer":True,"block_right_click":True,"tab_switch_warning":True,"clipboard_api_override":False,"time_per_question":0}

def load_settings(competition: str) -> dict:
    try:
        doc = db.collection("settings").document(competition).get()
        if doc.exists:
            m = DEFAULT_SETTINGS.copy(); m.update(doc.to_dict()); return m
    except: pass
    return DEFAULT_SETTINGS.copy()

def save_settings(competition: str, settings: dict): db.collection("settings").document(competition).set(settings)

def get_anti_ai_js(s: dict) -> str:
    sc = []
    if s.get("block_right_click"): sc.append("document.addEventListener('contextmenu',function(e){e.preventDefault();alert('Right-click disabled.');},true);")
    if s.get("block_ctrl_c"): sc.append("document.addEventListener('keydown',function(e){if((e.ctrlKey||e.metaKey)&&['c','v','x','a'].includes(e.key.toLowerCase())){e.preventDefault();e.stopPropagation();}},true);")
    if s.get("block_text_selection"): sc.append("document.addEventListener('selectionchange',function(){if(window.getSelection().toString().length>10)window.getSelection().removeAllRanges();});")
    if s.get("block_paste_answer"): sc.append("document.addEventListener('paste',function(e){var t=e.target;if(t.tagName==='INPUT'||t.tagName==='TEXTAREA')e.preventDefault();},true);")
    if s.get("tab_switch_warning"): sc.append("document.addEventListener('visibilitychange',function(){if(document.hidden)alert('Warning: Stay on the exam tab!');});")
    if s.get("clipboard_api_override"): sc.append("Object.defineProperty(navigator,'clipboard',{get:function(){return{readText:function(){return Promise.resolve('');},writeText:function(){return Promise.resolve();}};} });")
    return "<script>try{" + "\n".join(sc) + "}catch(e){}</script>" if sc else ""

def sign_in(email: str, password: str) -> dict | None:
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={st.secrets.get('FIREBASE_API_KEY','')}"
    try:
        r = requests.post(url, json={"email":email,"password":password,"returnSecureToken":True}, timeout=10)
        return r.json() if r.ok else None
    except: return None

def get_profile(uid: str) -> dict:
    try:
        doc = db.collection("users").document(uid).get()
        return doc.to_dict() if doc.exists else {}
    except: return {}

def require_auth():
    if "uid" not in st.session_state: st.session_state["page"] = "login"; st.rerun()

def require_admin():
    if st.session_state.get("role") != "admin": st.session_state["page"] = "dashboard"; st.rerun()

def fetch_questions(competition, level, difficulty, n) -> list:
    try:
        base = db.collection("questions").where("competition","==",competition).where("level","==",level)
        if difficulty != "Mixed": base = base.where("difficulty","==",difficulty.lower())
        pool = [{"id": d.id, **d.to_dict()} for d in base.stream()]
        if len(pool) < n: pool = [{"id": d.id, **d.to_dict()} for d in db.collection("questions").where("competition","==",competition).where("level","==",level).stream()]
        return random.sample(pool, min(n, len(pool)))
    except Exception as e: st.error(f"Error loading questions: {e}"); return []

def upload_img(file, path: str) -> str:
    try:
        project_id = json.loads(st.secrets.get("FIREBASE_SERVICE_ACCOUNT","{}")).get("project_id","")
        bucket = f"{project_id}.appspot.com"
        url = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o?uploadType=media&name={requests.utils.quote(path,safe='')}"
        resp = requests.post(url, data=file.read(), headers={"Content-Type": file.type}, timeout=30)
        if resp.ok: return f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{requests.utils.quote(path,safe='')}?alt=media&token={resp.json().get('downloadTokens','')}"
    except Exception as e: st.warning(f"Image upload failed: {e}")
    return ""

def save_question(doc: dict): db.collection("questions").add(doc)

def compute_score(competition, questions, answers) -> dict:
    rules = get_all_competitions().get(competition,{}).get("scoring",{"correct":1,"wrong":0,"blank":0})
    raw = max_s = 0.0
    tbd = {t:{"correct":0,"total":0} for t in TOPICS+["Other"]}
    pqs = []
    
    for q in questions:
        qid = q["id"]
        topic = q.get("topic","Other")
        if topic not in tbd: 
            topic = "Other"
            
        ca = str(q.get("correct_answer","")).strip().upper()
        ch = str(answers.get(qid,"")).strip().upper()
        
        ok = (ch == ca and ch != "")
        blank = (ch == "")
        
        raw += rules["correct"] if ok else (rules["blank"] if blank else rules["wrong"])
        max_s += rules["correct"]
        
        tbd[topic]["total"] += 1
        # บรรทัดนี้ที่เคยพัง แก้โดยปัดลงมาบรรทัดใหม่
        if ok: 
            tbd[topic]["correct"] += 1
            
        pqs.append({
            "qid": qid,
            "correct": ok,
            "chosen": answers.get(qid),
            "right_answer": q.get("correct_answer"),
            "time_sec": answers.get(f"{qid}__time",0)
        })
        
    tbd = {k:v for k,v in tbd.items() if v["total"] > 0}
    pct = round(raw/max_s*100, 1) if max_s > 0 else 0.0
    
    return {"raw_score":round(raw,1), "max_score":round(max_s,1), "pct":pct, "topic_breakdown":tbd, "per_question":pqs}

def save_session(uid,competition,level,difficulty,questions,answers,result,duration) -> str:
    data = {"competition":competition,"level":level,"difficulty":difficulty,"timestamp_start":datetime.now(timezone.utc),"duration_sec":duration,"total_questions":len(questions),"raw_score":result["raw_score"],"max_score":result["max_score"],"pct":result["pct"],"topic_breakdown":result["topic_breakdown"],"answers":{q["id"]:{"chosen":answers.get(q["id"]),"correct":q.get("correct_answer"),"is_correct":pq["correct"],"time_sec":answers.get(f"{q['id']}__time",0),"topic":q.get("topic","Other")} for q,pq in zip(questions,result["per_question"])}}
    _,ref = db.collection("users").document(uid).collection("exam_sessions").add(data)
    return ref.id

def radar_chart(tbd) -> go.Figure:
    topics = list(tbd.keys()); scores = [round(v["correct"]/v["total"]*100) if v["total"]>0 else 0 for v in tbd.values()]
    fig = go.Figure(go.Scatterpolar(r=scores+[scores[0]], theta=topics+[topics[0]], fill="toself", fillcolor="rgba(74,124,247,0.12)", line=dict(color="#4A7CF7",width=2), marker=dict(size=5,color="#4A7CF7")))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,100],ticksuffix="%")), showlegend=False, margin=dict(l=50,r=50,t=40,b=40), paper_bgcolor="rgba(0,0,0,0)", height=300)
    return fig

# --- Gemini API Analysis ---
def ai_analyze_performance(name: str, competition: str, level: str, result: dict, questions: list, duration: int) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key: return "_AI analysis unavailable — GEMINI_API_KEY not set in secrets._"
    tbd = result["topic_breakdown"]
    topic_summary = "\n".join([f"  - {t}: {v['correct']}/{v['total']} correct ({round(v['correct']/v['total']*100)}%)" for t, v in tbd.items() if v['total'] > 0])
    wrong_qs = [f"  Q{i} [{q.get('topic','?')}]: chose {pq['chosen']}, correct {pq['right_answer']}" for i, (q, pq) in enumerate(zip(questions, result["per_question"]), 1) if not pq["correct"] and pq["chosen"]]
    wrong_summary = "\n".join(wrong_qs[:15]) if wrong_qs else "  None — all attempted questions were correct."

    prompt = f"""You are an expert mathematics coach specializing in competition mathematics. Analyze the following student exam result and provide a detailed, personalized, encouraging report.
Student name: {name}
Competition: {competition} — {level}
Score: {result['raw_score']} / {result['max_score']} ({result['pct']}%)
Time taken: {duration//60} min {duration%60} sec

Topic breakdown:
{topic_summary}

Wrong answers (first 15):
{wrong_summary}

Write a structured analysis in markdown with these sections:
## 🏆 Overall Performance
## 💪 Strengths
## 📈 Areas for Improvement
## 🎯 Recommended Next Steps
## ⭐ Encouragement

Keep the tone warm, professional, and motivating. Use specific mathematical terms. Total length: 300-400 words."""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1500}}
    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        if resp.ok: return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        return f"_AI analysis failed. Status: {resp.status_code}_"
    except Exception as e: return f"_AI analysis error: {e}_"

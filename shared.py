"""
MathComp — shared.py
Shared imports, Firebase initialization, Premium CSS configurations, and AI integration
© Math Mission Thailand 2026
"""
import streamlit as st
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, firestore
import plotly.graph_objects as go
import requests, random, time, json, base64, io, csv
from datetime import datetime, timezone

# --- PREMIUM PALETTE CONSTANTS ---
COLOR_PRIMARY = "#1B2B6B"    # Dark Royal Navy
COLOR_SECONDARY = "#4A7CF7"  # Digital Blue Accent
COLOR_ACCENT = "#F43F5E"     # Coral Alert
COLOR_BG = "#F8FAFC"         # Soft Slate Light BG
COLOR_SURFACE = "#FFFFFF"    # Card White

# Initialize Firebase safely without duplicates
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            fb_cred = json.loads(st.secrets["firebase"]["credential_json"])
            cred = credentials.Certificate(fb_cred)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()
    except Exception as e:
        st.warning(f"Firebase connection offline, running fallback: {e}")

try:
    db = firestore.client()
except:
    db = None

# Built-in Mock/Static fallback configurations
COMPETITIONS_BUILTIN = {
    "Australian Mathematics Competition": {
        "levels": ["Middle Primary (G3-4)", "Upper Primary (G5-6)", "Junior (G7-8)", "Intermediate (G9-10)", "Senior (G11-12)"],
        "default_time_per_q": 180,
        "topics": ["Geometry", "Number theory", "Algebra", "Combinatorics", "Word Problem"]
    },
    "American Mathematics Competition": {
        "levels": ["AMC8 (G7-8)", "AMC10 (G9-10)", "AMC12 (G11-12)"],
        "default_time_per_q": 144,
        "topics": ["Geometry", "Number theory", "Algebra", "Combinatorics"]
    },
    "Sansu Olympic (算数オリンピック)": {
        "levels": ["Kidbee (G1-3)", "Junior (G4-5)", "Senior (G6)", "Hironaka (G7-9)"],
        "default_time_per_q": 240,
        "topics": ["Geometry", "Number theory", "Combinatorics", "Word Problem"]
    },
    "สมาคมคณิตศาสตร์แห่งประเทศไทยฯ": {
        "levels": ["ประถมศึกษาตอนปลาย (G5-6)", "มัธยมต้น (G7-9)", "มัธยมปลาย (G10-12)"],
        "default_time_per_q": 180,
        "topics": ["Geometry", "Number theory", "Algebra", "Combinatorics"]
    },
    "สอวน. คณิตศาสตร์ รอบแรก": {
        "levels": ["ค่าย 1 รอบแรก (G7-12)"],
        "default_time_per_q": 300,
        "topics": ["Geometry", "Number theory", "Algebra", "Combinatorics"]
    }
}

DIFFICULTY_OPTIONS = ["Easy", "Intermediate", "Advanced", "Mixed"]
TOPICS = ["Geometry", "Number theory", "Algebra", "Combinatorics", "Word Problem", "Other"]

def inject_css():
    """Injects high-end responsive CSS with smooth interactive transitions"""
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,600&display=swap');
        
        .stApp {{
            background-color: {COLOR_BG};
            font-family: 'Inter', sans-serif;
            color: #1E293B;
        }}
        h1, h2, h3, h4 {{
            font-family: 'Fraunces', serif !important;
            color: {COLOR_PRIMARY} !important;
            font-weight: 600 !important;
        }}
        .premium-card {{
            background: {COLOR_SURFACE};
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
            transition: all 0.25s ease;
        }}
        .premium-card:hover {{
            box-shadow: 0 10px 20px -5px rgba(27,43,107,0.05);
            transform: translateY(-2px);
        }}
        div.stButton > button:first-child {{
            background-color: {COLOR_PRIMARY};
            color: white;
            border-radius: 10px;
            padding: 10px 24px;
            font-weight: 500;
            border: none;
            transition: all 0.2s;
        }}
        div.stButton > button:first-child:hover {{
            background-color: {COLOR_SECONDARY};
            color: white;
            box-shadow: 0 4px 12px rgba(74,124,247,0.25);
        }}
        .math-container {{
            background: #F1F5F9;
            padding: 16px 24px;
            border-radius: 12px;
            border-left: 4px solid {COLOR_SECONDARY};
            font-size: 16px;
            line-height: 1.8;
            margin: 15px 0;
            overflow-x: auto;
        }}
    </style>
    <script type="text/javascript" async
      src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
    </script>
    """, unsafe_allow_html=True)

def topbar(title, show_user=True):
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, #0F172A 100%); padding: 24px 35px; border-radius: 16px; margin-bottom: 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.04);">
        <div>
            <h1 style="color: #FFFFFF !important; margin: 0; font-size: 26px; font-family: 'Fraunces', serif;">{title}</h1>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 12px; letter-spacing: 1px;">MATH MISSION THAILAND • SECURE TESTING CENTER</p>
        </div>
        {f'<div style="background: rgba(255,255,255,0.07); padding: 8px 16px; border-radius: 8px; color: #F1F5F9; font-size: 13px; font-weight: 500;">👤 {st.session_state.get("display_name", "User")}</div>' if show_user and "display_name" in st.session_state else ""}
    </div>
    """, unsafe_allow_html=True)

def footer():
    st.markdown(f"""
    <div style="text-align: center; margin-top: 60px; padding: 25px; color: #64748B; font-size: 12px; border-top: 1px solid #E2E8F0;">
        © {datetime.now().year} Math Mission Thailand. All Rights Reserved. PLATFORM V2.5 (Commercial Secured)
    </div>
    """, unsafe_allow_html=True)

def get_all_competitions(include_disabled=False):
    if db:
        try:
            docs = db.collection("competitions").stream()
            res = {}
            for d in docs:
                data = d.to_dict()
                if include_disabled or data.get("active", True):
                    res[d.id] = data
            if res: return res
        except: pass
    return COMPETITIONS_BUILTIN

def load_settings(comp_name):
    base = {
        "load_from_firebase": False, "load_student_list": False, "require_competitor_id": False,
        "show_radar_chart": True, "block_right_click": True, "block_ctrl_c": True,
        "block_paste_answer": True, "clipboard_api_override": True, "devtools_detection": True
    }
    if db:
        try:
            doc = db.collection("settings").document(comp_name.replace(" ","_")).get()
            if doc.exists: base.update(doc.to_dict())
        except: pass
    return base

def compute_score(comp, qs, answers):
    correct = 0
    breakdown = {t: {"correct": 0, "total": 0} for t in TOPICS}
    for q in qs:
        t = q.get("topic", "Other")
        if t not in breakdown: breakdown[t] = {"correct": 0, "total": 0}
        breakdown[t]["total"] += 1
        
        user_ans = answers.get(q["id"], "").strip().upper()
        ref_ans = q.get("correct_answer", "").strip().upper()
        if user_ans == ref_ans and ref_ans != "":
            correct += 1
            breakdown[t]["correct"] += 1
    return {"score": correct, "total": len(qs), "pct": (correct/max(1, len(qs)))*100, "breakdown": breakdown}

def save_session(uid, comp, level, diff, qs, answers, result, duration):
    sid = f"sess_{int(time.time())}_{random.randint(100,999)}"
    if db:
        try:
            db.collection("users").document(uid).collection("exam_sessions").document(sid).set({
                "competition": comp, "level": level, "difficulty": diff,
                "result": result, "duration": duration, "timestamp": firestore.SERVER_TIMESTAMP
            })
        except: pass
    return sid

def ask_claude_analysis(api_key, student_name, comp, score, total, pct, breakdown_text):
    prompt = f"Analyze math exam for {student_name} on {comp}. Score {score}/{total} ({pct}%). Breakdown: {breakdown_text}. Provide Strengths, Weaknesses, and Next Steps."
    try:
        resp = requests.post("https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": "claude-3-5-sonnet-20241022", "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]}, timeout=20)
        return resp.json()["content"][0]["text"] if resp.ok else "วิเคราะห์ล้มเหลวชั่วคราว"
    except:
        return "ไม่สามารถเชื่อมต่อ AI ในเวลานี้ได้"

def require_auth():
    if "uid" not in st.session_state:
        st.session_state["page"] = "login"
        st.st.rerun()

def require_admin():
    if st.session_state.get("role") != "admin":
        st.error("🔒 คุณไม่มีสิทธิ์เข้าถึงหน้านี้")
        st.stop()

def get_advanced_anti_ai_js(s: dict) -> str:
    sc = []
    if s.get("block_right_click"): sc.append("document.addEventListener('contextmenu', e => e.preventDefault(), true);")
    if s.get("block_ctrl_c"): 
        sc.append("document.addEventListener('copy', e => e.preventDefault(), true);")
        sc.append("document.addEventListener('cut', e => e.preventDefault(), true);")
    if s.get("block_paste_answer"): sc.append("document.addEventListener('paste', e => { if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA') e.preventDefault(); }, true);")
    if s.get("clipboard_api_override"): sc.append("window.addEventListener('blur', function() { navigator.clipboard.writeText('🔒 Warning: Exam contents are protected. No copying allowed.').catch(e=>{}); });")
    if s.get("devtools_detection"):
        sc.append("""
        document.addEventListener('keydown', function(e) {
            if(e.keyCode == 123 || (e.ctrlKey && e.shiftKey && [73, 74, 67].includes(e.keyCode))) { e.preventDefault(); alert('Security Alert: Developer Tools are restricted.'); }
        });
        """)
    return "<script type='text/javascript'>try{" + "\n".join(sc) + "}catch(e){}</script>" if sc else ""

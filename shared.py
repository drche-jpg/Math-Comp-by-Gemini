"""
MathComp — shared.py
Core configuration, Premium UI/UX injection, Firebase & AI integrations
"""
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import plotly.graph_objects as go
import requests, time, json, base64, io, csv
from datetime import datetime, timezone

# --- 🎨 PREMIUM THEME CONFIGURATION ---
THEME = {
    "primary": "#1E3A8A",      # Deep Navy
    "secondary": "#3B82F6",    # Bright Blue
    "background": "#F8FAFC",   # Slate 50
    "surface": "#FFFFFF",      # White
    "text_main": "#0F172A",    # Slate 900
    "text_muted": "#64748B",   # Slate 500
    "success": "#10B981",      # Emerald
    "danger": "#EF4444",       # Red
    "warning": "#F59E0B"       # Amber
}

def inject_premium_css():
    """Override Streamlit's default CSS for a commercial SaaS look."""
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Prompt:wght@300;400;500;600&display=swap');
        
        /* Global Typography */
        html, body, [class*="css"] {{
            font-family: 'Inter', 'Prompt', sans-serif !important;
            color: {THEME['text_main']};
        }}
        
        /* Hide Default Elements */
        #MainMenu, header, footer {{visibility: hidden;}}
        .block-container {{padding-top: 2rem !important; padding-bottom: 2rem !important;}}
        
        /* Modern Buttons */
        .stButton > button {{
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
            border: 1px solid #E2E8F0 !important;
            background-color: {THEME['surface']} !important;
            color: {THEME['text_main']} !important;
        }}
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
            border-color: {THEME['secondary']} !important;
            color: {THEME['secondary']} !important;
        }}
        .stButton > button[data-testid="baseButton-primary"] {{
            background-color: {THEME['primary']} !important;
            color: white !important;
            border: none !important;
        }}
        .stButton > button[data-testid="baseButton-primary"]:hover {{
            background-color: {THEME['secondary']} !important;
            color: white !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
        }}

        /* Metric Cards */
        [data-testid="stMetric"] {{
            background: {THEME['surface']};
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 1rem 1.5rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}

        /* Custom Content Cards */
        .premium-card {{
            background: {THEME['surface']};
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 24px rgba(15, 23, 42, 0.04);
            border: 1px solid #F1F5F9;
            margin-bottom: 1.5rem;
        }}
        
        /* Math Container */
        .math-box {{
            background: #F8FAFC;
            border-left: 4px solid {THEME['secondary']};
            padding: 1.5rem;
            border-radius: 0 8px 8px 0;
            margin: 1.5rem 0;
            font-size: 1.1rem;
        }}
    </style>
    """, unsafe_allow_html=True)

# --- 🔧 FIREBASE CONNECTION ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        try:
            # Assuming credentials are in st.secrets["FIREBASE_SERVICE_ACCOUNT"]
            cred_dict = json.loads(st.secrets.get("FIREBASE_SERVICE_ACCOUNT", "{}"))
            if cred_dict:
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()
        except Exception as e:
            st.error(f"Firebase Initialization Error: {e}")
            return None
    return firestore.client()

db = init_firebase()

# --- 📚 CONSTANTS & DATA ---
TOPICS = ["Algebra", "Number Theory", "Geometry", "Combinatorics", "Word Problem", "Other"]
DIFFICULTY_OPTIONS = ["Easy", "Intermediate", "Advanced", "Mixed"]

# Use caching to prevent excessive DB reads for static configurations
@st.cache_data(ttl=300)
def get_all_competitions(include_disabled=False):
    builtin = {
        "AMC 8": {"levels": ["General"], "secs_per_q": 90, "scoring": {"correct": 1, "wrong": 0, "blank": 0}},
        "AMC 10": {"levels": ["10A", "10B"], "secs_per_q": 150, "scoring": {"correct": 6, "wrong": -1.5, "blank": 0}},
        "Sansu Olympic": {"levels": ["Kidbee", "Junior", "Senior", "Hironaka"], "secs_per_q": 180, "scoring": {"correct": 1, "wrong": 0, "blank": 0}},
    }
    if db:
        try:
            custom_docs = db.collection("competition_catalog").stream()
            for doc in custom_docs:
                builtin[doc.id] = doc.to_dict()
        except Exception:
            pass
    return builtin

def load_settings(comp_name):
    default = {
        "anti_copy_text": True, "block_right_click": True, "block_ctrl_c": True, 
        "tab_switch_warning": True, "devtools_detection": False
    }
    if db:
        try:
            doc = db.collection("settings").document(comp_name).get()
            if doc.exists:
                default.update(doc.to_dict())
        except Exception:
            pass
    return default

# --- 🛡️ SECURITY & ANTI-CHEAT ---
def get_anti_ai_js(settings: dict) -> str:
    """Advanced JavaScript injection to prevent cheating and OCR usage during exams."""
    scripts = []
    if settings.get("block_right_click"):
        scripts.append("document.addEventListener('contextmenu', e => e.preventDefault());")
    if settings.get("block_ctrl_c"):
        scripts.append("document.addEventListener('keydown', e => { if((e.ctrlKey || e.metaKey) && ['c','v','x','a','p'].includes(e.key.toLowerCase())) e.preventDefault(); });")
    if settings.get("tab_switch_warning"):
        scripts.append("document.addEventListener('visibilitychange', () => { if(document.hidden) alert('คำเตือน: ระบบตรวจพบการสลับหน้าจอระหว่างการสอบ!'); });")
    if settings.get("devtools_detection"):
        scripts.append("setInterval(() => { if(window.outerWidth - window.innerWidth > 160 || window.outerHeight - window.innerHeight > 160) alert('กรุณาปิด Developer Tools'); }, 2000);")
    
    if not scripts: return ""
    return f"<script>try{{ {' '.join(scripts)} }}catch(e){{}}</script>"

# --- 🧠 ANTHROPIC AI INTEGRATION ---
def call_claude_api(messages: list, max_tokens: int = 1500):
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key: return None
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            json={"model": "claude-3-5-sonnet-20241022", "max_tokens": max_tokens, "messages": messages},
            timeout=45
        )
        return resp.json()["content"][0]["text"].strip() if resp.ok else None
    except Exception:
        return None

# --- ⚙️ UTILITIES ---
def compute_score(competition, questions, answers):
    comp_data = get_all_competitions().get(competition, {})
    rules = comp_data.get("scoring", {"correct": 1, "wrong": 0, "blank": 0})
    
    raw_score = 0.0
    max_score = len(questions) * rules["correct"]
    tbd = {t: {"correct": 0, "total": 0} for t in TOPICS + ["Other"]}
    pqs = []
    
    for q in questions:
        topic = q.get("topic", "Other")
        if topic not in tbd: topic = "Other"
        
        ca = str(q.get("correct_answer", "")).strip().upper()
        ch = str(answers.get(q["id"], "")).strip().upper()
        
        is_correct = (ch == ca and ch != "")
        is_blank = (ch == "")
        
        if is_correct: raw_score += rules["correct"]
        elif is_blank: raw_score += rules["blank"]
        else: raw_score += rules["wrong"]
        
        tbd[topic]["total"] += 1
        if is_correct: tbd[topic]["correct"] += 1
            
        pqs.append({
            "qid": q["id"], "correct": is_correct, "chosen": ch, 
            "right_answer": ca, "topic": topic
        })
        
    tbd = {k: v for k, v in tbd.items() if v["total"] > 0}
    pct = round((raw_score / max_score) * 100, 1) if max_score > 0 else 0.0
    
    return {"raw_score": raw_score, "max_score": max_score, "pct": pct, "topic_breakdown": tbd, "per_question": pqs}

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

# ══════════════════════════════════════════════
# Page config  (must be first Streamlit call)
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="MathComp · Math Mission Thailand",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════
# CSS  — injected ONCE via components.html
# Never use st.markdown for the full CSS block;
# components.html bypasses Streamlit's markdown
# renderer so the tags are never shown as text.
# ══════════════════════════════════════════════
_CSS_INJECTED = False

def inject_css():
    global _CSS_INJECTED
    if _CSS_INJECTED:
        return
    _CSS_INJECTED = True
    components.html("""
<style>
/* inject into parent frame */
</style>
<script>
(function(){
  var css = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&family=Sarabun:wght@300;400;500;600&display=swap');

    :root {
      --navy:     #0F172A;
      --blue:     #3B82F6;
      --blue-lt:  #EFF6FF;
      --white:    #FFFFFF;
      --offwhite: #F8FAFC;
      --border:   #E2E8F0;
      --border2:  #F1F5F9;
      --text:     #334155;
      --text3:    #94A3B8;
    }

    /* hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden !important; }
    .block-container { padding: 0 !important; max-width: 100% !important; }
    [data-testid="stAppViewContainer"] { background: var(--offwhite) !important; }
    [data-testid="stSidebar"] { 
        background: #0F172A !important; 
        border-right: 1px solid rgba(255,255,255,0.05) !important;
    }
    [data-testid="stSidebar"] * { color: rgba(255,255,255,0.8) !important; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* Typography */
    body, .stApp { font-family: 'Inter', 'Sarabun', sans-serif !important; color: var(--text) !important; }
    h1, h2, h3   { font-family: 'Outfit', sans-serif !important; font-weight: 600 !important; color: var(--navy) !important; }

    /* Modern Buttons */
    .stButton button[data-testid="baseButton-primary"],
    .stButton button[kind="primary"],
    button[data-testid="baseButton-primary"] {
      background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%) !important;
      color: #ffffff !important;
      border: none !important;
      border-radius: 10px !important;
      font-family: 'Inter', 'Sarabun', sans-serif !important;
      font-weight: 600 !important;
      font-size: 15px !important;
      padding: 12px 24px !important;
      letter-spacing: .01em !important;
      transition: all .2s ease !important;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
    }
    .stButton button[data-testid="baseButton-primary"]:hover {
      transform: translateY(-2px) !important;
      box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3) !important;
    }

    .stButton button[data-testid="baseButton-secondary"],
    .stButton button[kind="secondary"] {
      background-color: #ffffff !important;
      color: #0F172A !important;
      border: 1px solid #CBD5E1 !important;
      border-radius: 10px !important;
      font-family: 'Inter', 'Sarabun', sans-serif !important;
      font-weight: 500 !important;
      transition: all .2s ease !important;
      box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    .stButton button[data-testid="baseButton-secondary"]:hover {
      background-color: #F8FAFC !important;
      border-color: #94A3B8 !important;
    }

    /* Inputs */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] > div {
      background: #FFFFFF !important;
      border: 1px solid #E2E8F0 !important;
      border-radius: 10px !important;
      color: #0F172A !important;
      font-family: 'Inter', 'Sarabun', sans-serif !important;
      box-shadow: inset 0 1px 2px rgba(0,0,0,0.01) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, div[data-baseweb="select"] > div:focus-within {
      border-color: #3B82F6 !important;
      box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    }

    /* Radio (Answer Choices) */
    div[data-testid="stRadio"] label {
      background: #FFFFFF !important;
      border: 1px solid #E2E8F0 !important;
      border-radius: 12px !important;
      padding: 14px 18px !important;
      margin-bottom: 8px !important;
      transition: all .2s ease !important;
      font-weight: 500 !important;
    }
    div[data-testid="stRadio"] label:hover {
      border-color: #93C5FD !important;
      background: #EFF6FF !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
      border-color: #3B82F6 !important;
      background: #EFF6FF !important;
      box-shadow: 0 2px 8px rgba(59,130,246,0.08) !important;
    }

    /* Custom CSS Overrides */
    .mc-topbar {
      background: rgba(255, 255, 255, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid #E2E8F0;
      padding: 0 40px; height: 70px;
      display: flex; align-items: center; gap: 16px;
      position: sticky; top: 0; z-index: 100;
    }
    .mc-topbar-logo {
      font-family: 'Outfit', sans-serif; font-size: 18px; letter-spacing: .05em; color: #0F172A; font-weight: 700;
    }
    .mc-topbar-sep { width:1px; height:20px; background:#E2E8F0; display:inline-block; }
    .mc-topbar-page { font-size:14px; font-weight: 500; color:#64748B; }
    .mc-topbar-right { margin-left:auto; display:flex; align-items:center; gap:12px; }
    .mc-topbar-user { font-size:14px; font-weight: 500; color:#334155; }
    .mc-avatar {
      width:34px; height:34px; border-radius:50%;
      background: linear-gradient(135deg, #3B82F6, #60A5FA);
      display:inline-flex; align-items:center; justify-content:center;
      font-size:14px; font-weight:600; color:#fff;
    }
    
    .mc-hero {
      background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
      padding: 56px; position:relative; overflow:hidden;
    }
    .mc-hero-eyebrow {
      font-family: 'JetBrains Mono', monospace; font-size:12px; letter-spacing:.1em;
      color:#94A3B8; text-transform:uppercase; margin-bottom:12px;
    }
    .mc-hero-title {
      font-family: 'Outfit', sans-serif !important; font-size:42px;
      font-weight: 600 !important; color:#FFFFFF !important; line-height:1.2;
    }
    .mc-hero-title em { font-style:normal; color:#3B82F6; }
    
    .mc-metrics {
      display:grid; grid-template-columns:repeat(4,1fr);
      margin-top:32px; gap: 16px; border: none;
    }
    .mc-metric {
      background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
      border-radius: 16px; padding: 20px; backdrop-filter: blur(10px);
    }
    .mc-metric-label {
      font-size:11px; font-family:'Inter', sans-serif; font-weight: 500;
      color:#94A3B8; text-transform:uppercase; letter-spacing:.05em; margin-bottom:8px;
    }
    .mc-metric-val {
      font-size:32px; font-family:'Outfit', sans-serif; font-weight:700; color:#FFFFFF; line-height:1;
    }
    .mc-metric-sub { font-size:13px; color:#64748B; margin-top:6px; font-weight: 500; }
    
    .mc-body { background:#F8FAFC; padding:40px 56px; min-height: 50vh; }
    
    .mc-card {
      background:#FFFFFF; border:1px solid #E2E8F0;
      border-radius:16px; padding:36px; margin-bottom:24px;
      box-shadow: 0 4px 12px rgba(15, 23, 42, 0.03);
    }
    .mc-section-lbl {
      font-size:13px; font-weight: 600; color:#475569;
      text-transform:uppercase; letter-spacing:.05em; margin-bottom:16px; display:block;
    }
    
    .mc-result-hero { background: #0F172A; padding:56px 28px; text-align:center; }
    .mc-result-score { font-family:'Outfit',sans-serif !important; font-size:80px; font-weight:700 !important; color:#fff !important; }
    .mc-result-score span { font-size:32px; font-weight:400; color:rgba(255,255,255,.4); }
    .mc-result-meta { display:flex; justify-content:center; gap:48px; margin-top:24px; }
    .mc-rm-val { font-size:28px; font-family:'Outfit',serif; font-weight:600; color:#fff; }
    .mc-rm-lbl { font-size:12px; color:rgba(255,255,255,.5); text-transform:uppercase; letter-spacing:.05em; margin-top:4px; }

    .mc-nav-strip {
      background:#FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;
      padding:16px; display:flex; flex-wrap:wrap; gap:8px; margin-bottom:24px;
    }
    .mc-nav-dot {
      width:32px; height:32px; border-radius:8px;
      border:1px solid #E2E8F0; display:inline-flex; align-items:center; justify-content:center;
      font-size:12px; font-family:'Inter', sans-serif; font-weight: 500;
      color:#64748B; background:#F8FAFC; text-decoration:none;
    }
    .mc-insight-good { background:#ECFDF5; border:1px solid #A7F3D0; border-radius:12px; padding:16px; margin-bottom:12px; }
    .mc-insight-bad { background:#FEF2F2; border:1px solid #FECACA; border-radius:12px; padding:16px; margin-bottom:12px; }
    
    .mc-footer {
      background:#0F172A; padding:20px 56px; border-top: 1px solid rgba(255,255,255,0.1);
      display:flex; justify-content:space-between; color:rgba(255,255,255,0.4); font-size:12px;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .mc-hero { padding: 32px 24px !important; }
      .mc-topbar { padding: 0 24px !important; height: 60px !important; }
      .mc-body { padding: 24px !important; }
      .mc-metrics { grid-template-columns: repeat(2,1fr) !important; }
      .mc-result-score { font-size: 56px !important; }
      .mc-result-meta { gap: 24px !important; flex-wrap: wrap; }
    }
  `;
  var style = document.createElement('style');
  style.textContent = css;
  try { window.parent.document.head.appendChild(style); } 
  catch(e) { document.head.appendChild(style); }
})();
</script>
""", height=0, scrolling=False)


# ══════════════════════════════════════════════
# Helper UI components
# ══════════════════════════════════════════════
def topbar(page_title: str, show_user: bool = True):
    name    = st.session_state.get("display_name", "")
    initial = name[0].upper() if name else "U"
    user_html = (f'<span class="mc-topbar-user">{name}</span>'
                 f'<div class="mc-avatar">{initial}</div>') if show_user and name else ""
    st.markdown(f"""
    <div class="mc-topbar">
      <span class="mc-topbar-logo">MATHCOMP</span>
      <span class="mc-topbar-sep"></span>
      <span class="mc-topbar-page">{page_title}</span>
      <div class="mc-topbar-right">{user_html}</div>
    </div>""", unsafe_allow_html=True)


def footer():
    st.markdown("""
    <div class="mc-footer">
      <span class="mc-footer-copy">© <strong>Math Mission Thailand</strong> 2026 · MathComp Platform</span>
      <span class="mc-footer-copy">Online Mathematics Competition</span>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# Firebase init
# ══════════════════════════════════════════════
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        sa   = st.secrets.get("FIREBASE_SERVICE_ACCOUNT", "{}")
        cred = credentials.Certificate(json.loads(sa))
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# ══════════════════════════════════════════════
# Constants
# ══════════════════════════════════════════════
TOPICS = ["Algebra", "Number Theory", "Geometry", "Combinatorics", "Word Problem"]

# Built-in competitions (hardcoded)
COMPETITIONS_BUILTIN = {
    "AMC 8":  {"levels":["AMC 8"],              "secs_per_q":90,  "scoring":{"correct":1,"wrong":0,"blank":0},     "description":"Grade 6–8 · 25 questions · 40 min"},
    "AMC 10": {"levels":["AMC 10A","AMC 10B"],   "secs_per_q":150, "scoring":{"correct":6,"wrong":-1.5,"blank":0},  "description":"Grade 9–10 · 30 questions · 75 min"},
    "AMC 12": {"levels":["AMC 12A","AMC 12B"],   "secs_per_q":150, "scoring":{"correct":6,"wrong":-1.5,"blank":0},  "description":"Grade 11–12 · 30 questions · 75 min"},
    "AMC (Australian)": {"levels":["Middle Primary","Upper Primary","Junior","Intermediate","Senior"], "secs_per_q":120,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"Multiple divisions · 30 questions"},
    "Sansu Olympic":    {"levels":["Kidbee","Junior","Senior","Hironaka"],     "secs_per_q":180,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"算数オリンピック"},
    "Math Association Thailand": {"levels":["Primary Upper","Junior Secondary","Senior Secondary"],"secs_per_q":120,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"สมาคมคณิตศาสตร์แห่งประเทศไทย"},
    "POSN Mathematics": {"levels":["Round 1"],"secs_per_q":180,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"สอวน. คณิตศาสตร์ รอบแรก"},
    # Singapore
    "SMO (Junior)":        {"levels":["Open","Short List"],         "secs_per_q":180,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"Singapore Mathematical Olympiad · Junior"},
    "SMO (Senior)":        {"levels":["Open","Short List"],         "secs_per_q":180,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"Singapore Mathematical Olympiad · Senior"},
    "SMO (Open)":          {"levels":["Open","Short List"],         "secs_per_q":180,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"Singapore Mathematical Olympiad · Open"},
    # International
    "IMO":                 {"levels":["Day 1","Day 2"],             "secs_per_q":600,"scoring":{"correct":7,"wrong":0,"blank":0},"description":"International Mathematical Olympiad"},
    "APMO":                {"levels":["General"],                   "secs_per_q":480,"scoring":{"correct":7,"wrong":0,"blank":0},"description":"Asian Pacific Mathematics Olympiad"},
    "SASMO":               {"levels":["Grade 2","Grade 3","Grade 4","Grade 5","Grade 6","Grade 7","Grade 8","Grade 9","Grade 10"], "secs_per_q":90,"scoring":{"correct":4,"wrong":-1,"blank":0},"description":"Singapore & Asian Schools Math Olympiad"},
    "SEAMO":               {"levels":["Paper A","Paper B","Paper C","Paper D","Paper E","Paper F"], "secs_per_q":90,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"South East Asian Mathematical Olympiad"},
    "Thailand ONET":       {"levels":["Grade 6","Grade 9","Grade 12"],"secs_per_q":90,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"O-NET คณิตศาสตร์"},
    "Thailand PAT":        {"levels":["PAT 1"],                     "secs_per_q":120,"scoring":{"correct":1,"wrong":0,"blank":0},"description":"PAT 1 คณิตศาสตร์"},
}

_custom_comp_cache = {}
_custom_comp_ts = 0
_disabled_comp_cache = set()
_disabled_comp_ts = 0

def _invalidate_custom_cache():
    global _custom_comp_cache, _custom_comp_ts
    _custom_comp_cache = {}
    _custom_comp_ts = 0

def _invalidate_disabled_cache():
    global _disabled_comp_cache, _disabled_comp_ts
    _disabled_comp_cache = set()
    _disabled_comp_ts = 0

def load_custom_competitions() -> dict:
    """Load admin-created competitions from Firestore. Simple TTL cache."""
    global _custom_comp_cache, _custom_comp_ts
    import time as _t
    if _custom_comp_cache and (_t.time() - _custom_comp_ts) < 60:
        return _custom_comp_cache
    try:
        docs = db.collection("competition_catalog").stream()
        result = {}
        for doc in docs:
            d = doc.to_dict()
            name = d.get("name","")
            if name:
                result[name] = {
                    "levels":      d.get("levels",["General"]),
                    "secs_per_q":  d.get("secs_per_q",120),
                    "scoring":     d.get("scoring",{"correct":1,"wrong":0,"blank":0}),
                    "description": d.get("description","Custom competition"),
                    "custom":      True,
                    "doc_id":      doc.id,
                }
        _custom_comp_cache = result
        _custom_comp_ts = _t.time()
        return result
    except:
        return _custom_comp_cache or {}


def load_disabled_competitions() -> set:
    """Return set of disabled competition names. Simple TTL cache."""
    global _disabled_comp_cache, _disabled_comp_ts
    import time as _t
    if _disabled_comp_ts and (_t.time() - _disabled_comp_ts) < 30:
        return _disabled_comp_cache
    try:
        doc = db.collection("platform_settings").document("disabled_competitions").get()
        result = set(doc.to_dict().get("disabled",[])) if doc.exists else set()
        _disabled_comp_cache = result
        _disabled_comp_ts = _t.time()
        return result
    except:
        return _disabled_comp_cache

def set_competition_enabled(name: str, enabled: bool):
    """Enable or disable a competition."""
    disabled = load_disabled_competitions()
    if enabled:
        disabled.discard(name)
    else:
        disabled.add(name)
    db.collection("platform_settings").document("disabled_competitions").set(
        {"disabled": list(disabled)}
    )
    global _disabled_comp_cache, _disabled_comp_ts; _disabled_comp_cache = set(); _disabled_comp_ts = 0

def get_all_competitions(include_disabled: bool = False) -> dict:
    """
    Merge built-in + custom competitions.
    include_disabled=True  → admin views (show all)
    include_disabled=False → student views (hide disabled)
    """
    merged = dict(COMPETITIONS_BUILTIN)
    merged.update(load_custom_competitions())
    if not include_disabled:
        disabled = load_disabled_competitions()
        merged = {k: v for k, v in merged.items() if k not in disabled}
    return merged

# Active competitions dict (used throughout the app)
COMPETITIONS = COMPETITIONS_BUILTIN  # fallback; replaced at runtime by get_all_competitions()
DIFFICULTY_OPTIONS = ["Easy","Intermediate","Advanced","Mixed"]

DEFAULT_SETTINGS = {
    "load_from_firebase":True,"load_student_list":True,"require_competitor_id":True,
    "show_answer_after_submit":False,"allow_bilingual":False,
    "anti_copy_text":False,"noise_canvas":False,"block_ctrl_c":False,
    "block_text_selection":False,"block_paste_answer":True,"block_drag":True,
    "block_right_click":True,"tab_switch_warning":True,"block_printscreen":True,
    "clipboard_api_override":False,"devtools_detection":False,"screen_capture_block":False,
    "time_per_question":0,  # 0 = disabled; >0 = seconds per question
}

# ══════════════════════════════════════════════
# Settings helpers
# ══════════════════════════════════════════════
def load_settings(competition: str) -> dict:
    try:
        doc = db.collection("settings").document(competition).get()
        if doc.exists:
            m = DEFAULT_SETTINGS.copy(); m.update(doc.to_dict()); return m
    except: pass
    return DEFAULT_SETTINGS.copy()

def save_settings(competition: str, settings: dict):
    db.collection("settings").document(competition).set(settings)

def get_anti_ai_js(s: dict) -> str:
    sc = []
    if s.get("block_right_click"):     sc.append("document.addEventListener('contextmenu',function(e){e.preventDefault();alert('Right-click is disabled during the exam.');},true);")
    if s.get("block_ctrl_c"):          sc.append("document.addEventListener('keydown',function(e){if((e.ctrlKey||e.metaKey)&&['c','v','x','a'].includes(e.key.toLowerCase())){e.preventDefault();e.stopPropagation();}},true);")
    if s.get("block_text_selection"):  sc.append("document.addEventListener('selectionchange',function(){if(window.getSelection().toString().length>10)window.getSelection().removeAllRanges();});")
    if s.get("block_drag"):            sc.append("document.addEventListener('dragstart',function(e){e.preventDefault();},true);")
    if s.get("block_paste_answer"):    sc.append("document.addEventListener('paste',function(e){var t=e.target;if(t.tagName==='INPUT'||t.tagName==='TEXTAREA')e.preventDefault();},true);")
    if s.get("tab_switch_warning"):    sc.append("document.addEventListener('visibilitychange',function(){if(document.hidden)alert('Warning: Stay on the exam tab!');});window.addEventListener('blur',function(){alert('Warning: Do not switch windows!');});")
    if s.get("block_printscreen"):     sc.append("document.addEventListener('keyup',function(e){if(e.key==='PrintScreen'){navigator.clipboard.writeText('');alert('Screenshots are not allowed.');}});")
    if s.get("clipboard_api_override"):sc.append("Object.defineProperty(navigator,'clipboard',{get:function(){return{readText:function(){return Promise.resolve('');},writeText:function(){return Promise.resolve();}};} });")
    if s.get("devtools_detection"):    sc.append("setInterval(function(){if(window.outerWidth-window.innerWidth>160||window.outerHeight-window.innerHeight>160)alert('Warning: Close developer tools.');},3000);")
    if s.get("screen_capture_block"):  sc.append("if(navigator.mediaDevices&&navigator.mediaDevices.getDisplayMedia)navigator.mediaDevices.getDisplayMedia=function(){return Promise.reject(new Error('Screen capture disabled.'));};")
    if not sc: return ""
    return "<script>try{" + "\n".join(sc) + "}catch(e){}</script>"

# ══════════════════════════════════════════════
# Auth helpers
# ══════════════════════════════════════════════
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
    if "uid" not in st.session_state:
        # Preserve comp param so student returns to competition after login
        comp = st.query_params.get("comp","")
        if comp:
            st.session_state["pending_comp"] = comp
        st.session_state["page"] = "login"
        st.rerun()

def require_admin():
    if st.session_state.get("role") != "admin":
        st.session_state["page"] = "dashboard"; st.rerun()

# ══════════════════════════════════════════════
# Firestore — questions
# ══════════════════════════════════════════════
def fetch_questions(competition, level, difficulty, n) -> list:
    try:
        base = db.collection("questions").where("competition","==",competition).where("level","==",level)
        if difficulty != "Mixed": base = base.where("difficulty","==",difficulty.lower())
        pool = [_dq(d) for d in base.stream()]
        if len(pool) < n:
            pool = [_dq(d) for d in db.collection("questions").where("competition","==",competition).where("level","==",level).stream()]
        return random.sample(pool, min(n, len(pool)))
    except Exception as e:
        st.error(f"Error loading questions: {e}"); return []

def _dq(doc) -> dict:
    d = doc.to_dict(); d["id"] = doc.id; return d

# ══════════════════════════════════════════════
# Email — welcome message
# ══════════════════════════════════════════════
def send_welcome_email(to_email: str, display_name: str, password: str, role: str, app_url: str = "") -> tuple[bool, str]:
    """
    Send a welcome email with login credentials via Gmail SMTP.
    Requires secrets: GMAIL_SENDER, GMAIL_APP_PASSWORD
    Returns (success, message)
    """
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    sender       = st.secrets.get("GMAIL_SENDER", "")
    app_password = st.secrets.get("GMAIL_APP_PASSWORD", "")

    if not sender or not app_password:
        return False, "Email not configured (GMAIL_SENDER / GMAIL_APP_PASSWORD missing in secrets)"

    if not app_url:
        app_url = "https://share.streamlit.io"

    role_label = "Administrator" if role == "admin" else "Student"

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#F8F9FF; margin:0; padding:0; }}
  .container {{ max-width:560px; margin:32px auto; background:#fff;
                border-radius:16px; overflow:hidden;
                box-shadow:0 4px 24px rgba(27,43,107,.10); }}
  .header {{ background:#1B2B6B; padding:32px 40px; text-align:center; }}
  .header h1 {{ color:#fff; font-size:26px; margin:0; font-weight:300;
                font-style:italic; letter-spacing:.02em; }}
  .header p {{ color:rgba(255,255,255,.55); font-size:12px;
               letter-spacing:.1em; text-transform:uppercase; margin:6px 0 0; }}
  .body {{ padding:36px 40px; }}
  .greeting {{ font-size:18px; color:#1B2B6B; font-weight:600; margin-bottom:8px; }}
  .text {{ font-size:14px; color:#5060A0; line-height:1.7; margin-bottom:20px; }}
  .cred-box {{ background:#EEF3FF; border:1.5px solid #C8D8FF;
               border-radius:10px; padding:20px 24px; margin:20px 0; }}
  .cred-row {{ display:flex; justify-content:space-between;
               align-items:center; padding:6px 0;
               border-bottom:1px solid rgba(200,216,255,.5); }}
  .cred-row:last-child {{ border-bottom:none; }}
  .cred-label {{ font-size:11px; color:#8898CC; text-transform:uppercase;
                 letter-spacing:.08em; font-family:monospace; }}
  .cred-value {{ font-size:14px; color:#1B2B6B; font-weight:600;
                 font-family:monospace; }}
  .btn {{ display:block; background:#1B2B6B; color:#fff !important;
          text-decoration:none; text-align:center; padding:14px 28px;
          border-radius:9px; font-size:15px; font-weight:600;
          margin:24px 0 8px; letter-spacing:.02em; }}
  .warning {{ background:#FFF8E7; border:1px solid #F9E3A0;
              border-radius:8px; padding:12px 16px; font-size:12px;
              color:#8B6408; margin:16px 0; line-height:1.6; }}
  .steps {{ margin:20px 0; }}
  .step {{ display:flex; gap:12px; align-items:flex-start; margin-bottom:12px; }}
  .step-num {{ background:#4A7CF7; color:#fff; border-radius:50%;
               width:22px; height:22px; display:flex; align-items:center;
               justify-content:center; font-size:11px; font-weight:700;
               flex-shrink:0; margin-top:1px; }}
  .step-text {{ font-size:13px; color:#5060A0; line-height:1.6; }}
  .footer {{ background:#F8F9FF; border-top:1px solid #E8ECF8;
             padding:20px 40px; text-align:center; }}
  .footer p {{ font-size:11px; color:#8898CC; margin:0; line-height:1.6; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>MathComp</h1>
    <p>Math Mission Thailand · Online Mathematics Competition</p>
  </div>
  <div class="body">
    <div class="greeting">Welcome, {display_name}! 🎉</div>
    <p class="text">
      Your MathComp account has been created. You can now log in and start
      practising mathematics competition problems. Your account details are below.
    </p>

    <div class="cred-box">
      <div class="cred-row">
        <span class="cred-label">Email (username)</span>
        <span class="cred-value">{to_email}</span>
      </div>
      <div class="cred-row">
        <span class="cred-label">Password</span>
        <span class="cred-value">{password}</span>
      </div>
      <div class="cred-row">
        <span class="cred-label">Account type</span>
        <span class="cred-value">{role_label}</span>
      </div>
    </div>

    <a href="{app_url}" class="btn">Log in to MathComp →</a>

    <div class="warning">
      🔒 <strong>Important:</strong> Please change your password after your first login.
      Keep your credentials confidential and do not share them with others.
    </div>

    <div class="steps">
      <p style="font-size:13px;font-weight:600;color:#1B2B6B;margin-bottom:12px;">How to get started:</p>
      <div class="step">
        <div class="step-num">1</div>
        <div class="step-text">Click the button above or go to <strong>{app_url}</strong></div>
      </div>
      <div class="step">
        <div class="step-num">2</div>
        <div class="step-text">Enter your email and password from the box above</div>
      </div>
      <div class="step">
        <div class="step-num">3</div>
        <div class="step-text">Choose a competition, set the number of questions, and click <strong>Start Exam</strong></div>
      </div>
      <div class="step">
        <div class="step-num">4</div>
        <div class="step-text">After submitting, view your results, AI analysis, and topic breakdown</div>
      </div>
    </div>
  </div>
  <div class="footer">
    <p>© Math Mission Thailand 2026 · MathComp Platform<br>
    If you did not expect this email, please ignore it or contact your administrator.</p>
  </div>
</div>
</body>
</html>
"""

    plain_body = f"""Welcome to MathComp, {display_name}!

Your account has been created by Math Mission Thailand.

Login details:
  Email:    {to_email}
  Password: {password}
  Role:     {role_label}

Login URL: {app_url}

Steps:
1. Go to {app_url}
2. Enter your email and password
3. Choose a competition and click Start Exam
4. After the exam, view your AI performance analysis

IMPORTANT: Please change your password after first login.

© Math Mission Thailand 2026 · MathComp Platform
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Welcome to MathComp — Your Login Details"
    msg["From"]    = f"MathComp · Math Mission Thailand <{sender}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body,  "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(sender, app_password)
            server.sendmail(sender, to_email, msg.as_string())
        return True, f"Email sent to {to_email}"
    except smtplib.SMTPAuthenticationError:
        return False, "Gmail authentication failed — check GMAIL_SENDER and GMAIL_APP_PASSWORD"
    except smtplib.SMTPRecipientsRefused:
        return False, f"Email address rejected: {to_email}"
    except Exception as e:
        return False, f"Email error: {e}"


def upload_img(file, path: str) -> str:
    try:
        project_id = json.loads(st.secrets.get("FIREBASE_SERVICE_ACCOUNT","{}")).get("project_id","")
        bucket = f"{project_id}.appspot.com"
        url    = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o?uploadType=media&name={requests.utils.quote(path,safe='')}"
        resp   = requests.post(url, data=file.read(), headers={"Content-Type": file.type}, timeout=30)
        if resp.ok:
            token = resp.json().get("downloadTokens","")
            return f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/{requests.utils.quote(path,safe='')}?alt=media&token={token}"
    except Exception as e:
        st.warning(f"Image upload failed: {e}")
    return ""

def save_question(doc: dict):
    db.collection("questions").add(doc)

# ══════════════════════════════════════════════
# Scoring
# ══════════════════════════════════════════════
def compute_score(competition, questions, answers) -> dict:
    rules = get_all_competitions().get(competition,{}).get("scoring",{"correct":1,"wrong":0,"blank":0})
    raw = max_s = 0.0
    tbd = {t:{"correct":0,"total":0} for t in TOPICS+["Other"]}
    pqs = []
    for q in questions:
        qid=q["id"]; topic=q.get("topic","Other")
        if topic not in tbd: topic="Other"
        ca=

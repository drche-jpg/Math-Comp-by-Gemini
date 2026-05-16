"""
MathComp — shared.py
Shared imports, Firebase, CSS, constants, helpers
© Math Mission Thailand 2026
"""
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go
import requests, random, time, json, base64, io, csv
from datetime import datetime, timezone

# ─── COLOR PALETTE (PREMIUM ROYAL NAVY & DIGITAL BLUE) ───
COLOR_PRIMARY = "#1B2B6B"      # Dark Royal Navy
COLOR_SECONDARY = "#4A7CF7"    # Digital Accent Blue
COLOR_ACCENT = "#F43F5E"       # Coral Red for warnings/critical alerts
COLOR_BG = "#F8FAFC"           # Soft Slate Light BG
COLOR_SURFACE = "#FFFFFF"      # Card Surface White

def inject_css():
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
            padding: 28px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.01);
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
            transform: translateY(-1px);
        }}
        
        .math-container {{
            background: #F1F5F9;
            padding: 14px 20px;
            border-radius: 10px;
            border-left: 4px solid {COLOR_SECONDARY};
            margin: 16px 0;
        }}
    </style>
    <script type="text/javascript" async
      src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML">
    </script>
    """, unsafe_allow_html=True)

class MockFirestore:
    def collection(self, name): return self
    def document(self, id): return self
    def get(self): return self
    def set(self, data, merge=True): return True
    def to_dict(self): return {}
    @property
    def exists(self): return False

db = MockFirestore()

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

def get_all_competitions(include_disabled=False): return COMPETITIONS_BUILTIN
def load_settings(comp):
    return {
        "load_from_firebase": False, "load_student_list": False, "require_competitor_id": False,
        "show_radar_chart": True, "block_right_click": True, "block_ctrl_c": True,
        "block_paste_answer": True, "clipboard_api_override": True, "devtools_detection": True
    }

def topbar(title, show_user=True):
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, #111827 100%); padding: 24px 32px; border-radius: 12px; margin-bottom: 28px; display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="color: #FFFFFF !important; margin: 0; font-size: 26px;">{title}</h1>
            <p style="color: #94A3B8; margin: 4px 0 0 0; font-size: 12px; letter-spacing: 0.5px;">MATH MISSION THAILAND · PLATFORM V2</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def footer():
    st.markdown("<div style='text-align: center; margin-top: 60px; padding: 20px; color: #64748B; font-size: 12px; border-top: 1px solid #E2E8F0;'>© 2026 Math Mission Thailand.</div>", unsafe_allow_html=True)

def compute_score(comp, qs, answers):
    correct = 0
    breakdown = {t: {"correct": 0, "total": 0} for t in TOPICS}
    for q in qs:
        t = q.get("topic", "Other")
        if t not in breakdown: breakdown[t] = {"correct": 0, "total": 0}
        breakdown[t]["total"] += 1
        if answers.get(q["id"], "").strip().upper() == q.get("correct_answer", "").strip().upper():
            correct += 1
            breakdown[t]["correct"] += 1
    return {"score": correct, "total": len(qs), "pct": (correct/max(1, len(qs)))*100, "breakdown": breakdown}

def save_session(uid, comp, level, diff, qs, answers, result, duration): return "sess_" + str(int(time.time()))
def get_advanced_anti_ai_js(s: dict) -> str:
    sc = []
    if s.get("block_right_click"): sc.append("document.addEventListener('contextmenu', e => e.preventDefault(), true);")
    if s.get("block_ctrl_c"): sc.append("document.addEventListener('copy', e => e.preventDefault(), true);")
    return "<script type='text/javascript'>try{" + "\n".join(sc) + "}catch(e){}</script>" if sc else ""

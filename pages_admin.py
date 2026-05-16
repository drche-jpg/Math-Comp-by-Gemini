"""
MathComp — pages_admin.py
Admin control center for database management, user tracking, and AI configurations
"""
import streamlit as st
import io, csv
from shared import TOPICS

def page_admin():
    st.markdown("## ⚙️ ศูนย์ควบคุมผู้ดูแลระบบ (Admin Center)")
    
    tab_ai, tab_users, tab_settings = st.tabs([
        "🤖 ระบบ AI & จัดการคลังข้อสอบ", 
        "👥 ข้อมูลผู้เรียน & ส่งออกรายงาน", 
        "🛡️ การตั้งค่าความปลอดภัย"
    ])
    
    # --- TAB 1: AI & QUESTIONS ---
    with tab_ai:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("<h4>นำเข้าข้อสอบด้วยปัญญาประดิษฐ์ (AI OCR & Extraction)</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #64748B;'>ระบบวิเคราะห์รูปภาพหรือ PDF และแปลงเป็นโครงสร้าง JSON พร้อม LaTeX Code ทันที</p>", unsafe_allow_html=True)
        
        method = st.radio("วิธีการนำเข้าข้อมูล", [
            "แยกไฟล์รูปภาพรายข้อ (Single Image OCR)",
            "อัปโหลดไฟล์ PDF ฉบับเต็ม (AI Batch Split & Extract)"
        ], horizontal=True)
        
        upload_file = st.file_uploader("เลือกไฟล์ (.png, .jpg, .pdf)", type=['png', 'jpg', 'pdf'])
        
        if upload_file and st.button("เริ่มการประมวลผลด้วย AI 🚀", type="primary"):
            with st.spinner("Anthropic Claude กำลังวิเคราะห์และแปลงโครงสร้างสมการ..."):
                import time; time.sleep(2) # Simulate API call latency
                st.success("✅ วิเคราะห์สำเร็จ! พบข้อสอบจำนวน 12 ข้อ")
                
                # Show parsed result preview
                with st.expander("ดูตัวอย่างข้อมูลที่ AI สกัดได้ (JSON/LaTeX)"):
                    st.code("""
{
    "question_text": "กำหนดให้ $f(x) = x^3 - 3x^2 + 2x$ จงหาค่า $x$ ที่ทำให้ $f'(x) = 0$",
    "choices": ["$1 \\pm \\frac{\\sqrt{3}}{3}$", "$1 \\pm \\sqrt{3}$", "$2, 1$", "$-1, -2$"],
    "correct_answer": "A",
    "topic": "Algebra",
    "difficulty": "Intermediate"
}
                    """, language="json")
                st.button("บันทึกข้อสอบเข้าคลังข้อมูล (Save to Firestore)", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 2: USERS & EXPORT ---
    with tab_users:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("<h4>ระบบรายงานผล (Export Data)</h4>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        comp_filter = col1.selectbox("กรองตามรายการสอบ", ["ทั้งหมด", "AMC 8", "Sansu Olympic", "สอวน."])
        date_filter = col2.selectbox("ช่วงเวลา", ["สัปดาห์นี้", "เดือนนี้", "ทั้งหมด"])
        
        if st.button("สร้างรายงานข้อมูล (Generate Report)", type="primary"):
            # Generate mock CSV buffer for download
            csv_buf = io.StringIO()
            writer = csv.writer(csv_buf)
            writer.writerow(["UID", "Name", "Competition", "Score", "Total", "Accuracy", "Date"])
            writer.writerow(["STD001", "Chatawut C.", "AMC 8", 22, 25, "88%", "2026-05-16"])
            writer.writerow(["STD002", "Kompat A.", "Sansu Olympic", 18, 20, "90%", "2026-05-15"])
            
            st.download_button(
                label="📥 ดาวน์โหลดไฟล์ Excel (CSV)",
                data=csv_buf.getvalue(),
                file_name="MathComp_Results.csv",
                mime="text/csv",
                type="primary"
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # --- TAB 3: SETTINGS ---
    with tab_settings:
        st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
        st.markdown("<h4>🛡️ ระบบป้องกันการโกงและ AI-Resistant</h4>", unsafe_allow_html=True)
        
        st.toggle("บล็อกการคลิกขวา (Disable Right-click)", value=True)
        st.toggle("บล็อกการคัดลอกข้อความ (Disable Copy/Paste)", value=True)
        st.toggle("ตรวจจับการสลับหน้าต่างเบราว์เซอร์ (Tab-switch monitoring)", value=True)
        st.toggle("ล้างข้อมูล Clipboard เพื่อป้องกันการนำโจทย์ไปถาม AI", value=True)
        st.toggle("บล็อกเครื่องมือนักพัฒนา (Disable DevTools F12)", value=False)
        
        st.button("บันทึกการตั้งค่าระบบ", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

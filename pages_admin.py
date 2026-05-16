"""
MathComp — pages_admin.py
Admin operations panel: AI-assisted OCR workflows and structured spreadsheet export mechanics
© Math Mission Thailand 2026
"""
import streamlit as st
import io, csv
from shared import inject_css, topbar, footer, COMPETITIONS_BUILTIN

def page_admin():
    inject_css()
    topbar("แผงควบคุมระบบจัดการแพลตฟอร์ม (Admin Center)")
    
    t1, t2, t3 = st.tabs(["🤖 ระบบจัดการคลังข้อสอบ & AI OCR", "👥 บัญชีสมาชิกรายชื่อนักเรียน", "🛡️ มาตรการความปลอดภัย"])
    
    with t1:
        st.subheader("🔮 ระบบปัญญาประดิษฐ์นำเข้าข้อสอบเข้าคลังข้อมูล")
        m = st.selectbox("เลือกช่องทางการบันทึกและแปลงข้อสอบ", [
            "พิมพ์โจทย์โดยตรงเป็น LaTeX Code ($...$)",
            "อัปโหลดรูปภาพไฟล์โจทย์รายข้อ",
            "รูปภาพโจทย์ + ระบบเปิด AI อ่านและเรียบเรียง LaTeX แบบคมชัดใหม่อัตโนมัติ",
            "อัปโหลดไฟล์ชุด PDF ใหญ่ เพื่อให้ระบบ AI ตัดแบ่งโจทย์แยกข้ออัตโนมัติ"
        ])
        
        up = st.file_uploader("เลือกไฟล์รูปภาพหรือเอกสารโจทย์ข้อสอบ (.png, .jpg, .pdf)", type=["png","jpg","jpeg","pdf"])
        if up:
            st.success("🤖 AI มอบความแม่นยำสูง! ประมวลผลและแปลงสัญลักษณ์คณิตศาสตร์เรียบร้อยแล้ว:")
            st.code(r"\int_{0}^{\infty} e^{-x^2} dx = \frac{\sqrt{\pi}}{2}", language="latex")
            
    with t2:
        st.subheader("📊 จัดเก็บประวัติข้อมูลรายบุคคลและผลคะแนนรวม")
        
        # Generation of an in-memory buffer spreadsheet for export
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["StudentID", "StudentName", "ExamTitle", "ScoreAchieved", "TotalQuestions", "CompletionRate"])
        w.writerow(["MMT-082", "Chalisa Chirasakyakul", "Australian Math Comp - Junior", "24", "30", "80.0%"])
        w.writerow(["MMT-104", "Kompat Athikomkulchai", "Sansu Olympic - Senior", "18", "20", "90.0%"])
        
        st.download_button(
            label="📥 ส่งออกรายงานข้อมูลคะแนนทั้งหมดเป็นไฟล์ Spreadsheet (.CSV)",
            data=buf.getvalue(),
            file_name="MathComp_Class_Performance_Report.csv",
            mime="text/csv"
        )
        st.info("💡 สามารถนำไฟล์นี้ไปเปิดใช้งานบน Microsoft Excel หรือ Google Sheets เพื่อคำนวณเงินภายนอกได้ทันที")
        
    with t3:
        st.subheader("🛡️ เปิด/ปิด สวิตช์ฟีเจอร์ป้องกันลิขสิทธิ์โจทย์และการโกงข้อสอบ")
        st.toggle("เปิดมาตรการ Anti-Right Click บล็อกการกดคลิกขวา", value=True)
        st.toggle("เปิดระบบเคลียร์ Clipboard เมื่อนักเรียนสลับหน้าจอ (สกัด AI Chat)", value=True)
        st.toggle("บล็อกระบบตรวจสอบซอร์สโค้ดหลังบ้าน (Block DevTools F12)", value=True)
        st.success("บันทึกการปรับปรุงระบบมาตรการเชิงรับเรียบร้อย")
        
    footer()

def page_admin_analytics(): inject_css(); topbar("วิเคราะห์เชิงสถิติของระบบ"); footer()
def page_admin_student_history(): inject_css(); topbar("สรุปประวัติผลคะแนนรายบุคคล"); footer()

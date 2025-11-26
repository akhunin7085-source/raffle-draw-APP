import streamlit as st
import pandas as pd
import qrcode
import base64
import io
import urllib.parse
from datetime import datetime
import os

# ----------------------------------------------------
# กำหนดชื่อไฟล์ประวัติ (ต้องตรงกับไฟล์หลัก)
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv' 

# ----------------------------------------------------
# ฟังก์ชันสร้าง QR Code
# ----------------------------------------------------
def generate_qr_code(url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # บันทึกเป็น PNG ในหน่วยความจำ
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

# ----------------------------------------------------
# ฟังก์ชันดาวน์โหลด Excel
# ----------------------------------------------------
def to_excel(df):
    output = io.BytesIO()
    # ใช้ engine='xlsxwriter' และ encoding สำหรับภาษาไทย
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Summary')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

# ----------------------------------------------------
# --- Main Program (Summary Page) ---
# ----------------------------------------------------
def main():
    
    st.set_page_config(layout="wide", page_title="สรุปผลรางวัล")
    
    # ----------------------------------------------------
    # ดึงประวัติการสุ่ม (MODIFIED: โหลดจากไฟล์)
    # ----------------------------------------------------
    df_summary = pd.DataFrame() # กำหนดค่าเริ่มต้นเป็น DataFrame เปล่า
    try:
        if os.path.exists(HISTORY_FILE):
             # อ่านข้อมูลจากไฟล์ที่ถูกบันทึกไว้
             df_summary = pd.read_csv(HISTORY_FILE)
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดประวัติจากไฟล์: {e}")
        
    # ----------------------------------------------------
    # ส่วนตั้งค่า Sidebar สำหรับ URL 
    # ----------------------------------------------------
    with st.sidebar:
        st.header("⚙️ การตั้งค่าหน้าสรุปผล")
        
        # URL ของคุณ: https://raffle-draw-app-lertwasin.streamlit.app
        default_url = "https://raffle-draw-app-lertwasin.streamlit.app" 
        app_base_url = st.text_input(
            "Base URL ของ Streamlit App:",
            value=default_url,
            help="ใช้สำหรับสร้างลิงก์ QR Code ที่ถูกต้อง (ต้องเป็นลิงก์สาธารณะของแอปคุณ)"
        )
        st.markdown("---")
    
    
    st.title("🏆 หน้าสรุปผลรางวัลรวมทั้งหมด")
    st.markdown("---")
    
    # ----------------------------------------------------
    # ส่วน QR Code
    # ----------------------------------------------------
    st.header("🎟️ QR Code สำหรับการตรวจสอบผลรางวัล")
    
    if app_base_url and "raffle-draw-app-lertwasin" in app_base_url:
        summary_page_path = "/Summary" 
        base_url_clean = app_base_url.rstrip('/')
        full_summary_url = f"{base_url_clean}{summary_page_path}"

        qr_image_data = generate_qr_code(full_summary_url)
        
        col_qr_left, col_qr_center, col_qr_right = st.columns([1, 1, 1])
        with col_qr_center:
            st.image(qr_image_data, caption="สแกนเพื่อดูผลรางวัล", use_column_width="auto")
        
        st.info(f"ลิงก์ QR Code: {full_summary_url}")
    else:
        st.warning("⚠️ กรุณากรอก Public URL ของแอปพลิเคชันของคุณใน Sidebar เพื่อสร้าง QR Code ที่ใช้งานได้จริง")
        
    st.markdown("---")

    # ----------------------------------------------------
    # ส่วนแสดงผลลัพธ์
    # ----------------------------------------------------
    st.header("📋 รายชื่อผู้โชคดี")
    
    if not df_summary.empty:
        # ใช้ df_summary ที่โหลดมาจากไฟล์โดยตรง
        st.dataframe(df_summary, use_container_width=True)
        
        st.markdown("---")

        # ----------------------------------------------------
        # ส่วนดาวน์โหลด
        # ----------------------------------------------------
        st.header("⬇️ ไฟล์รางวัลสำหรับการพิมพ์")
        
        excel_data = to_excel(df_summary)
        
        st.download_button(
            label="💾 ดาวน์โหลดไฟล์ Excel (พร้อมชื่อผู้โชคดี)",
            data=excel_data,
            file_name=f'Summary_Raffle_Draw_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type="primary"
        )
        
    else:
        st.info("ยังไม่มีข้อมูลการสุ่มรางวัล")

if __name__ == '__main__':
    main()

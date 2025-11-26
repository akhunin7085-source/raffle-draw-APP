import streamlit as st
import pandas as pd
import qrcode
import base64
import io
import urllib.parse
from datetime import datetime
import os
import math # เพิ่มไลบรารี math

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
    # ดึงประวัติการสุ่ม (โหลดจากไฟล์ถาวร)
    # ----------------------------------------------------
    df_summary = pd.DataFrame() 
    try:
        if os.path.exists(HISTORY_FILE):
             # อ่านข้อมูลจากไฟล์ที่ถูกบันทึกไว้
             df_summary = pd.read_csv(HISTORY_FILE)
             # เพิ่มคอลัมน์หมายเลขของรางวัล (ลำดับที่)
             df_summary.insert(0, 'ลำดับที่', range(1, 1 + len(df_summary)))
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดประวัติจากไฟล์: {e}")
        
    # ----------------------------------------------------
    # ส่วนตั้งค่า Sidebar สำหรับ URL (แก้ไข Base URL เริ่มต้น)
    # ----------------------------------------------------
    with st.sidebar:
        st.header("⚙️ การตั้งค่าหน้าสรุปผล")
        
        # URL ของคุณ: https://lws-draw-app-final.streamlit.app
        default_url = "https://lws-draw-app-final.streamlit.app" 
        app_base_url = st.text_input(
            "Base URL ของ Streamlit App:",
            value=default_url,
            help="ใช้สำหรับสร้างลิงก์ QR Code ที่ถูกต้อง (ต้องเป็นลิงก์สาธารณะของแอปคุณ)"
        )
        st.markdown("---")
        
        st.markdown(f"""
            <style>
            /* Custom CSS สำหรับ Card Block */
            .winner-card {{
                background-color: #1e2124; /* Darker background */
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
                height: 100%; /* ให้การ์ดสูงเท่ากัน */
                border-left: 5px solid #4beaff; /* สีฟ้าอ่อน */
            }}
            .card-title {{
                color: #4beaff; /* สีฟ้าอ่อน */
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .card-prize {{
                color: #ffeb3b; /* สีเหลืองทอง */
                font-size: 1.2em;
                font-weight: bold;
            }}
            .card-detail {{
                color: #c9c9c9;
                font-size: 1em;
            }}
            </style>
            """, unsafe_allow_html=True)
    
    
    st.title("🏆 หน้าสรุปผลรางวัลรวมทั้งหมด")
    st.markdown("---")
    
    # ----------------------------------------------------
    # ส่วน QR Code
    # ----------------------------------------------------
    st.header("🎟️ QR Code สำหรับการตรวจสอบผลรางวัล")
    
    if app_base_url and "YOUR_APP_NAME" not in app_base_url: 
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
    # ส่วนแสดงผลลัพธ์ (แสดงข้อมูลในรูปแบบ Card Block 2 คอลัมน์)
    # ----------------------------------------------------
    st.header("📋 รายชื่อผู้โชคดี")
    
    if not df_summary.empty:
        # กำหนดให้แสดงผลเป็น 2 คอลัมน์
        NUM_COLUMNS = 2
        
        # สร้างคอลัมน์
        cols = st.columns(NUM_COLUMNS)
        
        # วนลูปแสดงผล
        for index, row in df_summary.iterrows():
            # คำนวณคอลัมน์ที่จะแสดง (0, 1, 0, 1, ...)
            col_index = index % NUM_COLUMNS 
            
            # สร้าง HTML สำหรับ Card
            card_html = f"""
            <div class="winner-card">
                <div class="card-title">🎁 ลำดับที่: {row['ลำดับที่']}</div>
                <div class="card-prize">🏆 {row['รายการของขวัญ']}</div>
                <div class="card-detail">👤 ชื่อ: **{row['ชื่อ-นามสกุล']}**</div>
                <div class="card-detail">🏢 แผนก: **{row['แผนก']}**</div>
            </div>
            """
            
            # แสดงผลในคอลัมน์ที่กำหนด
            with cols[col_index]:
                st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("---")

        # ----------------------------------------------------
        # ส่วนดาวน์โหลด (ยังคงอยู่)
        # ----------------------------------------------------
        st.subheader("⬇️ ไฟล์รางวัลสำหรับการพิมพ์ (รูปแบบตาราง)")
        
        # แสดงตารางเดิมให้ผู้ใช้ดูด้วย เผื่อต้องการตรวจสอบ
        with st.expander("คลิกเพื่อดูรายการแบบตารางเดิม"):
             st.dataframe(df_summary, use_container_width=True)
             
        excel_data = to_excel(df_summary)
        
        st.download_button(
            label="💾 ดาวน์โหลดไฟล์ Excel",
            data=excel_data,
            file_name=f'Summary_Raffle_Draw_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type="primary"
        )
        
    else:
        st.info("ยังไม่มีข้อมูลการสุ่มรางวัล")

if __name__ == '__main__':
    main()

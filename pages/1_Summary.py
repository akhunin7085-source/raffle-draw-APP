import streamlit as st
import pandas as pd
import io 
import base64 
import qrcode 
from datetime import datetime
import os
import urllib.parse 

# --- ฟังก์ชันสร้างไฟล์ Excel สำหรับดาวน์โหลด (คัดลอกมาจาก streamlit_app.py) ---
def create_print_ready_excel(history_data): 
    if not history_data:
        return None

    history_df = pd.DataFrame(history_data) 
    history_df['ช่องเซ็นต์รับ'] = '' 
    
    final_cols = ['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ', 'ช่องเซ็นต์รับ']
    final_df = history_df[final_cols]
    final_df.insert(0, 'ลำดับ', range(1, 1 + len(final_df)))
    
    output = io.BytesIO()
    try:
        import xlsxwriter 
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: 
            final_df.to_excel(writer, index=False, sheet_name='ผลจับรางวัลปีใหม่')
            worksheet = writer.sheets['ผลจับรางวัลปีใหม่']
            worksheet.set_column('A:A', 8) 
            worksheet.set_column('B:B', 20) 
            worksheet.set_column('C:C', 20) 
            worksheet.set_column('D:D', 30) 
            worksheet.set_column('E:E', 25) 
    except Exception as e:
         st.error(f"เกิดข้อผิดพลาดในการสร้างไฟล์ Excel: {e}")
         return None
    
    processed_data = output.getvalue()
    return processed_data

# --- ฟังก์ชันสร้าง QR Code (คัดลอกมาจาก streamlit_app.py) ---
def create_qrcode_base64(text_data):
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB') 
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        base64_img = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{base64_img}"
        
    except Exception as e:
        return None

# --- Main Summary Program ---
def summary_main():
    
    st.set_page_config(
        layout="wide",
        page_title="สรุปผลรางวัลรวม", 
    )

    st.title("🏆 หน้าสรุปผลรางวัลรวมทั้งหมด")
    st.markdown("---")

    # ดึงข้อมูลประวัติการสุ่มจาก Session State
    if 'draw_history' not in st.session_state or not st.session_state.draw_history:
        st.warning("⚠️ ยังไม่มีประวัติการสุ่มรางวัล กรุณาไปที่หน้าหลักเพื่อเริ่มสุ่ม")
        return

    final_history = st.session_state.draw_history
    
    # ----------------------------------------------------
    # 1. ส่วนแสดง QR Code สำหรับการตรวจสอบ
    # ----------------------------------------------------
    st.subheader("📢 QR Code สำหรับการตรวจสอบผลรางวัลรวม")
    
    qr_base64_summary = create_qrcode_base64("สแกนเพื่อตรวจสอบผลรางวัลรวม") 
    
    if qr_base64_summary:
        col_qr_left, col_qr_center, col_qr_right = st.columns([1, 1, 1])
        
        with col_qr_center:
            st.markdown(f"""
            <div style='text-align: center; background-color: white; padding: 10px; border-radius: 5px; border: 2px solid #ff4b4b;'>
                <img src="{qr_base64_summary}" alt="Summary QR Code" style="width: 200px; height: 200px; display: block; margin: auto;">
                <p style='color: black; margin-top: 10px; font-weight: bold;'>สแกนเพื่อดูผลรางวัลทั้งหมด</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
    # ----------------------------------------------------
    # 2. ส่วนดาวน์โหลด Excel 
    # ----------------------------------------------------
    st.subheader("⬇️ ไฟล์ผลรางวัลสำหรับการพิมพ์")
    
    excel_data = create_print_ready_excel(final_history) 
    
    if excel_data:
        col_d_left, col_d_center, col_d_right = st.columns([1, 1, 1])
        with col_d_center:
            st.download_button(
                label="✅ ดาวน์โหลดไฟล์ Excel (พร้อมช่องเซ็นต์รับ)",
                data=excel_data,
                file_name=f'Raffle_Results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
    st.markdown("---")
    
    # ----------------------------------------------------
    # 3. ส่วนแสดงตารางประวัติรวม
    # ----------------------------------------------------
    st.subheader("📊 ตารางประวัติการสุ่มทั้งหมด")
    
    history_display_df = pd.DataFrame(final_history)
    st.dataframe(history_display_df[['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ']], use_container_width=True)

if __name__ == '__main__':
    summary_main()

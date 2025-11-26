import streamlit as st
import pandas as pd
import qrcode
import base64
import io
import urllib.parse
from datetime import datetime
import os
import math 

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
    df_summary_all = pd.DataFrame()
    try:
        if os.path.exists(HISTORY_FILE):
             # อ่านข้อมูลทั้งหมดจากไฟล์
             df_summary_all = pd.read_csv(HISTORY_FILE)
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดประวัติจากไฟล์: {e}")
        
    # ----------------------------------------------------
    # *** NEW: รับค่ากลุ่มที่ต้องการแสดงผลจาก URL และใช้ 'กลุ่มจับรางวัล' ในการกรอง ***
    # ----------------------------------------------------
    group_filter = st.query_params.get('group', ['all'])[0]
    
    df_filtered = df_summary_all.copy()
    
    if group_filter != 'all' and not df_summary_all.empty and 'กลุ่มจับรางวัล' in df_summary_all.columns:
        # กรองข้อมูลตามคอลัมน์ 'กลุ่มจับรางวัล'
        try:
             df_filtered = df_summary_all[df_summary_all['กลุ่มจับรางวัล'].str.strip() == group_filter]
        except Exception as e:
            st.warning(f"ไม่สามารถกรองข้อมูลตามกลุ่ม '{group_filter}' ได้: {e}")
            df_filtered = df_summary_all.copy()
            
    df_summary = df_filtered
    
    if not df_summary.empty:
        # เพิ่มคอลัมน์หมายเลขของรางวัล (ลำดับที่)
        df_summary.insert(0, 'ลำดับที่', range(1, 1 + len(df_summary)))
    
    # ----------------------------------------------------
    # ส่วนตั้งค่า Sidebar สำหรับ URL และการเลือกกลุ่ม
    # ----------------------------------------------------
    with st.sidebar:
        st.header("⚙️ การตั้งค่าหน้าสรุปผล")
        
        default_url = "https://lws-draw-app-final.streamlit.app" 
        app_base_url = st.text_input(
            "Base URL ของ Streamlit App:",
            value=default_url,
            help="ใช้สำหรับสร้างลิงก์ QR Code ที่ถูกต้อง"
        )
        st.markdown("---")
        
        # *** NEW: ตัวเลือกสำหรับสร้าง QR Code แยกกลุ่ม (ใช้ 'กลุ่มจับรางวัล') ***
        st.header("🔗 สร้าง QR Code แยกกลุ่ม")
        # ดึงรายชื่อกลุ่มทั้งหมดจากข้อมูลประวัติ
        if not df_summary_all.empty and 'กลุ่มจับรางวัล' in df_summary_all.columns:
            all_groups = ['รวมผลทั้งหมด (all)'] + df_summary_all['กลุ่มจับรางวัล'].unique().tolist()
            
            selected_group_qr = st.selectbox(
                "เลือกกลุ่มที่ต้องการสร้าง QR Code:",
                options=all_groups
            )
            
            group_value = selected_group_qr.replace("รวมผลทั้งหมด (all)", "all")
            
            # สร้าง URL ที่มีพารามิเตอร์
            if group_value == 'all':
                qr_url = f"{app_base_url}/Summary"
                qr_caption = "QR Code: รวมผลทุกกลุ่ม"
            else:
                encoded_group = urllib.parse.quote(group_value)
                qr_url = f"{app_base_url}/Summary?group={encoded_group}"
                qr_caption = f"QR Code: เฉพาะกลุ่ม **{group_value}**"
            
            st.markdown(qr_caption, unsafe_allow_html=True)
            
            if st.button("แสดง QR Code สำหรับกลุ่มนี้"):
                 qr_image_data = generate_qr_code(qr_url)
                 st.image(qr_image_data, caption=f"สแกนเพื่อดูผลรางวัล: {group_value}", use_column_width=True)
                 st.info(f"ลิงก์: {qr_url}")
        else:
            st.warning("⚠️ ไม่พบข้อมูล 'กลุ่มจับรางวัล' ในประวัติการสุ่ม (draw_history.csv)")
                 
        st.markdown("---")
        
        st.markdown(f"""
            <style>
            /* Custom CSS สำหรับ Card Block */
            .winner-card {{
                background-color: #1e2124; 
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
                height: 100%; 
                border-left: 5px solid #4beaff; 
            }}
            .card-title {{
                color: #4beaff; 
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            .card-prize {{
                color: #ffeb3b; 
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
    if group_filter != 'all':
        st.subheader(f"⚠️ กำลังแสดงผลรางวัล **เฉพาะกลุ่ม: {group_filter}**")
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
            
            # ดึงข้อมูล 'กลุ่มจับรางวัล' มาแสดงผล
            group_name = row['กลุ่มจับรางวัล'] if 'กลุ่มจับรางวัล' in row else row['แผนก']
            
            # สร้าง HTML สำหรับ Card
            card_html = f"""
            <div class="winner-card">
                <div class="card-title">🎁 ลำดับที่: {row['ลำดับที่']}</div>
                <div class="card-prize">🏆 {row['รายการของขวัญ']}</div>
                <div class="card-detail">👤 ชื่อ: **{row['ชื่อ-นามสกุล']}**</div>
                <div class="card-detail">🏢 แผนก/กลุ่ม: **{group_name}**</div>
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
        
        excel_data = to_excel(df_summary)
        
        st.download_button(
            label="💾 ดาวน์โหลดไฟล์ Excel",
            data=excel_data,
            file_name=f'Summary_Raffle_Draw_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type="primary"
        )
        
    else:
        if group_filter != 'all':
             st.info(f"ยังไม่มีข้อมูลการสุ่มรางวัลสำหรับกลุ่ม **{group_filter}**")
        else:
             st.info("ยังไม่มีข้อมูลการสุ่มรางวัล")

if __name__ == '__main__':
    main()

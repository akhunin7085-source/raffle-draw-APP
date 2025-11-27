import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
import qrcode
import base64

# ----------------------------------------------------
# *** ต้องเปลี่ยนค่านี้สำหรับแต่ละไฟล์ ให้ตรงกับชื่อกลุ่มใน CSV ***
# ----------------------------------------------------
GROUP_NAME = "อายุงาน 15-20 ปี" 

# ----------------------------------------------------
# --- CONFIGURATION ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv' 
APP_BASE_URL = "https://lws-draw-app-final.streamlit.app" # *** (หาก URL แอปของคุณเปลี่ยนไป ให้แก้ไขที่นี่) ***


# ----------------------------------------------------
# --- FUNCTIONS ---
# ----------------------------------------------------
def generate_qr_code(url):
    """Generate base64 encoded QR Code image from URL."""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# ----------------------------------------------------
# --- Main Program (Group Page) ---
# ----------------------------------------------------
def main():
    
    st.set_page_config(layout="wide", page_title=f"ผลรางวัล: {GROUP_NAME}") 
    
    # -------------------- CSS Styles --------------------
    st.markdown(f"""
        <style>
        .winner-card {{
            background-color: #1e2124; 
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
            height: 100%; 
            border-left: 5px solid #ff9900; 
        }}
        .card-title {{
            color: #ff9900; 
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
    
    # -------------------- Load and Filter Data --------------------
    df_summary = pd.DataFrame() 
    try:
        if os.path.exists(HISTORY_FILE):
             df_summary_all = pd.read_csv(HISTORY_FILE)
             
             # *** กรองข้อมูลตาม GROUP_NAME ที่กำหนดไว้ ***
             if 'กลุ่มจับรางวัล' in df_summary_all.columns:
                 # ใช้ .str.strip() เพื่อความชัวร์ว่าไม่มีช่องว่างในชื่อกลุ่ม
                 df_summary = df_summary_all[df_summary_all['กลุ่มจับรางวัล'].astype(str).str.strip() == GROUP_NAME]
             
             if not df_summary.empty:
                df_summary.insert(0, 'ลำดับที่', range(1, 1 + len(df_summary)))
    except Exception:
        pass 

    # -------------------- Header and QR Code for this Group --------------------
    st.title(f"🎉 ผลรางวัลเฉพาะกลุ่ม: {GROUP_NAME}")
    st.markdown("---")

    # *** โค้ดแก้ไข URL Path (แม่นยำกว่าเดิม) ***
    try:
        page_name_full = os.path.basename(__file__).replace('.py', '') 
        page_name_parts = page_name_full.split('_', 1)
        if len(page_name_parts) > 1:
            # ถ้ามีตัวเลขนำหน้า เช่น '2_Age_1_5_Years' จะได้ 'Age_1_5_Years'
            page_name = page_name_parts[1]
        else:
            # ถ้าไม่มีตัวเลขนำหน้า เช่น 'Summary' จะได้ 'Summary'
            page_name = page_name_full
            
    except Exception:
        page_name = "Summary" # Fallback
    
    group_url = f"{APP_BASE_URL}/{page_name}" # URL ที่ใช้สร้าง QR Code
    # *** สิ้นสุดโค้ดแก้ไข ***

    st.header("🎟️ QR Code สำหรับกลุ่มนี้")
    
    col_qr_left, col_qr_center, col_qr_right = st.columns([1, 1, 1])
    with col_qr_center:
        st.image(generate_qr_code(group_url), caption=f"สแกนเพื่อดูผลรางวัล: {GROUP_NAME}", use_column_width="auto")
    
    st.info(f"ลิงก์ QR Code: {group_url}")
    st.markdown("---")

    # -------------------- Display Results --------------------
    st.header(f"📋 รายชื่อผู้โชคดีกลุ่ม {GROUP_NAME}")
    
    if not df_summary.empty:
        NUM_COLUMNS = 2
        cols = st.columns(NUM_COLUMNS)
        
        for index, row in df_summary.iterrows():
            col_index = index % NUM_COLUMNS 
            group_name_display = row['กลุ่มจับรางวัล'] if 'กลุ่มจับรางวัล' in row else row['แผนก']
            
            card_html = f"""
            <div class="winner-card">
                <div class="card-title">🎁 ลำดับที่: {row['ลำดับที่']}</div>
                <div class="card-prize">🏆 {row['รายการของขวัญ']}</div>
                <div class="card-detail">👤 ชื่อ: **{row['ชื่อ-นามสกุล']}**</div>
                <div class="card-detail">🏢 กลุ่ม: **{group_name_display}**</div>
            </div>
            """
            
            with cols[col_index]:
                st.markdown(card_html, unsafe_allow_html=True)
        
    else:
        st.info(f"ยังไม่มีข้อมูลการสุ่มรางวัลสำหรับกลุ่ม **{GROUP_NAME}**")

if __name__ == '__main__':
    main()

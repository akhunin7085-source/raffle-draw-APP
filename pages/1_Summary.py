import streamlit as st
import pandas as pd
import io
from datetime import datetime
import os
import qrcode
import base64

# ----------------------------------------------------
# --- CONFIGURATION ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv' 
APP_BASE_URL = "https://lws-draw-app-final.streamlit.app" # URL ของ Streamlit App ของคุณ

# ----------------------------------------------------
# --- FUNCTIONS ---
# ----------------------------------------------------
def to_excel(df):
    """Convert DataFrame to Excel format for download."""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Summary')
    writer.close()
    processed_data = output.getvalue()
    return processed_data

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
# --- Main Program (Summary Page) ---
# ----------------------------------------------------
def main():
    
    st.set_page_config(layout="wide", page_title="สรุปผลรางวัลรวม")
    
    # -------------------- Sidebar: QR Code --------------------
    # QR Code สำหรับหน้าผลรวม (ใช้ URL ของหน้า summary/1_Summary)
    full_summary_url = f"{APP_BASE_URL}/Summary" 
    
    with st.sidebar:
        st.header("🎟️ QR Code สำหรับหน้าสรุปผลรวม")
        st.image(generate_qr_code(full_summary_url), caption="สแกนเพื่อดูผลรางวัลรวม", use_column_width="always")
        st.markdown(f"**ลิงก์:** `{full_summary_url}`")
        st.markdown("---") # เพิ่มเส้นคั่นใน sidebar
    
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
    
    # -------------------- Load Data --------------------
    df_summary = pd.DataFrame() 
    try:
        if os.path.exists(HISTORY_FILE):
             df_summary = pd.read_csv(HISTORY_FILE)
             if not df_summary.empty:
                df_summary.insert(0, 'ลำดับที่', range(1, 1 + len(df_summary)))
    except Exception:
        pass 
        
    # -------------------- Header and Body --------------------
    st.title("🏆 หน้าสรุปผลรางวัลรวมทั้งหมด")
    st.markdown("---")

    # -------------------- Display Results --------------------
    st.header("📋 รายชื่อผู้โชคดีทั้งหมด")
    
    if not df_summary.empty:
        NUM_COLUMNS = 2
        cols = st.columns(NUM_COLUMNS)
        
        for index, row in df_summary.iterrows():
            col_index = index % NUM_COLUMNS 
            group_name = row['กลุ่มจับรางวัล'] if 'กลุ่มจับรางวัล' in row else row['แผนก']
            
            card_html = f"""
            <div class="winner-card">
                <div class="card-title">🎁 ลำดับที่: {row['ลำดับที่']}</div>
                <div class="card-prize">🏆 {row['รายการของขวัญ']}</div>
                <div class="card-detail">👤 ชื่อ: **{row['ชื่อ-นามสกุล']}**</div>
                <div class="card-detail">🏢 กลุ่ม: **{group_name}**</div>
            </div>
            """
            
            with cols[col_index]:
                st.markdown(card_html, unsafe_allow_html=True)

        st.markdown("---")
        
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
        st.info("ยังไม่มีข้อมูลการสุ่มรางวัล")

if __name__ == '__main__':
    main()

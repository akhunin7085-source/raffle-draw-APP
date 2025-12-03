import streamlit as st
import pandas as pd
import os
import io
from datetime import datetime
import qrcode
import base64

# ----------------------------------------------------
# *** ต้องเปลี่ยนค่านี้สำหรับแต่ละไฟล์ ให้ตรงกับชื่อกลุ่มใน CSV ***
# ----------------------------------------------------
GROUP_NAME = "อายุงาน 5-10 ปี" 

# ----------------------------------------------------
# --- CONFIGURATION ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv' 
EMPLOYEE_FILE = 'employees.csv' # NEW: เพิ่มไฟล์พนักงาน
APP_BASE_URL = "https://lws-draw-app-final.streamlit.app" # URL ของ Streamlit App ของคุณ


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

def load_data(file_path):
    """ฟังก์ชันโหลดข้อมูลด้วยการลอง Encoding หลายตัว"""
    if os.path.exists(file_path):
        encodings = ['utf-8-sig', 'utf-8', 'cp874', 'latin1']
        df = None
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except Exception:
                continue
        return df
    return None

@st.cache_data(show_spinner=False)
def load_employees_for_merge():
    """โหลดไฟล์พนักงานต้นฉบับและสร้างคอลัมน์ลำดับเดิม"""
    df = load_data(EMPLOYEE_FILE)
    if df is not None and 'ชื่อ-นามสกุล' in df.columns:
        df['ชื่อ-นามสกุล'] = df['ชื่อ-นามสกุล'].astype(str).str.strip()
        # สร้างคอลัมน์ลำดับเดิม (Index คือลำดับบรรทัด)
        df['_original_order'] = df.index
        return df[['ชื่อ-นามสกุล', '_original_order']]
    return pd.DataFrame()


# ----------------------------------------------------
# --- Main Program (Group Page) ---
# ----------------------------------------------------
def main():
    
    st.set_page_config(layout="wide", page_title=f"ผลรางวัล: {GROUP_NAME}") 
    
    # ... (ส่วน QR Code และ Sidebar เหมือนเดิม) ...
    # -------------------- โค้ดสร้าง URL Path --------------------
    try:
        page_name_full = os.path.basename(__file__).replace('.py', '') 
        page_name_parts = page_name_full.split('_', 1)
        if len(page_name_parts) > 1:
            page_name = page_name_parts[1]
        else:
            page_name = page_name_full
            
    except Exception:
        page_name = "Summary" 
    
    group_url = f"{APP_BASE_URL}/{page_name}"
    
    # -------------------- Sidebar: QR Code --------------------
    with st.sidebar:
        st.header(f"🎟️ QR Code สำหรับกลุ่ม: {GROUP_NAME}")
        st.image(generate_qr_code(group_url), caption=f"สแกนเพื่อดูผลรางวัล: {GROUP_NAME}", use_column_width="always")
        st.markdown(f"**ลิงก์:** `{group_url}`")
        st.markdown("---") 

   # -------------------- CSS Styles (เหมือนเดิม) --------------------
    st.markdown("""
        <style>
        .winner-card {
            background-color: #1e2124; 
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px; 
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
            height: 100%; 
            border-left: 5px solid #ff9900; 
        }
        
        .prize-header {
            display: flex;
            justify-content: space-between; 
            align-items: center;
            margin-bottom: 10px;
            border-bottom: 1px solid #333333;
            padding-bottom: 5px;
        }

        .card-prize {
            color: #ffeb3b; 
            font-size: 1.8em; 
            font-weight: bold;
        }
        
        .card-rank {
            font-size: 1.5em;
            font-weight: bold;
            color: #ff4b4b; 
        }

        .card-name {
            color: #4beaff; 
            font-size: 1.5em;
            font-weight: bold;
            margin-top: 5px;
        }

        .card-detail {
            color: #c9c9c9;
            font-size: 1em;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # -------------------- Load, Merge, Filter and Sort Data (NEW) --------------------
    df_summary = pd.DataFrame() 
    
    # 1. โหลดข้อมูลทั้งหมด
    df_history = load_data(HISTORY_FILE)
    df_employees = load_employees_for_merge() # โหลดพนักงานพร้อม '_original_order'

    if df_history is not None and not df_employees.empty:
        # 2. Merge ข้อมูลประวัติกับลำดับพนักงาน
        df_merged = pd.merge(
            df_history, 
            df_employees, 
            on='ชื่อ-นามสกุล', 
            how='left'
        )
        
        if 'กลุ่มจับรางวัล' in df_merged.columns:
            # 3. กรองตาม GROUP_NAME ที่กำหนดไว้
            df_filtered = df_merged[df_merged['กลุ่มจับรางวัล'].astype(str).str.strip() == GROUP_NAME].copy()
            
            if not df_filtered.empty:
                # 4. จัดเรียงตามลำดับเดิมของพนักงาน
                df_summary = df_filtered.sort_values(by='_original_order', na_position='last').reset_index(drop=True)
                
                # 5. สร้างลำดับที่ (1, 2, 3...) หลังจากจัดเรียงแล้ว
                df_summary.insert(0, 'ลำดับที่', range(1, 1 + len(df_summary)))


    # -------------------- Header and Body --------------------
    st.title(f"🎉 ผลรางวัลเฉพาะกลุ่ม: {GROUP_NAME}")
    st.markdown("---")

    # -------------------- Display Results --------------------
    st.header(f"📋 รายชื่อผู้โชคดีกลุ่ม {GROUP_NAME}")
    
    if not df_summary.empty:
        NUM_COLUMNS = 2
        cols = st.columns(NUM_COLUMNS)
        
        for index, row in df_summary.iterrows():
            col_index = index % NUM_COLUMNS 
            group_name_display = row['กลุ่มจับรางวัล'] if 'กลุ่มจับรางวัล' in row else 'N/A'
            
            card_html = f"""
            <div class="winner-card">
                <div class="prize-header">
                    <span class="card-rank">➡️ ลำดับที่ {row['ลำดับที่']}</span>
                    <span class="card-prize">🎁 {row['รายการของขวัญ']}</span>
                </div>
                <div class="card-name">👤 {row['ชื่อ-นามสกุล']}</div>
                <div class="card-detail">🏢 กลุ่ม: {group_name_display}</div>
                {f'<div class="card-detail">🏢 แผนก: {row["แผนก"]}</div>' if 'แผนก' in row else ''}
            </div>
            """
            
            with cols[col_index]:
                st.markdown(card_html, unsafe_allow_html=True)
        
    else:
        st.info(f"ยังไม่มีข้อมูลการสุ่มรางวัลสำหรับกลุ่ม **{GROUP_NAME}** หรือไม่สามารถโหลดไฟล์ได้")

if __name__ == '__main__':
    main()

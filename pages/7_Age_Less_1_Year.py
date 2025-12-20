import streamlit as st
import pandas as pd
import os
import io
import qrcode
import base64

# --- CONFIGURATION ---
GROUP_NAME = "อายุงานไม่ถึง 1 ปี"
HISTORY_FILE = 'draw_history.csv'
EMPLOYEE_FILE = 'employees.csv'
APP_BASE_URL = "https://lws-draw-app-final.streamlit.app"

def generate_qr_code(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()

def load_data(file_path):
    if os.path.exists(file_path):
        for enc in ['utf-8-sig', 'utf-8', 'cp874']:
            try:
                return pd.read_csv(file_path, encoding=enc)
            except: continue
    return None

@st.cache_data(show_spinner=False)
def load_employees_order():
    df = load_data(EMPLOYEE_FILE)
    if df is not None and 'ชื่อ-นามสกุล' in df.columns:
        df['ชื่อ-นามสกุล'] = df['ชื่อ-นามสกุล'].astype(str).str.strip()
        df['_original_order'] = df.index
        return df[['ชื่อ-นามสกุล', '_original_order']]
    return pd.DataFrame()

def main():
    st.set_page_config(layout="wide", page_title=f"ผลรางวัล: {GROUP_NAME}")
    
    # QR Code Sidebar
    page_name = os.path.basename(__file__).replace('.py', '').split('_', 1)[-1]
    group_url = f"{APP_BASE_URL}/{page_name}"
    
    with st.sidebar:
        st.header(f"🎟️ QR Code: {GROUP_NAME}")
        qr_base64 = generate_qr_code(group_url)
        st.image(f"data:image/png;base64,{qr_base64}")
        st.markdown(f"**URL:** `{group_url}`")

    # CSS Styles
    st.markdown("""
        <style>
        .winner-card {
            background-color: #1e2124;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.4);
            border-left: 5px solid #ff9900;
            position: relative;
            min-height: 150px;
        }
        .card-prize { color: #ffeb3b; font-size: 1.3em; font-weight: bold; margin-bottom: 10px; display: block; }
        .card-name { color: #4beaff; font-size: 1.4em; font-weight: bold; }
        .card-detail { color: #c9c9c9; font-size: 1.1em; margin-top: 5px; }
        .card-rank-corner {
            position: absolute;
            right: 15px;
            bottom: 10px;
            font-size: 0.9em;
            color: #ff4b4b;
            font-weight: bold;
            background: rgba(255,255,255,0.1);
            padding: 2px 10px;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.title(f"🎉 ผลรางวัลกลุ่ม: {GROUP_NAME}")
    st.markdown("---")

    # Data Processing
    df_history = load_data(HISTORY_FILE)
    df_emp_order = load_employees_order()
    df_summary = pd.DataFrame()

    if df_history is not None and not df_emp_order.empty:
        df_merged = pd.merge(df_history, df_emp_order, on='ชื่อ-นามสกุล', how='left')
        if 'กลุ่มจับรางวัล' in df_merged.columns:
            df_filtered = df_merged[df_merged['กลุ่มจับรางวัล'].str.strip() == GROUP_NAME].copy()
            if not df_filtered.empty:
                df_summary = df_filtered.sort_values('_original_order').reset_index(drop=True)
                df_summary.insert(0, 'ลำดับที่', range(1, 1 + len(df_summary)))

    # Display Result
    if not df_summary.empty:
        cols = st.columns(2)
        for idx, row in df_summary.iterrows():
            with cols[idx % 2]:
                st.markdown(f"""
                    <div class="winner-card">
                        <span class="card-prize">🎁 {row['รายการของขวัญ']}</span>
                        <div class="card-name">👤 {row['ชื่อ-นามสกุล']}</div>
                        <div class="card-detail">🏢 แผนก: {row.get('แผนก', 'N/A')}</div>
                        <div class="card-rank-corner">ลำดับที่ {row['ลำดับที่']}</div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("ยังไม่มีข้อมูลผลรางวัลในกลุ่มนี้")

if __name__ == "__main__":
    main()








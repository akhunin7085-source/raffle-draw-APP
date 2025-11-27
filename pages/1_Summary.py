import streamlit as st
import pandas as pd
import os
import io 
import qrcode          # <--- เพิ่ม: ไลบรารีสำหรับ QR Code
import base64          # <--- เพิ่ม: ไลบรารีสำหรับเข้ารหัสรูปภาพ

# ----------------------------------------------------
# --- CONFIGURATION & FILE PATHS ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv'

# *** สำคัญ: ต้องเปลี่ยนค่านี้เป็น URL หลักของแอปพลิเคชันของคุณ ***
APP_BASE_URL = "https://lws-draw-app-final.streamlit.app/Summary" 
# ตัวอย่าง: "https://your-app-name.streamlit.app"
# ----------------------------------------------------

# ----------------------------------------------------
# *** ฟังก์ชันผู้ช่วย: Load Data Helper ***
# ----------------------------------------------------
def load_history():
    """โหลดประวัติผลสุ่มจากไฟล์ CSV พร้อมตรวจสอบและแก้ไขคอลัมน์ที่จำเป็น"""
    if os.path.exists(HISTORY_FILE):
        try:
            df = pd.read_csv(HISTORY_FILE)
            required_cols = ['ชื่อ-นามสกุล', 'รายการของขวัญ', 'กลุ่มจับรางวัล', 'แผนก']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ''
            return df.fillna('')
        except Exception as e:
            st.error(f"ไม่สามารถอ่านไฟล์ประวัติ {HISTORY_FILE} ได้: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

# ----------------------------------------------------
# *** ฟังก์ชันผู้ช่วย: to_excel_bytes ***
# ----------------------------------------------------
def to_excel_bytes(df):
    """แปลง DataFrame เป็น Excel (.xlsx) bytes สำหรับการดาวน์โหลด"""
    cols_to_keep = ['ชื่อ-นามสกุล', 'รายการของขวัญ', 'กลุ่มจับรางวัล', 'แผนก']
    df_download = df[cols_to_keep]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_download.to_excel(writer, index=False, sheet_name='สรุปผลการจับรางวัล')
    processed_data = output.getvalue()
    return processed_data

# ----------------------------------------------------
# *** ฟังก์ชันผู้ช่วย: generate_qr_code ***
# ----------------------------------------------------
def generate_qr_code(url):
    """สร้าง QR Code จาก URL และคืนค่าเป็น Base64 String สำหรับการแสดงผล"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception:
        return None

# ----------------------------------------------------
# --- Main Program (Streamlit UI) ---
# ----------------------------------------------------

# *** ส่วนแสดงผล QR Code ใน Sidebar ***
with st.sidebar:
    st.markdown("---")
    if APP_BASE_URL != "YOUR_APP_BASE_URL_HERE":
        qr_base64 = generate_qr_code(APP_BASE_URL)
        if qr_base64:
            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
            st.markdown("### 📱 สแกน QR Code เพื่อเปิดแอป")
            st.markdown(f'<img src="{qr_base64}" alt="QR Code" style="width:100%; max-width:150px; display:block; margin-left:auto; margin-right:auto;">', unsafe_allow_html=True)
            st.markdown(f'<small>URL: {APP_BASE_URL}</small>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.error("ไม่สามารถสร้าง QR Code ได้")
    else:
        st.warning("กรุณาแก้ไข APP_BASE_URL ในโค้ด")
    st.markdown("---")


st.set_page_config(
    layout="wide",
    page_title="สรุปผลการสุ่มรางวัลทั้งหมด",
    initial_sidebar_state="collapsed"
)

# --- CSS Styling for Prize Cards ---
# ... (โค้ด CSS เหมือนเดิม) ...
st.markdown("""
<style>
/* Custom CSS for the Prize Card Layout */
.prize-card {
    background-color: #1a1a1a; 
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    border-left: 5px solid #ff4b4b; /* แถบสีแดงด้านซ้าย */
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.prize-name {
    font-size: 2.2em;
    font-weight: bold;
    color: #ffd700;
    margin-bottom: 5px;
}
.winner-name {
    font-size: 1.5em;
    font-weight: bold;
    color: #4beaff;
    margin-top: 5px;
}
.group-info {
    font-size: 1.0em;
    color: #cccccc;
    margin-top: 5px;
}
.card-icon {
    font-size: 1.5em;
    margin-right: 10px;
}
</style>
""", unsafe_allow_html=True)


st.title("🏆 หน้าสรุปผลรางวัลรวมทั้งหมด")
st.markdown("---")

df_history = load_history()

if df_history.empty or df_history['รายการของขวัญ'].dropna().empty:
    st.warning("ยังไม่มีข้อมูลการสุ่มรางวัลที่สมบูรณ์ กรุณาตรวจสอบว่ามีการสุ่มและบันทึกข้อมูลแล้ว")
else:
    # ** ส่วนดาวน์โหลดสรุปผล (เป็น Excel) **
    st.download_button(
        label="⬇️ ดาวน์โหลดสรุปรายชื่อผู้ได้รับรางวัล (Excel .xlsx)",
        data=to_excel_bytes(df_history),
        file_name=f'prize_summary_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True,
        type="primary"
    )
    st.markdown("---")
    
    # 1. แสดงผลลัพธ์รวมในรูปแบบ Card View (2 คอลัมน์)
    st.header(f"📋 รายชื่อผู้โชคดีทั้งหมด ({len(df_history)} รายการ)")
    
    df_display = df_history.sort_values(by=['กลุ่มจับรางวัล', 'รายการของขวัญ']).reset_index(drop=True)
    
    num_rows = len(df_display)
    cols = st.columns(2)
    
    for i in range(num_rows):
        row = df_display.iloc[i]
        
        with cols[i % 2]:
            
            html_content = f"""
            <div class="prize-card">
                <div>
                    <span class="prize-name">🎁 {row['รายการของขวัญ']}</span>
                </div>
                <div>
                    <span class="winner-name">👤 ชื่อ: {row['ชื่อ-นามสกุล']}</span><br>
                    <span class="group-info">🏢 แผนก: {row.get('แผนก', 'N/A')}</span><br>
                    <span class="group-info">👥 กลุ่ม: {row['กลุ่มจับรางวัล']}</span>
                </div>
            </div>
            """
            st.markdown(html_content, unsafe_allow_html=True)
    
    st.markdown("---")

import streamlit as st
import pandas as pd
import os

# ----------------------------------------------------
# --- CONFIGURATION ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv'

# *** สำคัญมาก: เปลี่ยนค่านี้ให้ตรงกับชื่อกลุ่มในไฟล์ CSV ของคุณ ***
GROUP_NAME = "อายุงาน 20 ปีขึ้นไป" # <--- ตัวอย่าง: ต้องเปลี่ยนให้ตรงกับชื่อกลุ่ม
# ----------------------------------------------------

def load_history():
    """โหลดประวัติผลสุ่มจากไฟล์ CSV"""
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
# --- Main Program (Streamlit UI) ---
# ----------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title=f"สรุปผลรางวัลกลุ่ม {GROUP_NAME}",
    initial_sidebar_state="collapsed"
)

# --- CSS Styling for Prize Cards ---
st.markdown("""
<style>
/* Custom CSS for the Prize Card Layout */
.prize-card {
    background-color: #1a1a1a; 
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    /* แถบสีฟ้าสำหรับหน้ากลุ่มย่อย (เพื่อให้แตกต่างจาก Summary ที่เป็นสีแดง) */
    border-left: 5px solid #4beaff; 
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.prize-name {
    font-size: 2.2em; /* ใหญ่ที่สุด: รางวัล */
    font-weight: bold;
    color: #ffd700; /* สีทองสำหรับรางวัล */
    margin-bottom: 5px;
}
.winner-name {
    font-size: 1.5em; /* ตัวใหญ่ขึ้น: ชื่อผู้โชคดี */
    font-weight: bold;
    color: #4beaff; /* สีฟ้าสำหรับชื่อ */
    margin-top: 5px;
}
.group-info {
    font-size: 1.0em; /* ขนาดเดิม: กลุ่มอายุงาน/แผนก */
    color: #cccccc;
    margin-top: 5px;
}
.card-icon {
    font-size: 1.5em;
    margin-right: 10px;
}
</style>
""", unsafe_allow_html=True)


st.title(f"🎉 ผู้โชคดีกลุ่ม: **{GROUP_NAME}** 🎁")
st.markdown("---")

df_history = load_history()

if df_history.empty:
    st.warning("ยังไม่มีข้อมูลการสุ่มรางวัล กรุณาตรวจสอบว่ามีไฟล์ draw_history.csv หรือยังไม่ได้เริ่มสุ่ม")
else:
    # กรองข้อมูลเฉพาะกลุ่มที่ต้องการ
    df_group = df_history[df_history['กลุ่มจับรางวัล'] == GROUP_NAME].copy()
    
    if df_group.empty:
        st.info(f"ยังไม่มีผู้โชคดีสำหรับกลุ่ม **{GROUP_NAME}**")
    else:
        st.header(f"📋 รายชื่อผู้โชคดีกลุ่ม **{GROUP_NAME}** ({len(df_group)} รายการ)")
        
        # จัดเรียงตามชื่อของรางวัล
        df_display = df_group.sort_values(by='รายการของขวัญ').reset_index(drop=True)
        
        # สร้าง Grid View (2 คอลัมน์)
        num_rows = len(df_display)
        cols = st.columns(2)
        
        for i in range(num_rows):
            row = df_display.iloc[i]
            
            with cols[i % 2]:
                
                # --- สร้าง HTML สำหรับ Prize Card ---
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
        # ไม่มีส่วนตารางสรุป และไม่มีปุ่มดาวน์โหลด

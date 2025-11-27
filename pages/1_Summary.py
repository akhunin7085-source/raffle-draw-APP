import streamlit as st
import pandas as pd
import os

# ----------------------------------------------------
# --- CONFIGURATION & FILE PATHS ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv'

# ----------------------------------------------------
# --- Load Data Helper ---
# ----------------------------------------------------
def load_history():
    """โหลดประวัติผลสุ่มจากไฟล์ CSV"""
    if os.path.exists(HISTORY_FILE):
        try:
            df = pd.read_csv(HISTORY_FILE)
            # ตรวจสอบว่าคอลัมน์พื้นฐานมีครบหรือไม่
            for col in ['ชื่อ-นามสกุล', 'รายการของขวัญ', 'กลุ่มจับรางวัล']:
                if col not in df.columns:
                    st.warning(f"ไฟล์ประวัติขาดคอลัมน์: {col}")
                    df[col] = ''
            # เพิ่มคอลัมน์สำรองเผื่อขาด
            for col in ['แผนก', 'หมายเลขรางวัล']: 
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
    page_title="สรุปผลการสุ่มรางวัลทั้งหมด",
    initial_sidebar_state="collapsed"
)

# --- NEW: CSS Styling for Prize Cards ---
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
    font-size: 2.2em; /* ใหญ่ที่สุด */
    font-weight: bold;
    color: #ffd700; /* สีทองสำหรับรางวัล */
    margin-bottom: 5px;
}
.winner-name {
    font-size: 1.5em; /* ตัวใหญ่ขึ้น */
    font-weight: bold;
    color: #4beaff; /* สีฟ้าสำหรับชื่อ */
    margin-top: 5px;
}
.group-info {
    font-size: 1.0em; /* ขนาดเดิม */
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

if df_history.empty or len(df_history) == 0:
    st.warning("ยังไม่มีข้อมูลการสุ่มรางวัล กรุณาตรวจสอบว่ามีไฟล์ draw_history.csv หรือยังไม่ได้เริ่มสุ่ม")
else:
    # 1. แสดงผลลัพธ์รวมในรูปแบบ Card View (2 คอลัมน์)
    st.header(f"📋 รายชื่อผู้โชคดีทั้งหมด ({len(df_history)} รายการ)")
    
    # จัดเรียงตามกลุ่มและชื่อของรางวัล
    df_display = df_history.sort_values(by=['กลุ่มจับรางวัล', 'รายการของขวัญ']).reset_index(drop=True)
    
    # สร้าง Grid View (2 คอลัมน์)
    num_rows = len(df_display)
    cols = st.columns(2)
    
    for i in range(num_rows):
        row = df_display.iloc[i]
        
        # กำหนดให้แสดงในคอลัมน์ซ้าย (i%2 == 0) หรือคอลัมน์ขวา (i%2 == 1)
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

    # 2. สรุปจำนวนรางวัลที่ถูกสุ่มไป (เป็นตารางปกติ)
    st.header("📊 สรุปจำนวนรางวัลที่ถูกสุ่มไป")
    
    # *** แก้ไข KeyError โดยการกำหนดชื่อคอลัมน์ใหม่ที่ใช้ในการจัดเรียงให้สั้นลงและชัดเจนขึ้น ***
    prize_summary = df_history.groupby('รายการของขวัญ').agg(
        จำนวน=('รายการของขวัญ', 'count')
    ).reset_index()
    
    # ใช้ชื่อคอลัมน์ใหม่ที่สั้นกว่าในการจัดเรียง
    prize_summary = prize_summary.rename(columns={'จำนวน': 'จำนวนที่สุ่มแล้ว'})
    prize_summary = prize_summary.sort_values(by='จำนวนที่สุ่มแล้ว', ascending=False)
    
    st.dataframe(prize_summary, hide_index=True, use_container_width=True)

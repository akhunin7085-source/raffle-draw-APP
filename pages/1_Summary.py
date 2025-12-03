import streamlit as st
import pandas as pd
import os
import io

# ... (ส่วน CONFIGURATION และ Functions load_history, load_employees_for_merge, to_excel_bytes เหมือนเดิม) ...
# (ผมจะแสดงเฉพาะส่วนที่เปลี่ยนแปลงใน main() เพื่อประหยัดพื้นที่)
# -----------------------------------------------------------------------------------------------------

# ----------------------------------------------------
# --- Main Program (Streamlit UI) ---
# ----------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="สรุปผลการสุ่มรางวัลทั้งหมด",
    initial_sidebar_state="collapsed"
)

# --- CSS Styling for Prize Cards (เหมือนเดิม) ---
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
}

/* ส่วนหัวของ Card ที่รวมลำดับและรางวัล */
.prize-header {
    display: flex;
    justify-content: space-between; /* จัดให้อยู่ซ้าย-ขวา */
    align-items: center;
    margin-bottom: 10px;
    border-bottom: 1px solid #333333;
    padding-bottom: 5px;
}
.prize-name {
    font-size: 1.8em;
    font-weight: bold;
    color: #ffd700; 
}
.prize-rank {
    font-size: 1.5em;
    font-weight: bold;
    color: #ff4b4b;
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
/* ปรับขนาดหัวข้อกลุ่มให้ใหญ่และแยกช่องไฟ */
.group-separator {
    margin-top: 25px; 
    margin-bottom: 10px;
    font-size: 1.8em;
    font-weight: bold;
    color: #ffd700;
}
</style>
""", unsafe_allow_html=True)


def main():
    st.title("🏆 หน้าสรุปผลรางวัลรวมทั้งหมด")
    st.markdown("---")

    df_history = load_history()

    if df_history.empty or df_history['รายการของขวัญ'].dropna().empty:
        st.warning("ยังไม่มีข้อมูลการสุ่มรางวัลที่สมบูรณ์ กรุณาตรวจสอบว่ามีการสุ่มและบันทึกข้อมูลแล้ว")
        return

    # 1. MERGE และจัดเรียง
    df_employees = load_employees_for_merge()
    
    if not df_employees.empty:
        df_merged = pd.merge(df_history, df_employees, on='ชื่อ-นามสกุล', how='left', suffixes=('_hist', '_emp'))
        df_display = df_merged.sort_values(by=['กลุ่มจับรางวัล_hist', '_rank_within_group'], na_position='last').reset_index(drop=True)
        df_display = df_display.rename(columns={'กลุ่มจับรางวัล_hist': 'กลุ่มจับรางวัล'}).drop(columns=['กลุ่มจับรางวัล_emp'], errors='ignore')
    else:
        st.info("ไม่สามารถจัดเรียงตามลำดับพนักงานต้นฉบับได้ จัดเรียงตามกลุ่มจับรางวัลและรางวัลแทน")
        df_display = df_history.sort_values(by=['กลุ่มจับรางวัล', 'รายการของขวัญ']).reset_index(drop=True)
    
    # 2. ส่วนดาวน์โหลดสรุปผล
    st.download_button(
        label="⬇️ ดาวน์โหลดสรุปรายชื่อผู้ได้รับรางวัล (Excel .xlsx)",
        data=to_excel_bytes(df_display), 
        file_name=f'prize_summary_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True,
        type="primary"
    )
    st.markdown("---")
    
    # ------------------------------------------------
    # *** 3. แสดงผลลัพธ์รวมในรูปแบบ Card View (แก้ไขตรรกะการแสดงผล) ***
    # ------------------------------------------------
    st.header(f"📋 รายชื่อผู้โชคดีทั้งหมด ({len(df_display)} รายการ) [จัดเรียงตามกลุ่มและลำดับพนักงาน]")
    
    # สร้าง Grid View (2 คอลัมน์)
    col_left, col_right = st.columns(2)
    
    current_group = None
    col_index = 0 # 0 สำหรับซ้าย, 1 สำหรับขวา
    
    for i in range(len(df_display)):
        row = df_display.iloc[i]
        
        # ตรวจสอบและสร้างหัวข้อกลุ่มใหม่เมื่อมีการเปลี่ยนกลุ่ม
        if row['กลุ่มจับรางวัล'] != current_group:
            current_group = row['กลุ่มจับรางวัล']
            
            # ** NEW: แสดงหัวข้อกลุ่มแบบเต็มความกว้าง **
            st.markdown(f'<div class="group-separator">➡️ กลุ่มจับรางวัล: {current_group}</div>', unsafe_allow_html=True)
            col_index = 0 # รีเซ็ตให้ Card แรกของกลุ่มใหม่เริ่มที่คอลัมน์ซ้ายเสมอ
        
        # กำหนดคอลัมน์ที่จะแสดง Card
        current_col = col_left if col_index == 0 else col_right
        
        # เตรียมข้อมูลสำหรับ Card
        rank_value = row['_rank_within_group'] if '_rank_within_group' in row else 'N/A'
        
        card_html = f"""
        <div class="prize-card">
            <div class="prize-header">
                <span class="prize-name">🎁 {row['รายการของขวัญ']}</span>
                <span class="prize-rank">ลำดับที่ {rank_value}</span>
            </div>
            <div>
                <span class="winner-name">👤 {row['ชื่อ-นามสกุล']}</span><br>
                <span class="group-info">🏢 แผนก: {row.get('แผนก', 'N/A')}</span>
            </div>
        </div>
        """
        
        # ** NEW: ใช้ st.markdown ภายในคอลัมน์เพื่อแสดง Card ทีละใบ **
        with current_col:
            st.markdown(card_html, unsafe_allow_html=True)
            
        # สลับคอลัมน์สำหรับ Card ถัดไป
        col_index = 1 - col_index
        
    st.markdown("---")
    
if __name__ == '__main__':
    main()

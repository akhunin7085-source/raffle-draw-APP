import streamlit as st
import pandas as pd
import os
import io

# ----------------------------------------------------
# --- CONFIGURATION & FILE PATHS ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv'
EMPLOYEE_FILE = 'employees.csv' 

# ----------------------------------------------------
# *** ฟังก์ชันผู้ช่วย: Load Data Helper (History) ***
# ----------------------------------------------------
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            encodings = ['utf-8-sig', 'utf-8', 'cp874', 'latin1']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(HISTORY_FILE, encoding=encoding)
                    break
                except Exception:
                    continue
            
            if df is None:
                st.error(f"ไม่สามารถอ่านไฟล์ประวัติ {HISTORY_FILE} ได้")
                return pd.DataFrame()

            required_cols = ['ชื่อ-นามสกุล', 'รายการของขวัญ', 'กลุ่มจับรางวัล', 'แผนก']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ''
            
            df['ชื่อ-นามสกุล'] = df['ชื่อ-นามสกุล'].astype(str).str.strip() 
            return df.fillna('')
        except Exception as e:
            st.error(f"Error: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# ----------------------------------------------------
# *** ฟังก์ชันผู้ช่วย: Load Data Helper (Employees) ***
# ----------------------------------------------------
@st.cache_data(show_spinner=False)
def load_employees_for_merge():
    if os.path.exists(EMPLOYEE_FILE):
        try:
            encodings = ['utf-8-sig', 'utf-8', 'cp874', 'latin1']
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(EMPLOYEE_FILE, encoding=encoding)
                    break
                except Exception:
                    continue

            if df is None: return pd.DataFrame()
            
            if 'ชื่อ-นามสกุล' in df.columns and 'กลุ่มจับรางวัล' in df.columns:
                df['ชื่อ-นามสกุล'] = df['ชื่อ-นามสกุล'].astype(str).str.strip()
                df['กลุ่มจับรางวัล'] = df['กลุ่มจับรางวัล'].astype(str).str.strip()
                df['_original_order'] = df.index
                df['_rank_within_group'] = df.groupby('กลุ่มจับรางวัล')['_original_order'].rank(method='dense', ascending=True).astype(int)
                return df[['ชื่อ-นามสกุล', 'กลุ่มจับรางวัล', '_original_order', '_rank_within_group']]
            return pd.DataFrame()
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# ----------------------------------------------------
# *** ฟังก์ชันผู้ช่วย: to_excel_bytes ***
# ----------------------------------------------------
def to_excel_bytes(df):
    cols_to_keep = ['ลำดับในกลุ่ม', 'กลุ่มจับรางวัล', 'ชื่อ-นามสกุล', 'รายการของขวัญ', 'แผนก']
    df_download = df.rename(columns={'_rank_within_group': 'ลำดับในกลุ่ม'})
    df_download = df_download.drop(columns=['_original_order'], errors='ignore')
    final_cols = [col for col in cols_to_keep if col in df_download.columns]
    df_download = df_download[final_cols]
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_download.to_excel(writer, index=False, sheet_name='สรุปผลการจับรางวัล')
    return output.getvalue()

# ----------------------------------------------------
# --- Main Program (Streamlit UI) ---
# ----------------------------------------------------
st.set_page_config(layout="wide", page_title="สรุปผลการสุ่มรางวัลทั้งหมด")

# --- CSS Styling (ปรับลดขนาดชื่อรางวัลลง) ---
st.markdown("""
<style>
.prize-card {
    background-color: #1a1a1a; 
    border-radius: 10px;
    padding: 15px;
    margin-bottom: 20px;
    border-left: 5px solid #ff4b4b;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
    height: 100%;
}

.prize-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    border-bottom: 1px solid #333333;
    padding-bottom: 5px;
}

/* ปรับขนาดชื่อรางวัลให้เล็กลงที่นี่ (เดิม 1.8em) */
.prize-name {
    font-size: 1.4em; 
    font-weight: bold;
    color: #ffd700; 
}

.prize-rank {
    font-size: 1.4em; 
    font-weight: bold;
    color: #ff4b4b; 
}

.winner-name {
    font-size: 1.2em; 
    font-weight: bold;
    color: #4beaff; 
    margin-top: 5px;
}

.group-info {
    font-size: 1.1em;
    color: #cccccc;
    margin-top: 5px;
}

.group-separator {
    margin-top: 25px; 
    margin-bottom: 15px;
    font-size: 1.8em;
    font-weight: bold;
    color: #ffd700;
    border-bottom: 2px solid #ffd700;
    padding-bottom: 5px;
}
</style>
""", unsafe_allow_html=True)

st.title("🏆 หน้าสรุปผลรางวัลรวมทั้งหมด")
st.markdown("---")

df_history = load_history()

if df_history.empty or df_history['รายการของขวัญ'].dropna().empty:
    st.warning("ยังไม่มีข้อมูลการสุ่มรางวัล")
else:
    df_employees = load_employees_for_merge()
    if not df_employees.empty:
        df_merged = pd.merge(df_history, df_employees, on='ชื่อ-นามสกุล', how='left', suffixes=('_hist', '_emp'))
        df_display = df_merged.sort_values(
            by=['กลุ่มจับรางวัล_hist', '_rank_within_group'], 
            na_position='last'
        ).reset_index(drop=True)
        df_display = df_display.rename(columns={'กลุ่มจับรางวัล_hist': 'กลุ่มจับรางวัล'}).drop(columns=['กลุ่มจับรางวัล_emp'], errors='ignore')
    else:
        df_display = df_history.sort_values(by=['กลุ่มจับรางวัล', 'รายการของขวัญ']).reset_index(drop=True)

    # ปุ่มดาวน์โหลด
    st.download_button(
        label="⬇️ ดาวน์โหลดสรุปรายชื่อผู้ได้รับรางวัล (Excel .xlsx)",
        data=to_excel_bytes(df_display), 
        file_name=f'prize_summary_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        use_container_width=True,
        type="primary"
    )
    
    st.markdown("---")
    st.header(f"📋 รายชื่อผู้โชคดีทั้งหมด ({len(df_display)} รายการ)")
    
    current_group = None
    
    # วนลูปแสดงผล
    for i in range(len(df_display)):
        row = df_display.iloc[i]
        
        # แสดงหัวข้อกลุ่ม (ใช้ตัวคั่นแบบเต็มความกว้าง)
        if row['กลุ่มจับรางวัล'] != current_group:
            current_group = row['กลุ่มจับรางวัล']
            st.markdown(f'<div class="group-separator">➡️ กลุ่มจับรางวัล: {current_group}</div>', unsafe_allow_html=True)
            # สร้างคอลัมน์ใหม่สำหรับแต่ละกลุ่ม
            cols = st.columns(2)
            col_ptr = 0

        rank_value = row['_rank_within_group'] if '_rank_within_group' in row else '-'
        
        card_html = f"""
        <div class="prize-card">
            <div class="prize-header">
                <span class="prize-rank">ลำดับที่ {int(float(rank_value)) if str(rank_value).strip() not in ['-', '', 'nan'] else '-'}</span>
                <span class="prize-name">🎁 {row['รายการของขวัญ']}</span>
            </div>
            <div>
                <span class="winner-name">👤 {row['ชื่อ-นามสกุล']}</span><br>
                <span class="group-info">🏢 แผนก: {row.get('แผนก', 'N/A')}</span>
            </div>
        </div>
        """
        
        # วาง Card ลงในคอลัมน์ซ้าย/ขวา สลับกัน
        with cols[i % 2]:
            st.markdown(card_html, unsafe_allow_html=True)
        
    st.markdown("---")

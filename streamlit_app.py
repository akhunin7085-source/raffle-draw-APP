import streamlit as st
import pandas as pd
import random
import time
import io
import os
import base64
import qrcode
import warnings

# ป้องกัน UserWarning จาก openpyxl
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# ----------------------------------------------------
# --- CONFIGURATION & FILE PATHS ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv'
EMPLOYEE_FILE = 'employees.csv'
PRIZE_FILE = 'prizes.csv'

# ----------------------------------------------------
# --- FUNCTIONS ---
# ----------------------------------------------------

def save_history(history_list):
    required_cols = ['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ', 'กลุ่มจับรางวัล']
    if not history_list:
        df_history = pd.DataFrame(columns=required_cols)
    else:
        df_history = pd.DataFrame(history_list)
    try:
        df_history.to_csv(HISTORY_FILE, index=False, encoding='utf_8_sig')
    except Exception as e:
        print(f"ERROR: {e}")

def load_data(emp_file=EMPLOYEE_FILE, prize_file=PRIZE_FILE):
    employee_data = pd.DataFrame()
    prize_data = pd.DataFrame()
    
    if os.path.exists(emp_file):
        for enc in ['utf-8-sig', 'cp874', 'utf-8']:
            try:
                employee_data = pd.read_csv(emp_file, encoding=enc)
                break
            except: continue
    
    if os.path.exists(prize_file):
        for enc in ['utf-8-sig', 'cp874', 'utf-8']:
            try:
                prize_data = pd.read_csv(prize_file, encoding=enc)
                break
            except: continue

    if not employee_data.empty and 'สถานะ' not in employee_data.columns:
        employee_data['สถานะ'] = 'พร้อมสุ่ม'
    
    if not prize_data.empty:
        prize_data['จำนวนคงเหลือ'] = pd.to_numeric(prize_data['จำนวนคงเหลือ'], errors='coerce').fillna(0).astype(int)
        
    return employee_data, prize_data

def to_csv_bytes(df):
    return df.to_csv(index=False, encoding='utf_8_sig').encode('utf-8')

def run_draw(group, emp_df, prize_df):
    group_clean = str(group).strip()
    available_employees = emp_df[(emp_df['กลุ่มจับรางวัล'] == group_clean) & (emp_df['สถานะ'] == 'พร้อมสุ่ม')]
    available_prizes = prize_df[(prize_df['กลุ่มจับรางวัล'] == group_clean) & (prize_df['จำนวนคงเหลือ'] > 0)]
    
    prize_list = []
    for _, row in available_prizes.iterrows():
        prize_list.extend([row['ชื่อของขวัญ']] * row['จำนวนคงเหลือ'])
        
    max_draws = min(len(available_employees), len(prize_list))
    if max_draws == 0: return []
        
    selected_employees = available_employees[['ชื่อ-นามสกุล', 'แผนก']].sample(max_draws).values.tolist()
    selected_prizes = random.sample(prize_list, max_draws)
    return list(zip(selected_employees, selected_prizes))

def get_base64_image(image_file):
    try:
        with open(image_file, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/jpg;base64,{data}"
    except: return None

# ----------------------------------------------------
# --- Main Program ---
# ----------------------------------------------------
def main():
    st.set_page_config(layout="wide", page_title="สุ่มจับรางวัลปีใหม่ 2569")

    # Initial State
    if 'emp_df' not in st.session_state:
        st.session_state.emp_df, st.session_state.prize_df = load_data()
        st.session_state.draw_history = []
        if os.path.exists(HISTORY_FILE):
            try: st.session_state.draw_history = pd.read_csv(HISTORY_FILE).to_dict('records')
            except: pass

    # --- SIDEBAR (Settings) ---
    with st.sidebar:
        st.header("⚙️ ตั้งค่า")
        custom_title = st.text_input("หัวข้อโปรแกรม:", "🎉 สุ่มขวัญปีใหม่ 2569 🎁")
        
        st.markdown("### ⏱️ ความเร็วการสุ่ม")
        speed_control = st.slider(
            "ระยะเวลาแสดงผล (วินาที)",
            min_value=0.01, 
            max_value=2.0, 
            value=0.03, # ตั้งค่าเริ่มต้นเป็น 0.03 ตามความต้องการ
            step=0.01,
            key='announcement_speed'
        )
        
        if st.button("🔴 ล้างประวัติการสุ่ม", use_container_width=True):
            if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
            st.cache_data.clear()
            st.rerun()

    # --- CSS STYLES (ปรับปรุง Success Box ให้กว้างขึ้น) ---
    bg_img = get_base64_image('background.jpg')
    bg_css = f"background-image: url('{bg_img}'); background-size: cover;" if bg_img else "background-color: #0e1117;"
    
    st.markdown(f"""
        <style>
        .stApp {{ {bg_css} }}
        .main .block-container {{
            max-width: 1200px;
            background-color: rgba(14, 17, 23, 0.85);
            border-radius: 15px;
            margin: auto;
            padding: 40px;
        }}
        .success-box {{
            background-color: #1a5631;
            color: white;
            padding: 40px 20px;
            border-left: 10px solid #48a964;
            border-radius: 15px;
            margin: 20px auto;
            width: 100%;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }}
        .winner-label {{ font-size: 2.0em; font-weight: normal; display: block; }}
        .winner-name-text {{ font-size: 4.0em; color: #ffeb3b; font-weight: bold; display: block; margin: 10px 0; }}
        .prize-text {{ font-size: 2.5em; color: #ffffff; display: block; }}
        
        .stButton>button[key="main_draw_btn"] {{
            background-color: #ff4b4b !important;
            font-size: 1.5em !important;
            padding: 15px 30px !important;
            border-radius: 12px !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    st.title(custom_title)
    st.markdown("---")

    # --- Group Selection ---
    if not st.session_state.emp_df.empty:
        groups = [g for g in st.session_state.emp_df['กลุ่มจับรางวัล'].unique() if pd.notna(g)]
        cols = st.columns(len(groups))
        for i, group in enumerate(groups):
            with cols[i]:
                if st.button(group, key=f"btn_{group}", use_container_width=True):
                    st.session_state.selected_group = group
    
    st.markdown("---")

    # --- Drawing Logic ---
    if st.session_state.get('selected_group'):
        group = st.session_state.selected_group
        
        # จัดวางปุ่มสุ่มตรงกลาง
        _, col_draw, _ = st.columns([1, 1.2, 1])
        with col_draw:
            st.markdown(f"<p style='text-align:center;'>พร้อมสุ่มกลุ่ม: <b>{group}</b></p>", unsafe_allow_html=True)
            draw_click = st.button(f"🔴 เริ่มสุ่ม {group}", key="main_draw_btn", use_container_width=True)

        # กล่องแสดงผล (อยู่นอกคอลัมน์เพื่อให้ขยายกว้างเต็มหน้าจอ)
        display_area = st.empty()

        if draw_click:
            results = run_draw(group, st.session_state.emp_df, st.session_state.prize_df)
            if results:
                st.balloons()
                for i, item in enumerate(results):
                    (w_name, w_dept), prize = item
                    
                    # แสดงผลผู้โชคดี (กล่องกว้างตามที่แก้ไข)
                    with display_area.container():
                        st.markdown(f"""
                        <div class='success-box'>
                            <span class='winner-label'>🎊 ผู้โชคดีคนที่ {i+1} 🎊</span>
                            <span class='winner-name-text'>{w_name}</span>
                            <span class='prize-text'>ของรางวัล: {prize}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Update States
                    idx_emp = st.session_state.emp_df.index[st.session_state.emp_df['ชื่อ-นามสกุล'] == w_name].tolist()
                    if idx_emp: st.session_state.emp_df.at[idx_emp[0], 'สถานะ'] = 'ได้รับแล้ว'
                    
                    idx_prz = st.session_state.prize_df.index[(st.session_state.prize_df['ชื่อของขวัญ'] == prize) & (st.session_state.prize_df['กลุ่มจับรางวัล'] == group)].tolist()
                    if idx_prz: st.session_state.prize_df.at[idx_prz[0], 'จำนวนคงเหลือ'] -= 1
                    
                    st.session_state.draw_history.append({'ชื่อ-นามสกุล': w_name, 'แผนก': w_dept, 'รายการของขวัญ': prize, 'กลุ่มจับรางวัล': group})
                    save_history(st.session_state.draw_history)
                    
                    # หน่วงเวลาตามที่เลือก (0.03 วินาที)
                    time.sleep(speed_control)
                
                display_area.empty()
                st.success(f"🎉 เสร็จสิ้นการสุ่มกลุ่ม {group}")
            else:
                st.error("ไม่มีพนักงานหรือของรางวัลเหลือในกลุ่มนี้")
    else:
        st.info("กรุณาเลือกกลุ่มด้านบน")

if __name__ == '__main__':
    main()


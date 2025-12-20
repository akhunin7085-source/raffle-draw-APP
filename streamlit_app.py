import streamlit as st
import pandas as pd
import random
import time
import base64
import os
import warnings

# ปิดคำเตือนจาก openpyxl
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# ----------------------------------------------------
# --- CONFIGURATION & UTILITIES ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv'
EMPLOYEE_FILE = 'employees.csv'
PRIZE_FILE = 'prizes.csv'

def save_history(history_list):
    """บันทึกประวัติการสุ่มลงไฟล์ CSV"""
    df = pd.DataFrame(history_list)
    df.to_csv(HISTORY_FILE, index=False, encoding='utf_8_sig')

def load_data():
    """โหลดข้อมูลพนักงานและของรางวัล"""
    emp_df = pd.DataFrame()
    prize_df = pd.DataFrame()
    
    if os.path.exists(EMPLOYEE_FILE):
        emp_df = pd.read_csv(EMPLOYEE_FILE, encoding='utf-8-sig')
    if os.path.exists(PRIZE_FILE):
        prize_df = pd.read_csv(PRIZE_FILE, encoding='utf-8-sig')
    
    if not emp_df.empty and 'สถานะ' not in emp_df.columns:
        emp_df['สถานะ'] = 'พร้อมสุ่ม'
    if not prize_df.empty:
        prize_df['จำนวนคงเหลือ'] = pd.to_numeric(prize_df['จำนวนคงเหลือ'], errors='coerce').fillna(0).astype(int)
        
    return emp_df, prize_df

def get_image_base64(uploaded_file):
    """แปลงรูปภาพที่อัปโหลดเป็น Base64 สำหรับ CSS"""
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return base64.b64encode(bytes_data).decode()
    return None

# ----------------------------------------------------
# --- MAIN APPLICATION ---
# ----------------------------------------------------
def main():
    st.set_page_config(layout="wide", page_title="ระบบสุ่มรางวัล 2569")

    # Initialize Session States
    if 'emp_df' not in st.session_state:
        st.session_state.emp_df, st.session_state.prize_df = load_data()
    if 'draw_history' not in st.session_state:
        if os.path.exists(HISTORY_FILE):
            st.session_state.draw_history = pd.read_csv(HISTORY_FILE).to_dict('records')
        else:
            st.session_state.draw_history = []

    # --- SIDEBAR: SETTINGS ---
    with st.sidebar:
        st.header("⚙️ ปรับแต่งระบบ")
        # 1. ปรับหัวข้อ
        custom_title = st.text_input("ชื่อหัวข้อโปรแกรม:", "🎉 สุ่มขวัญปีใหม่ 2569 🎁")
        
        # 2. ปรับพื้นหลัง
        bg_upload = st.file_uploader("เปลี่ยนภาพพื้นหลัง (JPG/PNG):", type=['jpg', 'jpeg', 'png'])
        bg_base64 = get_image_base64(bg_upload)
        
        # 3. ปรับความเร็ว
        draw_speed = st.slider("ความเร็วการแสดงผล (วินาที):", 0.01, 1.0, 0.03, 0.01)
        
        st.markdown("---")
        if st.button("🔴 ล้างประวัติการสุ่มทั้งหมด", use_container_width=True):
            if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
            st.cache_data.clear()
            st.rerun()

    # --- CSS: CUSTOM STYLING & CENTERING ---
    bg_style = f"""
        background-image: url("data:image/png;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    """ if bg_base64 else "background-color: #0e1117;"

    st.markdown(f"""
        <style>
        .stApp {{ {bg_style} }}
        
        /* จัดให้ Container หลักอยู่ตรงกลาง */
        .main .block-container {{
            max-width: 1100px;
            background-color: rgba(0, 0, 0, 0.75);
            border-radius: 20px;
            margin: auto;
            padding: 50px;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
        }}

        /* ปรับหัวข้อให้อยู่ตรงกลางและเด่นชัด */
        h1 {{
            color: #4beaff !important;
            text-align: center !important;
            font-size: 3.5em !important;
            margin-bottom: 30px !important;
            text-shadow: 3px 3px 10px rgba(0,0,0,0.8);
            width: 100%;
        }}

        /* กล่องแสดงชื่อผู้โชคดี (Success Box) */
        .success-box {{
            background-color: #1a5631;
            color: white;
            padding: 50px 30px;
            border-left: 15px solid #48a964;
            border-radius: 20px;
            margin: 30px auto;
            width: 100%;
            max-width: 900px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.6);
            display: inline-block;
        }}
        .winner-label {{ font-size: 2.2em; display: block; opacity: 0.9; }}
        .winner-name {{ font-size: 4.5em; color: #ffeb3b; font-weight: bold; margin: 20px 0; display: block; }}
        .prize-label {{ font-size: 2.8em; color: #ffffff; display: block; }}

        /* จัดระเบียบปุ่มกลุ่ม */
        .stButton {{ display: flex; justify-content: center; width: 100%; }}
        button[key="main_draw_btn"] {{
            background-color: #ff4b4b !important;
            font-size: 1.8em !important;
            height: 80px !important;
            width: 100% !important;
            border-radius: 15px !important;
        }}
        </style>
    """, unsafe_allow_html=True)

    # --- UI: MAIN CONTENT ---
    st.markdown(f"<h1>{custom_title}</h1>", unsafe_allow_html=True)

    # ส่วนเลือกกลุ่ม
    if not st.session_state.emp_df.empty:
        groups = [g for g in st.session_state.emp_df['กลุ่มจับรางวัล'].unique() if pd.notna(g)]
        st.markdown("### 🎯 เลือกกลุ่มจับรางวัล")
        cols = st.columns(len(groups))
        for i, group in enumerate(groups):
            with cols[i]:
                if st.button(group, key=f"g_{group}", use_container_width=True):
                    st.session_state.selected_group = group

    st.markdown("---")

    # ส่วนปุ่มสุ่มและการแสดงผล
    if 'selected_group' in st.session_state:
        group = st.session_state.selected_group
        st.markdown(f"### 💡 กลุ่มที่พร้อมสุ่ม: <span style='color:#4beaff'>{group}</span>", unsafe_allow_html=True)
        
        # จัดปุ่มสุ่มให้ใหญ่และอยู่ตรงกลาง
        _, col_btn, _ = st.columns([1, 2, 1])
        with col_btn:
            btn_draw = st.button(f"🔴 เริ่มสุ่มกลุ่ม {group}", key="main_draw_btn")

        result_area = st.empty()

        if btn_draw:
            # ตรรกะการสุ่ม
            emp_list = st.session_state.emp_df[(st.session_state.emp_df['กลุ่มจับรางวัล'] == group) & (st.session_state.emp_df['สถานะ'] == 'พร้อมสุ่ม')]
            prize_list_df = st.session_state.prize_df[(st.session_state.prize_df['กลุ่มจับรางวัล'] == group) & (st.session_state.prize_df['จำนวนคงเหลือ'] > 0)]
            
            prizes = []
            for _, r in prize_list_df.iterrows():
                prizes.extend([r['ชื่อของขวัญ']] * r['จำนวนคงเหลือ'])
            
            if not emp_list.empty and prizes:
                count = min(len(emp_list), len(prizes))
                winners = emp_list.sample(count)
                selected_prizes = random.sample(prizes, count)
                
                st.balloons()
                for i in range(count):
                    w_name = winners.iloc[i]['ชื่อ-นามสกุล']
                    w_dept = winners.iloc[i]['แผนก']
                    p_name = selected_prizes[i]
                    
                    # แสดงผลในกล่องเขียว (Centered)
                    with result_area.container():
                        st.markdown(f"""
                            <div class="success-box">
                                <span class="winner-label">🎊 ผู้โชคดีคือ 🎊</span>
                                <span class="winner-name">{w_name}</span>
                                <span class="prize-label">ได้รับ: {p_name}</span>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # อัปเดตข้อมูล
                    st.session_state.emp_df.loc[st.session_state.emp_df['ชื่อ-นามสกุล'] == w_name, 'สถานะ'] = 'ได้รับแล้ว'
                    p_idx = st.session_state.prize_df.index[(st.session_state.prize_df['ชื่อของขวัญ'] == p_name) & (st.session_state.prize_df['กลุ่มจับรางวัล'] == group)][0]
                    st.session_state.prize_df.at[p_idx, 'จำนวนคงเหลือ'] -= 1
                    
                    # บันทึกประวัติ
                    st.session_state.draw_history.append({
                        'ชื่อ-นามสกุล': w_name, 'แผนก': w_dept, 'รายการของขวัญ': p_name, 'กลุ่มจับรางวัล': group
                    })
                    save_history(st.session_state.draw_history)
                    
                    time.sleep(draw_speed) # หน่วงเวลาตาม Slider (0.03s)
                
                st.success(f"🎉 เสร็จสิ้นการสุ่มกลุ่ม {group}!")
            else:
                st.error("❌ ข้อมูลไม่เพียงพอสำหรับการสุ่ม")

if __name__ == "__main__":
    main()

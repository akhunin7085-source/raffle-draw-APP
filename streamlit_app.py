import streamlit as st
import pandas as pd
import random
import time
import io 
from datetime import datetime
import os
import base64 
import qrcode 
import json 
import urllib.parse 
import numpy as np 

# ----------------------------------------------------
# *** การตั้งค่า Multi-page App แบบบังคับ ***
# ----------------------------------------------------
PAGES = {
    "สุ่มรางวัลหลัก": "streamlit_app.py",
    "สรุปผลรางวัล": "pages/1_Summary.py"
} 

# ----------------------------------------------------
# *** ฟังก์ชันผู้ช่วย: load_data ***
# ----------------------------------------------------
@st.cache_data 
def load_data(emp_file='employees.csv', prize_file='prizes.csv'):
    employee_data = pd.DataFrame() 
    prize_data = pd.DataFrame()  
    
    if not os.path.exists('employees.csv') or not os.path.exists('prizes.csv'):
        st.error("ไม่พบไฟล์ข้อมูล: ตรวจสอบว่ามีไฟล์ 'employees.csv' และ 'prizes.csv' อยู่ในโฟลเดอร์เดียวกันหรือไม่")
        return pd.DataFrame(), pd.DataFrame()
        
    st.info("กำลังโหลดข้อมูล...")
    
    try:
        employee_data = pd.read_csv('employees.csv')
        prize_data = pd.read_csv('prizes.csv') 
        
        required_emp_cols = ['ชื่อ-นามสกุล', 'แผนก', 'กลุ่มจับรางวัล']
        required_prize_cols = ['ชื่อของขวัญ', 'กลุ่มจับรางวัล', 'จำนวนคงเหลือ']
        
        if not all(col in employee_data.columns for col in required_emp_cols):
            st.error(f"ไฟล์พนักงานขาดคอลัมน์ที่จำเป็น: {', '.join(required_emp_cols)}")
            return pd.DataFrame(), pd.DataFrame()
            
        if not all(col in prize_data.columns for col in required_prize_cols):
            st.error(f"ไฟล์ของขวัญขาดคอลัมน์ที่จำเป็น: {', '.join(required_prize_cols)}")
            return pd.DataFrame(), pd.DataFrame()

        prize_data['จำนวนคงเหลือ'] = prize_data['จำนวนคงเหลือ'].fillna(0).astype(int)
        
        if 'สถานะ' not in employee_data.columns:
             employee_data['สถานะ'] = 'พร้อมสุ่ม'
        
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลด/ประมวลผลข้อมูล: {e}")
        return pd.DataFrame(), pd.DataFrame()

    st.success("โหลดข้อมูลสำเร็จแล้ว! พร้อมสุ่มรางวัล")
    return employee_data, prize_data 

def run_draw(group, emp_df, prize_df):
    group_clean = str(group).strip()
    available_employees = emp_df[(emp_df['กลุ่มจับรางวัล'] == group_clean) & (emp_df['สถานะ'] == 'พร้อมสุ่ม')]
    available_prizes = prize_df[(prize_df['กลุ่มจับรางวัล'] == group_clean) & (prize_df['จำนวนคงเหลือ'] > 0)]
    
    prize_list = []
    for index, row in available_prizes.iterrows():
        prize_list.extend([row['ชื่อของขวัญ']] * row['จำนวนคงเหลือ'])
        
    max_draws = min(len(available_employees), len(prize_list))
    
    if max_draws == 0:
        st.error(f"กลุ่ม {group}: ไม่มีพนักงานที่ยังไม่ได้สุ่ม หรือไม่มีของขวัญเหลือแล้ว")
        return []
        
    selected_employee_data = available_employees[['ชื่อ-นามสกุล', 'แผนก']].sample(max_draws)
    selected_employees = selected_employee_data.values.tolist() 
    selected_prizes = random.sample(prize_list, max_draws)
    
    results = list(zip(selected_employees, selected_prizes))
    return results

# ฟังก์ชันดึงภาพพื้นหลัง
def get_base64_image(image_file):
    try:
        with open(image_file, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        if image_file.lower().endswith(('.png')):
            mime_type = 'image/png'
        elif image_file.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        else:
            mime_type = 'image/jpg' 
            
        return f"data:{mime_type};base64,{data}"
    except FileNotFoundError:
        return None
    except Exception as e:
        return None

# ----------------------------------------------------
# --- Main Program (Streamlit UI) ---
# ----------------------------------------------------
def main():
    
    # ตรวจสอบว่า Streamlit รองรับ st.switch_page หรือไม่ (ควรจะรองรับใน Streamlit เวอร์ชันใหม่)
    if 'switch_page' not in dir(st):
        st.error("เวอร์ชัน Streamlit ปัจจุบันไม่รองรับ 'st.switch_page()' โปรดอัปเดตหรือเปลี่ยนไปใช้ Python 3.9+.")
        return
        
    st.set_page_config(
        layout="wide",
        page_title="สุ่มจับรางวัลปีใหม่ 2568", 
        initial_sidebar_state="collapsed"
    )
    
    with st.sidebar:
        st.header("⚙️ ตั้งค่าโปรแกรม")
        default_title = "🎉 สุ่มจับรางวัลของขวัญปีใหม่ 2568 V.FINAL-FIX-6 🎁 (Raffle Draw)" 
        custom_title = st.text_input("ชื่อ/หัวข้อโปรแกรม:", value=default_title)
        st.markdown("---")
        
        # *** NEW CODE: Slider ควบคุมความเร็ว ***
        st.markdown("### ⏱️ ควบคุมระยะเวลาแสดงผล")
        default_speed = st.session_state.get('announcement_speed', 3.0)
        speed_control = st.slider(
            "ระยะเวลาแสดงผลผู้โชคดี (วินาที)",
            min_value=1.0,
            max_value=10.0,
            value=default_speed,
            step=0.5,
            key='announcement_speed' 
        )
        st.markdown("---")
        # *** END NEW CODE ***
        
        st.markdown("**ไฟล์ข้อมูล:**")
        st.markdown("* `employees.csv`")
        st.markdown("* `prizes.csv`")
        st.markdown("* `background.jpg`")
        st.markdown("---")


    BACKGROUND_IMAGE_FILE = 'background.jpg'  
    base64_bg = get_base64_image(BACKGROUND_IMAGE_FILE)

    if base64_bg:
        background_css = f"""
        .stApp {{ 
            background-image: url("{base64_bg}"); 
            background-size: cover; 
            background-attachment: fixed;
            background-position: center;
        }}
        """
    else:
        background_css = ".stApp { background-color: #0e1117; }" 
        
    st.markdown(f"""
        <style>
        {background_css}
        .block-container {{ 
            padding-top: 2rem;
            padding-bottom: 0rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }}
        .main .block-container {{
            max-width: 1000px; 
            margin-left: auto;
            margin-right: auto;
            background-color: rgba(14, 17, 23, 0.9); 
            border-radius: 10px;
            padding: 20px;
        }}
        .success-box {{ 
            background-color: #1a5631; 
            color: white; 
            padding: 15px;
            border-left: 6px solid #48a964; 
            border-radius: 5px;
            margin-bottom: 1rem;
            font-size: 2.5em; 
            font-weight: bold;
            text-align: center; 
        }}
        /* กำหนดสไตล์ปุ่มหลัก (Raffle Draw) */
        .stButton>button[key="main_draw_btn"] {{ 
            background-color: #ff4b4b;
            color: white !important;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 1.2em;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(255, 75, 75, 0.4);
            transition: all 0.3s ease;
        }}
        /* กำหนดสไตล์ปุ่มเลือกกลุ่ม */
        .stButton>button[key^="group_btn_"] {{
            background-color: #3e4856 !important; 
            color: #4beaff !important; 
            border: 2px solid #4beaff;
            border-radius: 20px;
            padding: 8px 15px;
            font-size: 1.1em;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
            transition: all 0.2s;
        }}
        .stButton>button[key^="group_btn_"]:hover {{
            background-color: #4beaff !important;
            color: #0e1117 !important;
        }}
        h1 {{
            color: #4beaff; 
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            text-align: center; 
        }}
        h2 {{
             text-align: center; 
        }}
        </style>
        """, unsafe_allow_html=True)
    
    # ----------------------------------------------------
    # 2. โหลดและเก็บข้อมูลใน Session State 
    # ----------------------------------------------------
    if 'emp_df' not in st.session_state:
        emp_df, prize_df = load_data() 
        st.session_state.emp_df = emp_df
        st.session_state.prize_df = prize_df
        st.session_state.draw_history = [] 
        st.session_state.selected_group = None 
    
    # แก้ไข AttributeError: ตรวจสอบและกำหนดค่าเริ่มต้นเสมอ
    if 'draw_history' not in st.session_state:
         st.session_state.draw_history = [] 

    if st.session_state.emp_df.empty:
         return 

    groups = st.session_state.emp_df['กลุ่มจับรางวัล'].unique().tolist()
    groups = [str(g).strip() for g in groups if pd.notna(g) and str(g).strip().lower() != "nan" and str(g).strip() != ""]
    groups = sorted(list(set(groups))) 
    
    # ----------------------------------------------------
    # 3. แสดงผล Title และส่วนเลือกกลุ่ม
    # ----------------------------------------------------
    st.title(custom_title)
    st.markdown("---")
    st.markdown("## เลือกกลุ่มจับรางวัล:")
    
    n_groups = len(groups)
    cols_weights = [1] * (n_groups + 2) 
    
    if n_groups > 0:
        cols_center = st.columns(cols_weights) 
        
        for i, group in enumerate(groups):
            with cols_center[i + 1]: 
                if st.button(group, key=f"group_btn_{group}", help=f"คลิกเพื่อเลือกกลุ่ม {group} เพื่อเตรียมสุ่ม", use_container_width=True):
                    st.session_state.selected_group = group
                    st.rerun() 
    else:
        st.warning("ไม่พบกลุ่มจับรางวัลที่ถูกต้องในไฟล์ข้อมูล โปรดตรวจสอบคอลัมน์ 'กลุ่มจับรางวัล'")

    st.markdown("---")
    
    # ----------------------------------------------------
    # 4. ปุ่มสุ่มหลักและแสดงผล (พร้อมเปลี่ยนหน้าอัตโนมัติ)
    # ----------------------------------------------------
    if st.session_state.selected_group:
        selected_group = st.session_state.selected_group
        
        col_dummy_left, col_btn_center, col_dummy_right = st.columns([1, 1, 1])
        
        with col_btn_center:
            st.markdown(f"**💡 กลุ่มที่พร้อมสุ่ม:** <span style='color:#4beaff; font-weight:bold;'>{selected_group}</span>", unsafe_allow_html=True)

            if st.button(f"🔴 เริ่มสุ่มรางวัลกลุ่ม: **{selected_group}**", key="main_draw_btn", use_container_width=True):
                
                draw_results = run_draw(selected_group, st.session_state.emp_df, st.session_state.prize_df)
                
                # กำหนดความเร็วจาก Slider
                ROLLING_DURATION = 0.5 # เวลาแสดงผลการหมุนคงที่ 0.5 วินาที
                ANNOUNCEMENT_DURATION = st.session_state.get('announcement_speed', 3.0)
                
                if draw_results:
                    st.subheader(f"เริ่มการสุ่มกลุ่ม **{selected_group}**") 
                    current_winner_box = st.empty() 
                    
                    st.balloons() 
                    time.sleep(1) 
                        
                    for i, item in enumerate(draw_results):
                        
                        try:
                            (winner_name, winner_dept), prize = item
                        except (ValueError, TypeError):
                            st.error(f"โครงสร้างข้อมูลผลลัพธ์ผิดพลาดในรายการที่ {i+1} : {item}")
                            continue
                        
                        # A. Show rolling animation 
                        with current_winner_box.container():
                            st.markdown(f"## กำลังสุ่มผู้โชคดีรายการที่ **{i+1}**...") 
                        time.sleep(ROLLING_DURATION) 
                        
                        # B. Announce Winner
                        with current_winner_box.container():
                            winner_message = f"""
                            <div class='success-box'>
                                <span style='font-size: 0.8em; font-weight: normal;'>🎊 ผู้โชคดีคนล่าสุดคือ:</span><br>
                                <span style='font-size: 1.0em; color: #ffeb3b;'>**{winner_name}**</span><br>
                                <span style='font-size: 0.8em; color: #ffffff;'> (ได้รับ: {prize}) </span>
                            </div>
                            """
                            st.markdown(winner_message, unsafe_allow_html=True)
                            st.markdown("---")
                            
                        # C. อัปเดตสถานะและเก็บประวัติ (ใช้ st.session_state)
                        idx_emp = st.session_state.emp_df.index[st.session_state.emp_df['ชื่อ-นามสกุล'] == winner_name].tolist()
                        if idx_emp:
                            st.session_state.emp_df.loc[idx_emp[0], 'สถานะ'] = 'ได้รับแล้ว'
                        
                        idx_prize = st.session_state.prize_df.index[st.session_state.prize_df['ชื่อของขวัญ'] == prize].tolist()
                        if idx_prize:
                            current_qty = st.session_state.prize_df.loc[idx_prize[0], 'จำนวนคงเหลือ']
                            st.session_state.prize_df.loc[idx_prize[0], 'จำนวนคงเหลือ'] = current_qty - 1
                        
                        st.session_state.draw_history.append({'ชื่อ-นามสกุล': winner_name, 
                                                              'แผนก': winner_dept, 
                                                              'รายการของขวัญ': prize})
                        
                        time.sleep(ANNOUNCEMENT_DURATION) # ใช้ค่าจาก Slider ที่ผู้ใช้กำหนด
                        
                    st.empty() 
                    st.balloons()
                    
                    st.success("🎉 จบการสุ่มรางวัลกลุ่มนี้แล้ว! กำลังนำไปยังหน้าสรุปผล...")
                    time.sleep(1.0) # หน่วงเวลา 1 วินาที ให้ผู้ใช้เห็นข้อความ
                    
                    # สั่งเปลี่ยนไปหน้า Summary โดยตรง
                    st.switch_page("pages/1_Summary.py") 
                    
        
    else:
         st.info("กรุณาเลือกกลุ่มจับรางวัลจากปุ่มด้านบนเพื่อเริ่มสุ่ม")
         
    st.markdown("---")
    
if __name__ == '__main__':
    # แก้ไข AttributeError: ตรวจสอบและกำหนดค่า draw_history ที่นี่อีกครั้งก่อนเรียก main()
    if 'draw_history' not in st.session_state:
         st.session_state.draw_history = [] 
         
    main()

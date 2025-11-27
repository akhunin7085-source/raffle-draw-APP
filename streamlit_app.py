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
# --- CONFIGURATION & FILE PATHS ---
# ----------------------------------------------------
HISTORY_FILE = 'draw_history.csv'
EMPLOYEE_FILE = 'employees.csv'
PRIZE_FILE = 'prizes.csv'
# ----------------------------------------------------

def save_history(history_list):
    """บันทึกประวัติผลสุ่มลงในไฟล์ CSV อย่างถาวร พร้อมคอลัมน์ 'กลุ่มจับรางวัล' และ 'หมายเลขรางวัล'"""
    required_cols = ['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ', 'กลุ่มจับรางวัล', 'หมายเลขรางวัล'] 
    
    if not history_list:
        df_history = pd.DataFrame(columns=required_cols) 
    else:
        df_history = pd.DataFrame(history_list)
        for col in required_cols:
             if col not in df_history.columns:
                 df_history[col] = ''
        
    try:
        df_history.to_csv(HISTORY_FILE, index=False, encoding='utf_8_sig') 
    except Exception as e:
        print(f"ERROR: ไม่สามารถบันทึกประวัติผลสุ่มลงในไฟล์ได้: {e}") 

def save_uploaded_data(uploaded_file, file_path):
    """บันทึกไฟล์ที่อัปโหลดทับไฟล์เดิมบนดิสก์"""
    try:
        if uploaded_file is not None:
            file_data = uploaded_file.getvalue()
            with open(file_path, 'wb') as f:
                f.write(file_data)
            st.success(f"บันทึกไฟล์ **{os.path.basename(file_path)}** สำเร็จ!")
            return True
        return False
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการบันทึกไฟล์ {file_path}: {e}")
        return False

@st.cache_data(show_spinner=False) 
def load_data(emp_file=EMPLOYEE_FILE, prize_file=PRIZE_FILE):
    """โหลดข้อมูลจากไฟล์ CSV บนดิสก์"""
    employee_data = pd.DataFrame() 
    prize_data = pd.DataFrame() 
    
    st.info("กำลังโหลดข้อมูลจากไฟล์ CSV บนดิสก์...")
    
    # 1. โหลดไฟล์พนักงาน
    if os.path.exists(emp_file):
        try:
            employee_data = pd.read_csv(emp_file)
        except Exception as e:
            st.error(f"ERROR: ไม่สามารถอ่านไฟล์ {emp_file} ได้: {e}")
    else:
         st.warning(f"ไม่พบไฟล์ {emp_file} กรุณาอัปโหลดไฟล์ใหม่")

    # 2. โหลดไฟล์ของขวัญ
    if os.path.exists(prize_file):
        try:
            prize_data = pd.read_csv(prize_file) 
        except Exception as e:
            st.error(f"ERROR: ไม่สามารถอ่านไฟล์ {prize_file} ได้: {e}")
    else:
         st.warning(f"ไม่พบไฟล์ {prize_file} กรุณาอัปโหลดไฟล์ใหม่")


    # 3. ตรวจสอบความสมบูรณ์ของข้อมูล
    if employee_data.empty or prize_data.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    required_emp_cols = ['ชื่อ-นามสกุล', 'แผนก', 'กลุ่มจับรางวัล']
    # 'หมายเลขรางวัล' เป็นคอลัมน์ที่จำเป็นสำหรับ prizes.csv
    required_prize_cols = ['ชื่อของขวัญ', 'กลุ่มจับรางวัล', 'จำนวนคงเหลือ', 'หมายเลขรางวัล'] 
    
    if not all(col in employee_data.columns for col in required_emp_cols):
        st.error(f"ไฟล์พนักงานขาดคอลัมน์ที่จำเป็น: {', '.join(required_emp_cols)}")
        return pd.DataFrame(), pd.DataFrame()
        
    if not all(col in prize_data.columns for col in required_prize_cols):
        st.error(f"ไฟล์ของขวัญขาดคอลัมน์ที่จำเป็น: {', '.join(required_prize_cols)}")
        st.error("⚠️ ต้องใช้โครงสร้าง prizes.csv ใหม่ที่มี 'หมายเลขรางวัล' ด้วย!")
        return pd.DataFrame(), pd.DataFrame()

    try:
        # ตรวจสอบว่า 'จำนวนคงเหลือ' เป็น int ได้ (ควรเป็น 1 หรือ 0)
        prize_data['จำนวนคงเหลือ'] = prize_data['จำนวนคงเหลือ'].fillna(0).astype(int)
    except:
        st.error("คอลัมน์ 'จำนวนคงเหลือ' ใน prizes.csv ต้องเป็นตัวเลข (1 หรือ 0)")
        return pd.DataFrame(), pd.DataFrame()
        
    if 'สถานะ' not in employee_data.columns:
         employee_data['สถานะ'] = 'พร้อมสุ่ม'
         
    # *** NEW: ตรวจสอบและบังคับให้ 'หมายเลขรางวัล' เป็น String เพื่อให้ใช้เป็นคีย์ได้ ***
    prize_data['หมายเลขรางวัล'] = prize_data['หมายเลขรางวัล'].astype(str).str.strip()
         
    st.success("โหลดข้อมูลสำเร็จ! พร้อมสุ่มรางวัล")
    return employee_data, prize_data 

def reset_application():
    """รีเซ็ต Session State, ล้างประวัติ และโหลดข้อมูลเริ่มต้นใหม่"""
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        
    st.cache_data.clear() 
    st.session_state.emp_df, st.session_state.prize_df = load_data() 
    st.session_state.draw_history = []
    st.session_state.selected_group = None 
    st.success("✅ รีเซ็ตข้อมูลทั้งหมดและล้างประวัติการสุ่มสำเร็จ! โปรดรอโหลดหน้าจอใหม่")
    time.sleep(1)
    st.rerun()

# *** ฟังก์ชัน run_draw (แก้ไข: สุ่มตาม (ชื่อรางวัล, หมายเลขรางวัล)) ***
def run_draw(group, emp_df, prize_df):
    group_clean = str(group).strip()
    available_employees = emp_df[(emp_df['กลุ่มจับรางวัล'] == group_clean) & (emp_df['สถานะ'] == 'พร้อมสุ่ม')]
    
    # ดึงของรางวัลที่ยังเหลือ (จำนวนคงเหลือ > 0)
    available_prizes = prize_df[(prize_df['กลุ่มจับรางวัล'] == group_clean) & (prize_df['จำนวนคงเหลือ'] > 0)]
    
    # เตรียมรายการของขวัญและหมายเลขรางวัลสำหรับการสุ่ม (รวมกันเป็น tuple)
    # เราใช้ .values.tolist() เพื่อให้ได้รายการของ tuple โดยตรง
    prize_list_tuples = available_prizes[['ชื่อของขวัญ', 'หมายเลขรางวัล']].values.tolist()
    
    max_draws = min(len(available_employees), len(prize_list_tuples))
    
    if max_draws == 0:
        st.error(f"กลุ่ม {group}: ไม่มีพนักงานที่ยังไม่ได้สุ่ม หรือไม่มีของขวัญเหลือแล้ว")
        return []
        
    selected_employee_data = available_employees[['ชื่อ-นามสกุล', 'แผนก']].sample(max_draws)
    selected_employees = selected_employee_data.values.tolist() 
    
    # สุ่มเลือกรางวัลและหมายเลขรางวัลพร้อมกัน
    selected_prize_tuples = random.sample(prize_list_tuples, max_draws)
    
    # จัดโครงสร้างผลลัพธ์: [((ชื่อ, แผนก), [ชื่อรางวัล, หมายเลขรางวัล]), ...]
    results = list(zip(selected_employees, selected_prize_tuples))
    return results

def to_csv_bytes(df):
    """แปลง DataFrame เป็น CSV bytes สำหรับการดาวน์โหลด"""
    csv_bytes = df.to_csv(index=False, encoding='utf_8_sig').encode('utf-8')
    return csv_bytes

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
            
        return f"data:image/{mime_type};base64,{data}"
    except FileNotFoundError:
        return None
    except Exception as e:
        return None
        
# ----------------------------------------------------
# --- Main Program (Streamlit UI) ---
# ----------------------------------------------------
def main():
    
    st.set_page_config(
        layout="wide",
        page_title="สุ่มจับรางวัลปีใหม่ 2568", 
        initial_sidebar_state="collapsed"
    )
    
    # ----------------------------------------------------
    # 1. โหลดและเก็บข้อมูลใน Session State 
    # ----------------------------------------------------
    if 'emp_df' not in st.session_state:
        st.session_state.emp_df, st.session_state.prize_df = load_data() 
        st.session_state.draw_history = [] 
        st.session_state.selected_group = None 
    
    if 'draw_history' not in st.session_state:
         st.session_state.draw_history = [] 

    
    with st.sidebar:
        st.header("⚙️ ตั้งค่าโปรแกรมและข้อมูล")
        default_title = "🎉 สุ่มจับรางวัลของขวัญปีใหม่ 2568 🎁 (Raffle Draw)" 
        custom_title = st.text_input("ชื่อ/หัวข้อโปรแกรม:", value=default_title)
        st.markdown("---")
        
        # *** ส่วนดาวน์โหลดเทมเพลต (ปรับปรุงหมายเลขรางวัล) ***
        st.markdown("### ⬇️ ดาวน์โหลดเทมเพลต CSV")
        
        # 1. เทมเพลตพนักงาน
        emp_template = pd.DataFrame({
            'ชื่อ-นามสกุล': ['สมชาย ใจดี', 'สมหญิง สุขใจ'],
            'แผนก': ['HR', 'IT'],
            'กลุ่มจับรางวัล': ['อายุงาน 1-5 ปี', 'อายุงาน 20 ปีขึ้นไป'],
            'สถานะ': ['พร้อมสุ่ม', 'พร้อมสุ่ม']
        })
        st.download_button(
            label="📄 Template: employees.csv",
            data=to_csv_bytes(emp_template),
            file_name='employees_template.csv',
            mime='text/csv'
        )
        
        # 2. เทมเพลตของรางวัล (แก้ไขตัวอย่างให้เห็นว่าหมายเลขซ้ำได้)
        prize_template = pd.DataFrame({
            'ชื่อของขวัญ': ['ตั๋วเครื่องบิน', 'พัดลม', 'ทีวี 55 นิ้ว', 'สร้อยทอง'],
            'กลุ่มจับรางวัล': ['อายุงาน 1-5 ปี', 'อายุงาน 1-5 ปี', 'อายุงาน 20 ปีขึ้นไป', 'อายุงาน 20 ปีขึ้นไป'],
            'หมายเลขรางวัล': ['1', '2', '1', '2'], # หมายเลข 1 ซ้ำกันระหว่างกลุ่มได้
            'จำนวนคงเหลือ': [1, 1, 1, 1]
        })
        st.download_button(
            label="🎁 Template: prizes.csv (มีหมายเลขรางวัล)",
            data=to_csv_bytes(prize_template),
            file_name='prizes_template_with_id.csv',
            mime='text/csv'
        )
        st.markdown("---")


        # *** ส่วนอัปโหลดไฟล์ข้อมูล ***
        st.markdown("### ⬆️ อัปโหลดไฟล์ข้อมูลใหม่ (.csv)")
        uploaded_emp = st.file_uploader("อัปโหลด Employee File (employees.csv)", type=['csv'])
        uploaded_prize = st.file_uploader("อัปโหลด Prize File (prizes.csv)", type=['csv'])
        
        if st.button("บันทึกและโหลดข้อมูลใหม่", key='upload_reload_btn', type="primary"):
            emp_saved = save_uploaded_data(uploaded_emp, EMPLOYEE_FILE)
            prize_saved = save_uploaded_data(uploaded_prize, PRIZE_FILE)
            
            if emp_saved or prize_saved:
                st.cache_data.clear() 
                st.session_state.emp_df, st.session_state.prize_df = load_data() 
                st.session_state.draw_history = []
                save_history(st.session_state.draw_history) 
                st.session_state.selected_group = None 
                st.rerun()
            else:
                 st.warning("กรุณาเลือกไฟล์ที่จะอัปโหลดก่อน")
        st.markdown("---")
        
        # *** ปุ่มรีเซ็ตข้อมูลทั้งหมด ***
        st.markdown("### 💣 การควบคุมข้อมูล (สำหรับ Admin)")
        if st.button("🔴 ล้างประวัติการสุ่ม (Reset History)", help="จะลบไฟล์ draw_history.csv และรีเซ็ตสถานะการสุ่มทั้งหมด", use_container_width=True):
            if st.session_state.get('confirm_reset', False):
                 reset_application()
            else:
                 st.session_state.confirm_reset = True
                 st.warning("⚠️ ยืนยันการล้างประวัติและข้อมูลทั้งหมดใช่หรือไม่? (คลิกอีกครั้งเพื่อยืนยัน)")
        
        if st.session_state.get('confirm_reset', False) and not st.button("ยกเลิกการยืนยัน", key="cancel_reset"):
             pass 
        elif st.session_state.get('confirm_reset', False) and st.button("ยกเลิกการยืนยัน", key="cancel_reset"):
             st.session_state.confirm_reset = False
             st.rerun()


        st.markdown("---")
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


    # ----------------------------------------------------
    # 2. เตรียมข้อมูลกลุ่ม
    # ----------------------------------------------------
    if st.session_state.emp_df.empty or st.session_state.prize_df.empty:
        st.error("ไม่สามารถเริ่มการสุ่มได้ เนื่องจากข้อมูลพนักงานหรือของขวัญไม่สมบูรณ์")
        return 

    groups = st.session_state.emp_df['กลุ่มจับรางวัล'].unique().tolist()
    groups = [str(g).strip() for g in groups if pd.notna(g) and str(g).strip().lower() != "nan" and str(g).strip() != ""]
    groups = sorted(list(set(groups))) 
    
    # ----------------------------------------------------
    # 3. CSS และ UI Main Body (ไม่เปลี่ยนแปลง)
    # ----------------------------------------------------
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
    # 4. แสดงผล Title และส่วนเลือกกลุ่ม
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
        st.warning("ไม่พบกลุ่มจับรางวัลที่ถูกต้องในไฟล์ข้อมูล โปรดตรวจสอบคอลัมน์ 'กลุ่มจับรางวัล' ในไฟล์ที่โหลด/อัปโหลด")

    st.markdown("---")
    
    # ----------------------------------------------------
    # 5. ปุ่มสุ่มหลักและแสดงผล
    # ----------------------------------------------------
    if st.session_state.selected_group:
        selected_group = st.session_state.selected_group
        
        col_dummy_left, col_btn_center, col_dummy_right = st.columns([1, 1, 1])
        
        with col_btn_center:
            st.markdown(f"**💡 กลุ่มที่พร้อมสุ่ม:** <span style='color:#4beaff; font-weight:bold;'>{selected_group}</span>", unsafe_allow_html=True)

            if st.button(f"🔴 เริ่มสุ่มรางวัลกลุ่ม: **{selected_group}**", key="main_draw_btn", use_container_width=True):
                
                # ผลลัพธ์ที่ได้จะเป็น [((ชื่อ, แผนก), [ชื่อรางวัล, หมายเลขรางวัล]), ...]
                draw_results = run_draw(selected_group, st.session_state.emp_df, st.session_state.prize_df)
                
                ROLLING_DURATION = 0.5 
                ANNOUNCEMENT_DURATION = st.session_state.get('announcement_speed', 3.0)
                
                if draw_results:
                    st.subheader(f"เริ่มการสุ่มกลุ่ม **{selected_group}**") 
                    current_winner_box = st.empty() 
                    
                    st.balloons() 
                    time.sleep(1) 
                        
                    for i, item in enumerate(draw_results):
                        
                        try:
                            # แยกข้อมูลผู้โชคดีและของรางวัล
                            (winner_name, winner_dept), (prize_name, prize_number) = item
                        except (ValueError, TypeError):
                            st.error(f"โครงสร้างข้อมูลผลลัพธ์ผิดพลาดในรายการที่ {i+1} : {item}")
                            continue
                        
                        # A. Show rolling animation 
                        with current_winner_box.container():
                            st.markdown(f"## กำลังสุ่มผู้โชคดีรายการที่ **{i+1}**...") 
                        time.sleep(ROLLING_DURATION) 
                        
                        # B. Announce Winner (แสดงหมายเลขรางวัลด้วย)
                        with current_winner_box.container():
                            winner_message = f"""
                            <div class='success-box'>
                                <span style='font-size: 0.8em; font-weight: normal;'>🎊 ผู้โชคดีคนล่าสุดคือ:</span><br>
                                <span style='font-size: 1.0em; color: #ffeb3b;'>**{winner_name}**</span><br>
                                <span style='font-size: 0.8em; color: #ffffff;'> (ได้รับ: {prize_name} **หมายเลข {prize_number}**) </span>
                            </div>
                            """
                            st.markdown(winner_message, unsafe_allow_html=True)
                            st.markdown("---")
                            
                        # C. อัปเดตสถานะ (ใน Session State)
                        emp_df_copy = st.session_state.emp_df.copy()
                        prize_df_copy = st.session_state.prize_df.copy()
                        
                        # อัปเดตสถานะพนักงาน
                        idx_emp = emp_df_copy.index[emp_df_copy['ชื่อ-นามสกุล'] == winner_name].tolist()
                        if idx_emp:
                            emp_df_copy.loc[idx_emp[0], 'สถานะ'] = 'ได้รับแล้ว'
                        st.session_state.emp_df = emp_df_copy 
                        
                        # *** แก้ไข: อัปเดตสถานะของรางวัล (หาจาก กลุ่มจับรางวัล และ หมายเลขรางวัล) ***
                        prize_update_condition = (prize_df_copy['กลุ่มจับรางวัล'] == selected_group) & (prize_df_copy['หมายเลขรางวัล'] == prize_number)
                        idx_prize = prize_df_copy.index[prize_update_condition].tolist()
                        
                        if idx_prize:
                            # เนื่องจากแต่ละแถวคือของรางวัล 1 ชิ้น เราตั้งให้ 'จำนวนคงเหลือ' เป็น 0
                            prize_df_copy.loc[idx_prize[0], 'จำนวนคงเหลือ'] = 0
                        else:
                             st.warning(f"ไม่พบรายการของขวัญ (กลุ่ม: {selected_group}, หมายเลข: {prize_number}) ในข้อมูลของขวัญ!")
                             
                        st.session_state.prize_df = prize_df_copy 
                        
                        # D. เก็บประวัติและบันทึกลงไฟล์ (บันทึกหมายเลขรางวัล)
                        new_record = {
                            'ชื่อ-นามสกุล': winner_name, 
                            'แผนก': winner_dept, 
                            'รายการของขวัญ': prize_name,
                            'กลุ่มจับรางวัล': selected_group,
                            'หมายเลขรางวัล': prize_number 
                        }
                        st.session_state.draw_history.append(new_record)
                        save_history(st.session_state.draw_history) 
                        
                        time.sleep(ANNOUNCEMENT_DURATION) 
                        
                    st.empty() 
                    st.balloons()
                    
                    st.success("🎉 จบการสุ่มรางวัลกลุ่มนี้แล้ว! กำลังนำไปยังหน้าสรุปผล...")
                    time.sleep(1.0) 
                    
                    st.switch_page("pages/1_Summary.py") 
                    
                
    else:
          st.info("กรุณาเลือกกลุ่มจับรางวัลจากปุ่มด้านบนเพื่อเริ่มสุ่ม")
          
    st.markdown("---")
    
if __name__ == '__main__':
    if 'draw_history' not in st.session_state:
          st.session_state.draw_history = [] 
          
    main()

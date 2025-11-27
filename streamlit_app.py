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
import warnings 

# เพื่อป้องกัน UserWarning จาก openpyxl เมื่ออ่านไฟล์ Excel 
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
    """บันทึกประวัติผลสุ่มลงในไฟล์ CSV"""
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

@st.cache_data(show_spinner=False) 
def load_data(emp_file=EMPLOYEE_FILE, prize_file=PRIZE_FILE):
    """โหลดข้อมูลเริ่มต้นจากไฟล์ CSV บนดิสก์"""
    employee_data = pd.DataFrame() 
    prize_data = pd.DataFrame() 
    
    # ... (โค้ด load_data ส่วนที่เหลือเหมือนเดิม) ...
    st.info("กำลังโหลดข้อมูลเริ่มต้นจากไฟล์ CSV บนดิสก์...")
    
    # 1. โหลดไฟล์พนักงาน
    if os.path.exists(emp_file):
        try:
            employee_data = pd.read_csv(emp_file, encoding='utf-8-sig') # ใช้ utf-8-sig แก้ปัญหา BOM
        except Exception as e:
            st.error(f"ERROR: ไม่สามารถอ่านไฟล์ {emp_file} ได้: {e}")
    
    # 2. โหลดไฟล์ของขวัญ
    if os.path.exists(prize_file):
        try:
            prize_data = pd.read_csv(prize_file, encoding='utf-8-sig') 
        except Exception as e:
            st.error(f"ERROR: ไม่สามารถอ่านไฟล์ {prize_file} ได้: {e}")
    

    # 3. ตรวจสอบความสมบูรณ์ของข้อมูลและคอลัมน์ที่จำเป็น
    if employee_data.empty or prize_data.empty:
        return pd.DataFrame(), pd.DataFrame()
        
    required_emp_cols = ['ชื่อ-นามสกุล', 'แผนก', 'กลุ่มจับรางวัล']
    required_prize_cols = ['ชื่อของขวัญ', 'กลุ่มจับรางวัล', 'จำนวนคงเหลือ'] 
    
    if not all(col in employee_data.columns for col in required_emp_cols):
        st.error(f"ไฟล์พนักงานขาดคอลัมน์ที่จำเป็น: {', '.join(required_emp_cols)}")
        return pd.DataFrame(), pd.DataFrame()
        
    if not all(col in prize_data.columns for col in required_prize_cols):
        st.error(f"ไฟล์ของขวัญขาดคอลัมน์ที่จำเป็น: {', '.join(required_prize_cols)}")
        return pd.DataFrame(), pd.DataFrame()

    try:
        prize_data['จำนวนคงเหลือ'] = pd.to_numeric(
            prize_data['จำนวนคงเหลือ'], 
            errors='coerce'
        ).fillna(0).astype(int)
        
        # ทำให้คอลัมน์ 'หมายเลข' เป็นตัวเลข/สตริง ถ้ามี
        if 'หมายเลข' in prize_data.columns:
             prize_data['หมายเลข'] = prize_data['หมายเลข'].astype(str).str.strip().replace('nan', '0')
        
    except:
        st.error("คอลัมน์ 'จำนวนคงเหลือ' ใน prizes.csv ต้องเป็นตัวเลข")
        return pd.DataFrame(), pd.DataFrame()
        
    if 'สถานะ' not in employee_data.columns:
        employee_data['สถานะ'] = 'พร้อมสุ่ม'
        
    st.success("โหลดข้อมูลเริ่มต้นสำเร็จ! (หากไฟล์เริ่มต้นมีอยู่)")
    return employee_data, prize_data 

def reset_application():
    """รีเซ็ต Session State, ล้างประวัติ และโหลดข้อมูลเริ่มต้นใหม่"""
    # ... (โค้ด reset_application ส่วนที่เหลือเหมือนเดิม) ...
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)
        
    st.cache_data.clear() 
    st.session_state.emp_df, st.session_state.prize_df = load_data() 
    st.session_state.draw_history = []
    st.session_state.selected_group = None 
    st.success("✅ รีเซ็ตข้อมูลทั้งหมดและล้างประวัติการสุ่มสำเร็จ! โปรดรอโหลดหน้าจอใหม่")
    time.sleep(1)
    st.rerun()

def to_csv_bytes(df):
    """แปลง DataFrame เป็น CSV bytes สำหรับการดาวน์โหลด"""
    return df.to_csv(index=False, encoding='utf_8_sig').encode('utf-8')

def run_draw(group, emp_df, prize_df):
    """ทำการสุ่มจับรางวัลสำหรับกลุ่มที่เลือก พร้อมดึงหมายเลขรางวัล"""
    group_clean = str(group).strip()
    available_employees = emp_df[(emp_df['กลุ่มจับรางวัล'] == group_clean) & (emp_df['สถานะ'] == 'พร้อมสุ่ม')]
    available_prizes = prize_df[(prize_df['กลุ่มจับรางวัล'] == group_clean) & (prize_df['จำนวนคงเหลือ'] > 0)]
    
    prize_details_list = []
    has_prize_number = 'หมายเลข' in available_prizes.columns
    
    for index, row in available_prizes.iterrows():
        prize_number = str(row['หมายเลข']) if has_prize_number else 0
        detail_tuple = (row['ชื่อของขวัญ'], prize_number)
        prize_details_list.extend([detail_tuple] * row['จำนวนคงเหลือ'])
        
    max_draws = min(len(available_employees), len(prize_details_list))
    
    if max_draws == 0:
        st.error(f"กลุ่ม {group}: ไม่มีพนักงานที่ยังไม่ได้สุ่ม หรือไม่มีของขวัญเหลือแล้ว")
        return []
        
    selected_employee_data = available_employees[['ชื่อ-นามสกุล', 'แผนก']].sample(max_draws)
    selected_employees = selected_employee_data.values.tolist() 
    selected_prize_details = random.sample(prize_details_list, max_draws) 
    
    results = list(zip(selected_employees, selected_prize_details))
    return results

def get_base64_image(image_file):
    """แปลงไฟล์รูปภาพเป็น Base64 สำหรับใช้ใน CSS (พื้นหลัง)"""
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
    if 'draw_history' not in st.session_state:
        try:
             if os.path.exists(HISTORY_FILE):
                st.session_state.draw_history = pd.read_csv(HISTORY_FILE).replace({np.nan: None}).to_dict('records')
             else:
                st.session_state.draw_history = []
        except:
             st.session_state.draw_history = []

    if 'emp_df' not in st.session_state:
        st.session_state.emp_df, st.session_state.prize_df = load_data() 
        st.session_state.selected_group = None 
    
    
    with st.sidebar:
        # ... (โค้ด Sidebar เหมือนเดิม) ...
        st.header("⚙️ ตั้งค่าโปรแกรมและข้อมูล")
        default_title = "🎉 สุ่มจับรางวัลของขวัญปีใหม่ 2568 🎁 (Raffle Draw)" 
        custom_title = st.text_input("ชื่อ/หัวข้อโปรแกรม:", value=default_title)
        st.markdown("---")
        
        # *** ส่วนดาวน์โหลดเทมเพลต ***
        st.markdown("### ⬇️ ดาวน์โหลดเทมเพลต")
        
        emp_template = pd.DataFrame({
            'ชื่อ-นามสกุล': ['สมชาย ใจดี', 'สมหญิง สุขใจ'],
            'แผนก': ['HR', 'IT'],
            'กลุ่มจับรางวัล': ['อายุงาน 1-5 ปี', 'อายุงาน 20 ปีขึ้นไป'],
            'สถานะ': ['พร้อมสุ่ม', 'พร้อมสุ่ม']
        })
        st.download_button(
            label="📄 Template: พนักงาน (CSV)",
            data=to_csv_bytes(emp_template),
            file_name='employees_template.csv',
            mime='text/csv'
        )
        
        prize_template = pd.DataFrame({
            'หมายเลข': [1, 2, 3],
            'ชื่อของขวัญ': ['ตั๋วเครื่องบิน', 'พัดลม', 'ทีวี 55 นิ้ว'],
            'กลุ่มจับรางวัล': ['อายุงาน 1-5 ปี', 'อายุงาน 1-5 ปี', 'อายุงาน 20 ปีขึ้นไป'],
            'จำนวนคงเหลือ': [3, 10, 1]
        })
        st.download_button(
            label="🎁 Template: ของรางวัล (CSV - มีหมายเลข)",
            data=to_csv_bytes(prize_template),
            file_name='prizes_template.csv',
            mime='text/csv'
        )
        st.markdown("---")


        # *** ส่วนอัปโหลดไฟล์ข้อมูลใหม่ ***
        st.markdown("### ⬆️ อัปโหลดไฟล์ข้อมูลใหม่ (.csv / .xlsx)")
        uploaded_type = ['csv', 'xlsx', 'xls']
        
        uploaded_emp = st.file_uploader(
            "อัปโหลด Employee File", 
            type=uploaded_type, 
            key='uploaded_emp_file'
        )
        uploaded_prize = st.file_uploader(
            "อัปโหลด Prize File", 
            type=uploaded_type, 
            key='uploaded_prize_file'
        )
        
        
        def read_uploaded_file(uploaded_file):
            if uploaded_file is None:
                return None
            
            file_ext = uploaded_file.name.split('.')[-1].lower()
            uploaded_file.seek(0)
            
            try:
                if file_ext in ['xlsx', 'xls']:
                    return pd.read_excel(uploaded_file)
                elif file_ext == 'csv':
                    try:
                        return pd.read_csv(uploaded_file, encoding='utf-8')
                    except UnicodeDecodeError:
                        uploaded_file.seek(0)
                        try:
                            return pd.read_csv(uploaded_file, encoding='cp874')
                        except:
                            uploaded_file.seek(0)
                            return pd.read_csv(uploaded_file, encoding='utf-8-sig')
                else:
                    return None
            except Exception as e:
                raise e
                
        
        if st.button("ประมวลผลและโหลดข้อมูลใหม่", key='upload_reload_btn', type="primary"):
            
            uploaded_count = 0
            
            # A. ประมวลผลไฟล์พนักงาน
            if uploaded_emp is not None:
                try:
                    new_emp_df = read_uploaded_file(uploaded_emp)
                    required_emp_cols = ['ชื่อ-นามสกุล', 'แผนก', 'กลุ่มจับรางวัล']
                    if new_emp_df is not None and not all(col in new_emp_df.columns for col in required_emp_cols):
                        st.error(f"ไฟล์พนักงานขาดคอลัมน์ที่จำเป็น: {', '.join(required_emp_cols)}")
                    elif new_emp_df is not None:
                        if 'สถานะ' not in new_emp_df.columns:
                            new_emp_df['สถานะ'] = 'พร้อมสุ่ม'
                        st.session_state.emp_df = new_emp_df
                        st.success("ประมวลผลไฟล์พนักงานสำเร็จ!")
                        uploaded_count += 1
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์พนักงาน: {e}")

            # B. ประมวลผลไฟล์ของขวัญ
            if uploaded_prize is not None:
                try:
                    new_prize_df = read_uploaded_file(uploaded_prize)
                    required_prize_cols = ['ชื่อของขวัญ', 'กลุ่มจับรางวัล', 'จำนวนคงเหลือ'] 
                    if new_prize_df is not None and not all(col in new_prize_df.columns for col in required_prize_cols):
                        st.error(f"ไฟล์ของขวัญขาดคอลัมน์ที่จำเป็น: {', '.join(required_prize_cols)}")
                    elif new_prize_df is not None:
                        new_prize_df['จำนวนคงเหลือ'] = pd.to_numeric(new_prize_df['จำนวนคงเหลือ'], errors='coerce').fillna(0).astype(int)
                        if 'หมายเลข' in new_prize_df.columns:
                            new_prize_df['หมายเลข'] = new_prize_df['หมายเลข'].astype(str).str.strip().replace('nan', '0')
                        st.session_state.prize_df = new_prize_df
                        st.success("ประมวลผลไฟล์ของขวัญสำเร็จ!")
                        uploaded_count += 1
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ของขวัญ: {e}")
            
            if uploaded_count > 0:
                st.session_state.draw_history = []
                save_history(st.session_state.draw_history) 
                st.session_state.selected_group = None
                st.cache_data.clear() 
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
        st.error("ไม่สามารถเริ่มการสุ่มได้ เนื่องจากข้อมูลพนักงานหรือของขวัญไม่สมบูรณ์ (กรุณาอัปโหลดไฟล์ใหม่)")
        return 

    groups = st.session_state.emp_df['กลุ่มจับรางวัล'].unique().tolist()
    groups = [str(g).strip() for g in groups if pd.notna(g) and str(g).strip().lower() != "nan" and str(g).strip() != ""]
    groups = sorted(list(set(groups))) 
    
    # ----------------------------------------------------
    # 3. CSS และ UI Main Body (ปรับปรุงความสวยงาม)
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
        /* 1. Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;700&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Kanit', sans-serif;
        }}
        
        /* 2. กำหนด Custom CSS Variables */
        :root {{
            --primary-color: #FFD700; /* สีทองสำหรับเน้น */
            --secondary-color: #00FFFF; /* สี Cyan สำหรับไฮไลท์ */
            --success-bg: #1e8449; /* สีเขียวเข้มสำหรับ Success Box */
        }}
        
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
            background-color: rgba(18, 20, 25, 0.9); /* พื้นหลังเข้มขึ้น */
            border-radius: 10px;
            padding: 20px;
        }}
        .success-box {{ 
            background-color: var(--success-bg); 
            color: white; 
            padding: 15px;
            border-left: 6px solid var(--primary-color); /* ใช้สีทองขอบซ้าย */
            border-radius: 5px;
            margin-bottom: 1rem;
            font-size: 2.5em; 
            font-weight: bold;
            text-align: center; 
        }}
        .stButton>button[key="main_draw_btn"] {{ 
            background-color: var(--primary-color); /* ใช้สีทอง */
            color: #0e1117 !important; /* เปลี่ยนตัวอักษรเป็นสีเข้ม */
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 1.2em;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(255, 215, 0, 0.4);
            transition: all 0.3s ease;
        }}
        .stButton>button[key^="group_btn_"] {{
            background-color: #3e4856 !important; 
            color: var(--secondary-color) !important; /* ใช้สี Cyan */
            border: 2px solid var(--secondary-color);
            border-radius: 20px;
            padding: 8px 15px;
            font-size: 1.1em;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.5);
            transition: all 0.2s;
        }}
        .stButton>button[key^="group_btn_"]:hover {{
            background-color: var(--secondary-color) !important;
            color: #0e1117 !important;
        }}
        h1 {{
            color: var(--primary-color); /* ใช้สีทอง */
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
    
    if n_groups > 0:
        cols = st.columns(n_groups + 2) 
        
        for i, group in enumerate(groups):
            with cols[i + 1]: 
                if st.button(group, key=f"group_btn_{group}", help=f"คลิกเพื่อเลือกกลุ่ม {group} เพื่อเตรียมสุ่ม", use_container_width=True):
                    st.session_state.selected_group = group
                    st.rerun() 
    else:
        st.warning("ไม่พบกลุ่มจับรางวัลที่ถูกต้องในไฟล์ข้อมูล")

    st.markdown("---")
    
    # ----------------------------------------------------
    # 5. ปุ่มสุ่มหลักและแสดงผล
    # ----------------------------------------------------
    if st.session_state.selected_group:
        selected_group = st.session_state.selected_group
        
        col_dummy_left, col_btn_center, col_dummy_right = st.columns([1, 1, 1])
        
        with col_btn_center:
            st.markdown(f"**💡 กลุ่มที่พร้อมสุ่ม:** <span style='color:var(--secondary-color); font-weight:bold;'>{selected_group}</span>", unsafe_allow_html=True)

            if st.button(f"🔴 เริ่มสุ่มรางวัลกลุ่ม: **{selected_group}**", key="main_draw_btn", use_container_width=True):
                
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
                            # โครงสร้าง: ((ชื่อ, แผนก), (ชื่อรางวัล, หมายเลขรางวัล))
                            (winner_name, winner_dept), (prize, prize_number) = item 
                        except (ValueError, TypeError):
                            st.error(f"โครงสร้างข้อมูลผลลัพธ์ผิดพลาดในรายการที่ {i+1} : {item}")
                            continue
                        
                        # A. Show rolling animation 
                        with current_winner_box.container():
                            st.markdown(f"## กำลังสุ่มผู้โชคดีรายการที่ **{i+1}**...") 
                        time.sleep(ROLLING_DURATION) 
                        
                        # B. Announce Winner (แสดงหมายเลขรางวัลด้วย)
                        prize_number_display = f" (No. {prize_number})" if prize_number not in [0, '0', None, 'nan'] else ""
                        with current_winner_box.container():
                            winner_message = f"""
                            <div class='success-box'>
                                <span style='font-size: 0.8em; font-weight: normal;'>🎊 ผู้โชคดีคนล่าสุดคือ:</span><br>
                                <span style='font-size: 1.0em; color: var(--primary-color);'>**{winner_name}**</span><br>
                                <span style='font-size: 0.8em; color: #ffffff;'> (ได้รับ: {prize}{prize_number_display}) </span>
                            </div>
                            """
                            st.markdown(winner_message, unsafe_allow_html=True)
                            st.markdown("---")
                            
                        # C. อัปเดตสถานะ (ใน Session State)
                        emp_df_copy = st.session_state.emp_df.copy()
                        prize_df_copy = st.session_state.prize_df.copy()
                        
                        idx_emp = emp_df_copy.index[emp_df_copy['ชื่อ-นามสกุล'] == winner_name].tolist()
                        if idx_emp:
                            emp_df_copy.loc[idx_emp[0], 'สถานะ'] = 'ได้รับแล้ว'
                        st.session_state.emp_df = emp_df_copy 
                        
                        filter_condition = (prize_df_copy['ชื่อของขวัญ'] == prize) & (prize_df_copy['กลุ่มจับรางวัล'] == selected_group) & (prize_df_copy['จำนวนคงเหลือ'] > 0)
                        
                        if prize_number not in [0, '0', None, 'nan'] and 'หมายเลข' in prize_df_copy.columns:
                            filter_condition = filter_condition & (prize_df_copy['หมายเลข'].astype(str) == str(prize_number))

                        idx_prize = prize_df_copy.index[filter_condition].tolist()
                        
                        if idx_prize:
                            first_idx = idx_prize[0] 
                            current_qty = prize_df_copy.loc[first_idx, 'จำนวนคงเหลือ']
                            prize_df_copy.loc[first_idx, 'จำนวนคงเหลือ'] = current_qty - 1
                        st.session_state.prize_df = prize_df_copy 
                        
                        # D. เก็บประวัติและบันทึกลงไฟล์
                        new_record = {
                            'ชื่อ-นามสกุล': winner_name, 
                            'แผนก': winner_dept, 
                            'รายการของขวัญ': prize,
                            'กลุ่มจับรางวัล': selected_group,
                            'หมายเลขรางวัล': prize_number 
                        }
                        st.session_state.draw_history.append(new_record)
                        save_history(st.session_state.draw_history) 
                        
                        time.sleep(ANNOUNCEMENT_DURATION) 
                        
                    current_winner_box.empty()
                    st.balloons()
                    
                    st.success(f"🎉 การสุ่มรางวัลสำหรับกลุ่ม **{selected_group}** เสร็จสมบูรณ์แล้ว!")
                    
                
    else:
        st.info("กรุณาเลือกกลุ่มจับรางวัลจากปุ่มด้านบนเพื่อเริ่มสุ่ม")
        
    st.markdown("---")
    
if __name__ == '__main__':
    if 'draw_history' not in st.session_state:
        try:
             if os.path.exists(HISTORY_FILE):
                st.session_state.draw_history = pd.read_csv(HISTORY_FILE).replace({np.nan: None}).to_dict('records')
             else:
                st.session_state.draw_history = []
        except:
             st.session_state.draw_history = []

    main()

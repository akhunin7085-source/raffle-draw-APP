import streamlit as st
import pandas as pd
import random
import time
# บรรทัดนี้ได้รับการแก้ไขและพิมพ์ใหม่ เพื่อลบอักขระ U+00A0
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
EMPLOYEE_FILE = 'employees.csv' # ไฟล์เริ่มต้น (สำหรับกรณีไม่มีการอัปโหลด)
PRIZE_FILE = 'prizes.csv'        # ไฟล์เริ่มต้น (สำหรับกรณีไม่มีการอัปโหลด)

# ----------------------------------------------------
# --- FUNCTIONS (ไม่เปลี่ยนแปลงการทำงาน) ---
# ----------------------------------------------------

def save_history(history_list):
    """บันทึกประวัติผลสุ่มลงในไฟล์ CSV อย่างถาวร (เท่าที่ Streamlit Cloud จะอนุญาต)"""
    required_cols = ['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ', 'กลุ่มจับรางวัล'] 
    
    if not history_list:
        df_history = pd.DataFrame(columns=required_cols) 
    else:
        df_history = pd.DataFrame(history_list)
        for col in required_cols:
             if col not in df_history.columns:
                 df_history[col] = ''
        
    try:
        # การเขียนไฟล์ draw_history.csv ยังคงต้องทำ แต่ไม่รับประกันความคงทน
        df_history.to_csv(HISTORY_FILE, index=False, encoding='utf_8_sig') 
    except Exception as e:
        print(f"ERROR: ไม่สามารถบันทึกประวัติผลสุ่มลงในไฟล์ได้: {e}") 

@st.cache_data(show_spinner=False) 
def load_data(emp_file=EMPLOYEE_FILE, prize_file=PRIZE_FILE):
    """โหลดข้อมูลเริ่มต้นจากไฟล์ CSV บนดิสก์ (ใช้เฉพาะตอนเริ่มต้นแอปเท่านั้น)"""
    employee_data = pd.DataFrame() 
    prize_data = pd.DataFrame() 
    
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
    # เพิ่มการตรวจสอบสำหรับคอลัมน์ 'หมายเลขสลาก' (ตามที่ app ต้องการในไฟล์ prizes.csv)
    if 'หมายเลขสลาก' not in prize_data.columns and 'หมายเลข' in prize_data.columns:
        prize_data.rename(columns={'หมายเลข': 'หมายเลขสลาก'}, inplace=True)
        st.warning("⚠️ แก้ไข: ตรวจพบ 'หมายเลข' ใน prizes.csv และเปลี่ยนเป็น 'หมายเลขสลาก' ให้แล้ว")
        
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
    except:
        st.error("คอลัมน์ 'จำนวนคงเหลือ' ใน prizes.csv ต้องเป็นตัวเลข")
        return pd.DataFrame(), pd.DataFrame()
        
    if 'สถานะ' not in employee_data.columns:
        employee_data['สถานะ'] = 'พร้อมสุ่ม'
        
    st.success("โหลดข้อมูลเริ่มต้นสำเร็จ! (หากไฟล์เริ่มต้นมีอยู่)")
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

def to_csv_bytes(df):
    """แปลง DataFrame เป็น CSV bytes สำหรับการดาวน์โหลด"""
    csv_bytes = df.to_csv(index=False, encoding='utf_8_sig').encode('utf-8')
    return csv_bytes

def run_draw(group, emp_df, prize_df):
    """ทำการสุ่มจับรางวัลสำหรับกลุ่มที่เลือก"""
    group_clean = str(group).strip()
    available_employees = emp_df[(emp_df['กลุ่มจับรางวัล'] == group_clean) & (emp_df['สถานะ'] == 'พร้อมสุ่ม')]
    
    # *** ปรับปรุงการสุ่มรางวัลให้ใช้ 'หมายเลขสลาก' หากมี ***
    prize_has_ticket = 'หมายเลขสลาก' in prize_df.columns and prize_df['หมายเลขสลาก'].nunique() > 0
    
    available_prizes = prize_df[(prize_df['กลุ่มจับรางวัล'] == group_clean) & (prize_df['จำนวนคงเหลือ'] > 0)]
    
    prize_list = []
    if prize_has_ticket:
        # ใช้ 'หมายเลขสลาก' เป็นตัวแทนรายการของขวัญในการสุ่ม
        for index, row in available_prizes.iterrows():
            prize_name = row['ชื่อของขวัญ']
            ticket_number = row.get('หมายเลขสลาก', prize_name) # ใช้ชื่อของขวัญถ้าไม่มีหมายเลขสลาก
            prize_list.extend([f"{prize_name} ({ticket_number})"] * row['จำนวนคงเหลือ'])
    else:
        # ใช้ 'ชื่อของขวัญ' ธรรมดา
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

def get_base64_image(image_file):
    """แปลงไฟล์รูปภาพเป็น Base64 สำหรับใช้ใน CSS (พื้นหลัง)"""
    try:
        # ตรวจสอบว่าไฟล์มีอยู่จริงหรือไม่
        if not os.path.exists(image_file):
            return None
            
        with open(image_file, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        
        # ตรวจสอบประเภทไฟล์
        if image_file.lower().endswith(('.png')):
            mime_type = 'image/png'
        elif image_file.lower().endswith(('.jpg', '.jpeg')):
            mime_type = 'image/jpeg'
        else:
            mime_type = 'image/jpg' 
            
        return f"data:{mime_type};base64,{data}"
    except Exception as e:
        # ไม่แสดง error ถ้าไม่ใช่ไฟล์หลัก (เช่น background)
        print(f"Background image load error: {e}")
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
        # หาก draw_history หายไป ให้สร้างใหม่และลองโหลดจากไฟล์ (กรณี app crash)
        try:
             if os.path.exists(HISTORY_FILE):
                st.session_state.draw_history = pd.read_csv(HISTORY_FILE).to_dict('records')
             else:
                st.session_state.draw_history = []
        except:
             st.session_state.draw_history = []

    
    with st.sidebar:
        st.header("⚙️ ตั้งค่าโปรแกรมและข้อมูล")
        default_title = "🎉 สุ่มจับรางวัลของขวัญปีใหม่ 2568 🎁 (Raffle Draw)" 
        custom_title = st.text_input("ชื่อ/หัวข้อโปรแกรม:", value=default_title)
        st.markdown("---")
        
        # *** ส่วนดาวน์โหลดเทมเพลต ***
        st.markdown("### ⬇️ ดาวน์โหลดเทมเพลต")
        
        # 1. เทมเพลตพนักงาน
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
        
        # 2. เทมเพลตของรางวัล 
        # แก้ไขเทมเพลตให้มี 'หมายเลขสลาก' ตามที่ app คาดหวัง
        prize_template = pd.DataFrame({
            'หมายเลขสลาก': [1, 2, 1], # เพิ่มคอลัมน์นี้เข้ามา
            'ชื่อของขวัญ': ['ตั๋วเครื่องบิน', 'พัดลม', 'ทีวี 55 นิ้ว'],
            'กลุ่มจับรางวัล': ['อายุงาน 1-5 ปี', 'อายุงาน 1-5 ปี', 'อายุงาน 20 ปีขึ้นไป'],
            'จำนวนคงเหลือ': [3, 10, 1]
        })
        st.download_button(
            label="🎁 Template: ของรางวัล (CSV)",
            data=to_csv_bytes(prize_template),
            file_name='prizes_template.csv',
            mime='text/csv'
        )
        st.markdown("---")


        # *** ส่วนอัปโหลดไฟล์ข้อมูลใหม่ (รองรับ CSV/Excel) ***
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
            """ฟังก์ชันช่วยอ่านไฟล์ที่อัปโหลด รองรับ CSV (หลาย encoding) และ Excel"""
            if uploaded_file is None:
                return None
            
            file_ext = uploaded_file.name.split('.')[-1].lower()
            uploaded_file.seek(0)
            
            try:
                if file_ext in ['xlsx', 'xls']:
                    return pd.read_excel(uploaded_file)
                elif file_ext == 'csv':
                    # ลองหลาย Encoding เพื่อแก้ปัญหา 'invalid start byte'
                    encodings = ['utf-8', 'utf-8-sig', 'cp874', 'latin1']
                    for encoding in encodings:
                        try:
                            df = pd.read_csv(uploaded_file, encoding=encoding)
                            # ตรวจสอบว่า DataFrame มีข้อมูลหรือไม่ (ถ้ามีข้อมูลแสดงว่าอ่านได้)
                            if not df.empty:
                                return df
                            uploaded_file.seek(0)
                        except Exception as e:
                            uploaded_file.seek(0)
                    
                    # หากลองทุก encoding แล้วยังไม่ได้ผล ให้ขึ้น error
                    raise UnicodeDecodeError("All encoding attempts failed.")
                else:
                    return None
            except Exception as e:
                #st.error(f"Error in read_uploaded_file: {e}")
                raise e # ส่ง Exception ต่อไปให้ส่วนเรียกใช้จัดการ
                
        
        # ใช้ปุ่มเดียวในการประมวลผลไฟล์ที่อัปโหลด
        if st.button("ประมวลผลและโหลดข้อมูลใหม่", key='upload_reload_btn', type="primary"):
            
            uploaded_count = 0
            
            # A. ประมวลผลไฟล์พนักงาน
            if uploaded_emp is not None:
                try:
                    new_emp_df = read_uploaded_file(uploaded_emp)
                    
                    if new_emp_df is None:
                         st.error("ไม่รองรับรูปแบบไฟล์พนักงาน")
                         
                    # ตรวจสอบคอลัมน์ที่สำคัญ
                    required_emp_cols = ['ชื่อ-นามสกุล', 'แผนก', 'กลุ่มจับรางวัล']
                    if new_emp_df is not None and not all(col in new_emp_df.columns for col in required_emp_cols):
                        st.error(f"ไฟล์พนักงานขาดคอลัมน์ที่จำเป็น: {', '.join(required_emp_cols)}")
                    elif new_emp_df is not None:
                        if 'สถานะ' not in new_emp_df.columns:
                            new_emp_df['สถานะ'] = 'พร้อมสุ่ม'
                        st.session_state.emp_df = new_emp_df # บันทึกเข้า Session State โดยตรง
                        st.success("ประมวลผลไฟล์พนักงานสำเร็จ!")
                        uploaded_count += 1
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์พนักงาน: {e}")

            # B. ประมวลผลไฟล์ของขวัญ
            if uploaded_prize is not None:
                try:
                    new_prize_df = read_uploaded_file(uploaded_prize)
                    
                    if new_prize_df is None:
                         st.error("ไม่รองรับรูปแบบไฟล์ของขวัญ")
                         
                    # แก้ไข/ตรวจสอบคอลัมน์ 'หมายเลขสลาก'
                    if new_prize_df is not None:
                        if 'หมายเลข' in new_prize_df.columns and 'หมายเลขสลาก' not in new_prize_df.columns:
                             new_prize_df.rename(columns={'หมายเลข': 'หมายเลขสลาก'}, inplace=True)
                             st.warning("⚠️ แก้ไข: ตรวจพบ 'หมายเลข' ใน prizes.csv และเปลี่ยนเป็น 'หมายเลขสลาก' ให้แล้ว")
                             
                    # ตรวจสอบคอลัมน์และแปลงประเภทข้อมูล
                    required_prize_cols = ['ชื่อของขวัญ', 'กลุ่มจับรางวัล', 'จำนวนคงเหลือ'] 
                    if new_prize_df is not None and not all(col in new_prize_df.columns for col in required_prize_cols):
                        st.error(f"ไฟล์ของขวัญขาดคอลัมน์ที่จำเป็น: {', '.join(required_prize_cols)}")
                    elif new_prize_df is not None:
                        new_prize_df['จำนวนคงเหลือ'] = pd.to_numeric(new_prize_df['จำนวนคงเหลือ'], errors='coerce').fillna(0).astype(int)
                        st.session_state.prize_df = new_prize_df # บันทึกเข้า Session State โดยตรง
                        st.success("ประมวลผลไฟล์ของขวัญสำเร็จ!")
                        uploaded_count += 1
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาดในการอ่านไฟล์ของขวัญ: {e}")
            
            # C. รีโหลดแอปหากมีการอัปโหลดสำเร็จ
            if uploaded_count > 0:
                st.session_state.draw_history = []
                save_history(st.session_state.draw_history) # ล้างประวัติการสุ่ม (ไฟล์)
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
    
# --- BEGIN: UI/CSS Changes ---
# ----------------------------------------------------
# 3. CSS และ UI Main Body (Glassmorphism + Gold Theme)
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
        # Fallback to a dark background if image not found
        background_css = ".stApp { background-color: #0e1117; }" 
        
    st.markdown(f"""
        <style>
        /* 1. Import Font */
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;700&display=swap');
        html, body, [class*="css"] {{
            font-family: 'Kanit', sans-serif;
        }}
        
        /* 2. Custom CSS Variables (Gold/Dark Theme) */
        :root {{
            --gold-color: #FFD700; /* Primary Gold */
            --dark-gold-color: #C5B358; /* Secondary Gold */
            --glass-bg: rgba(14, 17, 23, 0.7); /* Dark Glass Background */
            --glass-border: rgba(255, 255, 255, 0.2); /* Light Glass Border */
            --success-bg: #1e8449; 
            --gold-glow: rgba(255, 215, 0, 0.4);
        }}
        
        {background_css}
        .block-container {{ 
            padding-top: 2rem;
            padding-bottom: 0rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }}
        
        /* Glassmorphism Main Container */
        .main .block-container {{
            max-width: 1000px; 
            margin-left: auto;
            margin-right: auto;
            background-color: var(--glass-bg); /* Dark Glass */
            backdrop-filter: blur(8px); /* Glass effect */
            border-radius: 15px;
            border: 1px solid var(--glass-border); /* Subtle border */
            padding: 30px; /* Increased padding for better feel */
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37); /* Glass Shadow */
        }}
        
        /* Success Box / Announcement Box */
        .success-box {{ 
            background-color: var(--success-bg); 
            color: white; 
            padding: 20px; /* Increased padding */
            border-left: 8px solid var(--gold-color); /* Gold Accent */
            border-radius: 10px;
            margin-bottom: 1.5rem;
            font-size: 2.8em; /* Slightly larger */
            font-weight: 700;
            text-align: center; 
            box-shadow: 0 0 15px var(--gold-glow); /* Gold Glow Effect */
            transition: all 0.3s ease;
            animation: pulse-gold 1.5s infinite alternate; /* Add subtle animation */
        }}

        /* Keyframe for subtle gold pulse */
        @keyframes pulse-gold {{
            0% {{ box-shadow: 0 0 10px var(--gold-glow); }}
            100% {{ box-shadow: 0 0 20px rgba(255, 215, 0, 0.8); }}
        }}


        
        /* Main Draw Button (Gold) */
        .stButton>button[key="main_draw_btn"] {{ 
            background-color: var(--gold-color); /* Gold */
            color: #0e1117 !important; /* Black text on Gold */
            border-radius: 10px;
            padding: 12px 25px;
            font-size: 1.4em; /* Larger font */
            font-weight: 700;
            box-shadow: 0 6px 15px rgba(255, 215, 0, 0.6); /* Stronger Gold Shadow */
            transition: all 0.3s ease;
            transform: scale(1.0);
        }}
        .stButton>button[key="main_draw_btn"]:hover {{
            background-color: var(--dark-gold-color); /* Darker Gold on hover */
            transform: scale(1.05); /* Slight scale effect */
            box-shadow: 0 8px 20px rgba(255, 215, 0, 0.8);
        }}
        
        /* Group Selection Buttons (Subtle Gold/Dark) */
        .stButton>button[key^="group_btn_"] {{
            background-color: rgba(30, 30, 30, 0.8) !important; /* Darker Glass button */
            color: var(--gold-color) !important; 
            border: 2px solid var(--dark-gold-color);
            border-radius: 25px; /* More rounded */
            padding: 10px 18px;
            font-size: 1.05em;
            font-weight: 500;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
            transition: all 0.3s;
        }}
        .stButton>button[key^="group_btn_"]:hover {{
            background-color: var(--dark-gold-color) !important;
            color: #0e1117 !important;
            border-color: var(--gold-color);
        }}
        
        /* Selected Group Button Highlight (Optional - requires custom implementation) */
        /* Since Streamlit doesn't expose a clean "selected" state, we leave this as is. */

        /* Headers */
        h1 {{
            color: var(--gold-color); 
            text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.7); /* Enhanced shadow */
            text-align: center; 
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        h2 {{
            text-align: center; 
            color: #ffffff;
            margin-top: 1rem;
            text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.5);
        }}
        h3 {{
            color: var(--dark-gold-color);
        }}
        /* Info/Warning/Success boxes inside glass container */
        .stAlert {{
            background-color: rgba(255, 255, 255, 0.1) !important; 
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255, 215, 0, 0.3);
            border-radius: 10px;
        }}
        </style>
        """, unsafe_allow_html=True)
    
# --- END: UI/CSS Changes ---
    
    # ----------------------------------------------------
    # 4. แสดงผล Title และส่วนเลือกกลุ่ม
    # ----------------------------------------------------
    st.title(custom_title)
    st.markdown("---")
    st.markdown("## เลือกกลุ่มจับรางวัล:")
    
    n_groups = len(groups)
    
    # สร้างคอลัมน์สำหรับปุ่มกลุ่ม
    if n_groups > 0:
        # กำหนดให้ปุ่มอยู่ตรงกลางโดยมีคอลัมน์ dummy ซ้ายขวา
        cols = st.columns(n_groups + 2) 
        
        for i, group in enumerate(groups):
            with cols[i + 1]: 
                # เพิ่ม Logic สำหรับการเน้นปุ่มที่ถูกเลือก (Selected Group)
                if st.session_state.selected_group == group:
                    # ใช้ CSS พิเศษสำหรับปุ่มที่ถูกเลือก
                    button_html = f"""
                    <style>
                    .stButton>button[key="group_btn_{group}"] {{
                        background-color: var(--gold-color) !important;
                        color: #0e1117 !important;
                        border: 2px solid var(--gold-color);
                        box-shadow: 0 0 10px var(--gold-glow);
                        transform: scale(1.02);
                    }}
                    </style>
                    """
                    st.markdown(button_html, unsafe_allow_html=True)
                    
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
            st.markdown(f"**💡 กลุ่มที่พร้อมสุ่ม:** <span style='color:var(--gold-color); font-weight:bold;'>{selected_group}</span>", unsafe_allow_html=True)

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
                            # โครงสร้าง: ((ชื่อ, แผนก), ชื่อรางวัล)
                            (winner_name, winner_dept), prize = item 
                        except (ValueError, TypeError):
                            st.error(f"โครงสร้างข้อมูลผลลัพธ์ผิดพลาดในรายการที่ {i+1} : {item}")
                            continue
                        
                        # A. Show rolling animation 
                        with current_winner_box.container():
                            st.markdown(f"## กำลังสุ่มผู้โชคดีรายการที่ **{i+1}**...") 
                        time.sleep(ROLLING_DURATION) 
                        
                        # B. Announce Winner
                        # ตรวจสอบว่ามีข้อมูลหมายเลขสลากติดมาหรือไม่
                        if '(' in prize and ')' in prize:
                             prize_display = prize.split('(')[0].strip()
                             ticket_number = prize.split('(')[-1].replace(')', '').strip()
                             prize_text = f"{prize_display} (หมายเลขสลาก: {ticket_number})"
                        else:
                             prize_text = prize
                             
                        with current_winner_box.container():
                            winner_message = f"""
                            <div class='success-box'>
                                <span style='font-size: 0.8em; font-weight: normal;'>🎊 ผู้โชคดีคนล่าสุดคือ:</span><br>
                                <span style='font-size: 1.0em; color: var(--gold-color);'>**{winner_name}**</span><br>
                                <span style='font-size: 0.8em; color: #ffffff;'> (ได้รับ: {prize_text}) </span>
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
                        
                        # อัปเดตสถานะของขวัญ (ลดจำนวนคงเหลือ 1 หน่วย โดยใช้ชื่อของขวัญ)
                        # ต้องแยกชื่อของขวัญออกจากหมายเลขสลากก่อน
                        prize_name_only = prize.split('(')[0].strip()
                        
                        idx_prize = prize_df_copy.index[
                            (prize_df_copy['ชื่อของขวัญ'] == prize_name_only) & 
                            (prize_df_copy['กลุ่มจับรางวัล'] == selected_group) & 
                            (prize_df_copy['จำนวนคงเหลือ'] > 0)
                        ].tolist()
                        
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
                            'กลุ่มจับรางวัล': selected_group 
                        }
                        st.session_state.draw_history.append(new_record)
                        save_history(st.session_state.draw_history) 
                        
                        time.sleep(ANNOUNCEMENT_DURATION) 
                        
                    current_winner_box.empty() # ล้างกล่องแสดงผู้โชคดีคนล่าสุด
                    st.balloons()
                    
                    # *** แสดงข้อความแสดงความยินดีและยืนยันการจบการสุ่ม ***
                    st.success(f"🎉 การสุ่มรางวัลสำหรับกลุ่ม **{selected_group}** เสร็จสมบูรณ์แล้ว! ท่านสามารถตรวจสอบผลการสุ่มและรางวัลที่เหลือได้ในหน้า Summary หรือหน้าสรุปผลกลุ่มย่อย")
                    
                
    else:
        st.info("กรุณาเลือกกลุ่มจับรางวัลจากปุ่มด้านบนเพื่อเริ่มสุ่ม")
        
    st.markdown("---")
    
if __name__ == '__main__':
    # Initial check and setup for draw_history
    if 'draw_history' not in st.session_state:
        try:
             if os.path.exists(HISTORY_FILE):
                st.session_state.draw_history = pd.read_csv(HISTORY_FILE).to_dict('records')
             else:
                st.session_state.draw_history = []
        except:
             st.session_state.draw_history = []

    main()

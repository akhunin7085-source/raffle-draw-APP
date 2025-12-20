import streamlit as st
import pandas as pd
import random
import time
import base64
import os
import warnings

# ป้องกัน UserWarning
warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')

# ----------------------------------------------------
# --- FUNCTIONS ---
# ----------------------------------------------------
def save_history(history_list):
    df = pd.DataFrame(history_list)
    df.to_csv('draw_history.csv', index=False, encoding='utf_8_sig')

def load_data():
    emp_df = pd.DataFrame()
    prize_df = pd.DataFrame()
    if os.path.exists('employees.csv'):
        emp_df = pd.read_csv('employees.csv', encoding='utf-8-sig')
    if os.path.exists('prizes.csv'):
        prize_df = pd.read_csv('prizes.csv', encoding='utf-8-sig')
    if not emp_df.empty and 'สถานะ' not in emp_df.columns:
        emp_df['สถานะ'] = 'พร้อมสุ่ม'
    if not prize_df.empty:
        prize_df['จำนวนคงเหลือ'] = pd.to_numeric(prize_df['จำนวนคงเหลือ'], errors='coerce').fillna(0).astype(int)
    return emp_df, prize_df

def get_image_base64(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.getvalue()).decode()
    return None

# ----------------------------------------------------
# --- MAIN PROGRAM ---
# ----------------------------------------------------
def main():
    st.set_page_config(layout="wide", page_title="ระบบสุ่มรางวัล")

    if 'emp_df' not in st.session_state:
        st.session_state.emp_df, st.session_state.prize_df = load_data()
    if 'draw_history' not in st.session_state:
        st.session_state.draw_history = []

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ ตั้งค่า")
        custom_title = st.text_input("หัวข้อโปรแกรม:", "🎉 สุ่มขวัญปีใหม่ 2569 🎁")
        bg_upload = st.file_uploader("เปลี่ยนภาพพื้นหลัง:", type=['jpg', 'png'])
        bg_base64 = get_image_base64(bg_upload)
        draw_speed = st.slider("ความเร็ว (วินาที):", 0.01, 1.0, 0.03, 0.01)

    # --- CSS: บังคับทุกอย่างให้อยู่ตรงกลาง (FIXED) ---
    bg_style = f'background-image: url("data:image/png;base64,{bg_base64}"); background-size: cover;' if bg_base64 else "background-color: #0e1117;"

    st.markdown(f"""
        <style>
        .stApp {{ {bg_style} }}
        
        /* จัด Container หลักให้อยู่กึ่งกลางหน้าจอเสมอ */
        .main .block-container {{
            max-width: 1000px !important;
            margin: auto !important;
            padding-top: 2rem !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important; /* จัดลูกๆ ให้อยู่กลางแนวนอน */
            justify-content: center !important; /* จัดลูกๆ ให้อยู่กลางแนวตั้ง */
        }}

        /* หัวข้อต้องอยู่ตรงกลาง */
        .main-title {{
            text-align: center !important;
            color: #4beaff;
            font-size: 4rem;
            font-weight: bold;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
            margin-bottom: 20px;
            width: 100%;
        }}

        /* กล่องประกาศรางวัล (Success Box) แบบอยู่กึ่งกลางเป๊ะ */
        .success-box {{
            background-color: #1a5631;
            color: white;
            padding: 50px 20px;
            border-left: 15px solid #48a964;
            border-radius: 20px;
            text-align: center;
            width: 100%;
            max-width: 800px;
            margin: 20px auto !important; /* บังคับ Margin Auto */
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
        }}
        .w-name {{ font-size: 5rem; color: #ffeb3b; font-weight: bold; display: block; margin: 15px 0; }}
        .p-name {{ font-size: 2.5rem; color: #ffffff; display: block; }}
        
        /* ปรับปุ่มสุ่ม */
        div.stButton > button {{
            margin: 0 auto;
            display: block;
            background-color: #ff4b4b !important;
            height: 70px;
            width: 300px;
            font-size: 1.5rem !important;
        }}
        
        /* จัดการกลุ่มปุ่มให้เรียงกลาง */
        [data-testid="stHorizontalBlock"] {{
            justify-content: center !important;
        }}
        </style>
        """, unsafe_allow_html=True)

    # --- UI CONTENT ---
    # ใช้ Markdown แทน st.title เพื่อควบคุมการจัดกลางได้ 100%
    st.markdown(f'<div class="main-title">{custom_title}</div>', unsafe_allow_html=True)

    # เลือกกลุ่ม (จัดวางตรงกลาง)
    if not st.session_state.emp_df.empty:
        groups = [g for g in st.session_state.emp_df['กลุ่มจับรางวัล'].unique() if pd.notna(g)]
        st.markdown("<p style='text-align:center;'>🎯 เลือกกลุ่มจับรางวัล</p>", unsafe_allow_html=True)
        
        # สร้างปุ่มกลุ่ม
        cols = st.columns(len(groups))
        for i, group in enumerate(groups):
            with cols[i]:
                if st.button(group, key=f"g_{group}"):
                    st.session_state.selected_group = group

    st.markdown("---")

    # ส่วนการสุ่ม
    if 'selected_group' in st.session_state:
        group = st.session_state.selected_group
        st.markdown(f"<h3 style='text-align:center;'>พร้อมสุ่มกลุ่ม: <span style='color:#4beaff'>{group}</span></h3>", unsafe_allow_html=True)
        
        if st.button(f"🔴 เริ่มสุ่มรางวัล", key="draw_btn"):
            emp_list = st.session_state.emp_df[(st.session_state.emp_df['กลุ่มจับรางวัล'] == group) & (st.session_state.emp_df['สถานะ'] == 'พร้อมสุ่ม')]
            prize_list_df = st.session_state.prize_df[(st.session_state.prize_df['กลุ่มจับรางวัล'] == group) & (st.session_state.prize_df['จำนวนคงเหลือ'] > 0)]
            
            prizes = []
            for _, r in prize_list_df.iterrows():
                prizes.extend([r['ชื่อของขวัญ']] * r['จำนวนคงเหลือ'])
            
            if not emp_list.empty and prizes:
                count = min(len(emp_list), len(prizes))
                winners = emp_list.sample(count)
                selected_prizes = random.sample(prizes, count)
                
                placeholder = st.empty()
                st.balloons()

                for i in range(count):
                    w_name = winners.iloc[i]['ชื่อ-นามสกุล']
                    w_dept = winners.iloc[i]['แผนก']
                    p_name = selected_prizes[i]
                    
                    with placeholder.container():
                        st.markdown(f"""
                            <div class="success-box">
                                <span style="font-size:2rem;">🎊 ขอแสดงความยินดีกับ 🎊</span>
                                <span class="w-name">{w_name}</span>
                                <span class="p-name">ได้รับรางวัล: {p_name}</span>
                                <p style="margin-top:10px; opacity:0.8;">({w_dept})</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    # Update & Save
                    st.session_state.emp_df.loc[st.session_state.emp_df['ชื่อ-นามสกุล'] == w_name, 'สถานะ'] = 'ได้รับแล้ว'
                    p_idx = st.session_state.prize_df.index[(st.session_state.prize_df['ชื่อของขวัญ'] == p_name) & (st.session_state.prize_df['กลุ่มจับรางวัล'] == group)][0]
                    st.session_state.prize_df.at[p_idx, 'จำนวนคงเหลือ'] -= 1
                    
                    st.session_state.draw_history.append({'ชื่อ-นามสกุล': w_name, 'แผนก': w_dept, 'รายการของขวัญ': p_name, 'กลุ่มจับรางวัล': group})
                    save_history(st.session_state.draw_history)
                    
                    time.sleep(draw_speed) # 0.03 วินาที
                
                st.success("สุ่มรางวัลครบถ้วน!")
            else:
                st.warning("ไม่มีผู้มีสิทธิ์หรือของรางวัลเหลือในกลุ่มนี้")
    else:
        st.markdown("<p style='text-align:center;'>โปรดเลือกกลุ่มจับรางวัลด้านบน</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()

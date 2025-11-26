import streamlit as st
import pandas as pd
import random
import time
import io 
from datetime import datetime
import os
import base64 
import qrcode 

# --- ฟังก์ชันโหลดข้อมูล (จัดการ Error และแปลงชนิดข้อมูล) ---
@st.cache_data 
def load_data(emp_file='employees.csv', prize_file='prizes.csv'):
    
    employee_data = pd.DataFrame()
    prize_data = pd.DataFrame()
    
    if not os.path.exists(emp_file) or not os.path.exists(prize_file):
        st.error(f"⚠️ ไม่พบไฟล์ข้อมูล: ตรวจสอบว่ามีไฟล์ '{emp_file}' และ '{prize_file}' อยู่ในโฟลเดอร์เดียวกันหรือไม่")
        return pd.DataFrame(), pd.DataFrame()
        
    st.info(f"กำลังโหลดข้อมูลจากไฟล์: {emp_file} และ {prize_file}...")
    
    try:
        if emp_file.endswith(('.csv', '.CSV')):
             employee_data = pd.read_csv(emp_file)
        else:
             employee_data = pd.read_excel(emp_file)
        
        if prize_file.endswith(('.csv', '.CSV')):
             prize_data = pd.read_csv(prize_file)
        else:
             prize_data = pd.read_excel(prize_file)
        
        required_emp_cols = ['ชื่อ-นามสกุล', 'แผนก', 'กลุ่มจับรางวัล', 'สถานะ']
        required_prize_cols = ['ชื่อของขวัญ', 'กลุ่มจับรางวัล', 'จำนวนคงเหลือ']
        
        if not all(col in employee_data.columns for col in required_emp_cols):
            st.error(f"❌ ไฟล์พนักงานขาดคอลัมน์ที่จำเป็น: {', '.join(required_emp_cols)}")
            return pd.DataFrame(), pd.DataFrame()
            
        if not all(col in prize_data.columns for col in required_prize_cols):
            st.error(f"❌ ไฟล์ของขวัญขาดคอลัมน์ที่จำเป็น: {', '.join(required_prize_cols)}")
            return pd.DataFrame(), pd.DataFrame()

        prize_data['จำนวนคงเหลือ'] = prize_data['จำนวนคงเหลือ'].fillna(0) 
        prize_data['จำนวนคงเหลือ'] = prize_data['จำนวนคงเหลือ'].astype(int)
        
        if 'กลุ่มจับรางวัล' in employee_data.columns:
            employee_data['กลุ่มจับรางวัล'] = employee_data['กลุ่มจับรางวัล'].astype(str).str.strip()
        if 'กลุ่มจับรางวัล' in prize_data.columns:
            prize_data['กลุ่มจับรางวัล'] = prize_data['กลุ่มจับรางวัล'].astype(str).str.strip()
            
        if 'สถานะ' not in employee_data.columns:
             employee_data['สถานะ'] = 'พร้อมสุ่ม'

        
    except ValueError as e:
        st.error(f"❌ ข้อผิดพลาดในการแปลงข้อมูล: ตรวจสอบคอลัมน์ 'จำนวนคงเหลือ' ในไฟล์ของขวัญ ว่ามีข้อความที่ไม่ใช่ตัวเลขหรือไม่: ({e})")
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
        return pd.DataFrame(), pd.DataFrame()

    st.success("✅ โหลดข้อมูลสำเร็จแล้ว! พร้อมเริ่มจับรางวัล")
    return employee_data, prize_data 

# --- ฟังก์ชันหลักในการสุ่ม ---
def run_draw(group, emp_df, prize_df):
    
    group_clean = str(group).strip()

    available_employees = emp_df[(emp_df['กลุ่มจับรางวัล'] == group_clean) & (emp_df['สถานะ'] == 'พร้อมสุ่ม')]
    available_prizes = prize_df[(prize_df['กลุ่มจับรางวัล'] == group_clean) & (prize_df['จำนวนคงเหลือ'] > 0)]
    
    prize_list = []
    for index, row in available_prizes.iterrows():
        prize_list.extend([row['ชื่อของขวัญ']] * row['จำนวนคงเหลือ'])

    max_draws = min(len(available_employees), len(prize_list))

    if max_draws == 0:
        st.error(f"⚠️ **กลุ่ม {group}**: ไม่มีพนักงานที่ยังไม่ได้สุ่ม หรือไม่มีของขวัญเหลือแล้ว")
        return []

    selected_employee_data = available_employees[['ชื่อ-นามสกุล', 'แผนก']].sample(max_draws)
    selected_employees = selected_employee_data.values.tolist() 
    selected_prizes = random.sample(prize_list, max_draws)

    results = list(zip(selected_employees, selected_prizes))
    return results

# --- ฟังก์ชันสร้างไฟล์ Excel สำหรับดาวน์โหลด ---
def create_print_ready_excel():
    if not st.session_state.draw_history:
        return None

    history_df = pd.DataFrame(st.session_state.draw_history)
    history_df['ช่องเซ็นต์รับ'] = '' 
    
    final_cols = ['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ', 'ช่องเซ็นต์รับ']
    final_df = history_df[final_cols]
    final_df.insert(0, 'ลำดับ', range(1, 1 + len(final_df)))
    
    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: 
            final_df.to_excel(writer, index=False, sheet_name='ผลจับรางวัลปีใหม่')
            worksheet = writer.sheets['ผลจับรางวัลปีใหม่']
            worksheet.set_column('A:A', 8) 
            worksheet.set_column('B:B', 20) 
            worksheet.set_column('C:C', 20) 
            worksheet.set_column('D:D', 30) 
            worksheet.set_column('E:E', 25) 
    except ImportError:
         st.error("❌ ไม่พบ Library 'xlsxwriter' โปรดติดตั้งด้วยคำสั่ง: pip install xlsxwriter")
         return None
    except Exception as e:
         st.error(f"❌ เกิดข้อผิดพลาดในการสร้างไฟล์ Excel: {e}")
         return None
    
    processed_data = output.getvalue()
    return processed_data

# --- NEW FUNCTION: สร้าง QR Code จากข้อความและแปลงเป็น Base64 (ใช้ซ้ำได้) ---
def create_qrcode_base64(text_data):
    """สร้าง QR Code จากข้อความและส่งคืน Base64 String สำหรับใช้ใน HTML"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(text_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        base64_img = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{base64_img}"
        
    except ImportError:
        return None 
    except Exception as e:
        return None

# --- ฟังก์ชันแปลงไฟล์ภาพพื้นหลังให้เป็น Base64 สำหรับ CSS Background ---
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

# --- Main Program (Streamlit UI) ---
def main():
    
    # ----------------------------------------------------
    # 1. การตั้งค่าหน้าจอและ CSS Global 
    # ----------------------------------------------------
    st.set_page_config(
        layout="wide",
        page_title="สุ่มจับรางวัลปีใหม่ 2568", 
        initial_sidebar_state="collapsed"
    )
    
    with st.sidebar:
        st.header("⚙️ ตั้งค่าโปรแกรม")
        
        default_title = "🎉 สุ่มจับรางวัลของขวัญปีใหม่ 2568 🎁 (Raffle Draw)"
        custom_title = st.text_input(
            "ชื่อ/หัวข้อโปรแกรม:",
            value=default_title,
            help="ข้อความที่แสดงเป็นหัวข้อหลักด้านบนของหน้าจอ"
        )
        
        st.markdown("---")
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

        .stButton>button {{
            background-color: #ff4b4b;
            color: white !important;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 1.2em;
            font-weight: bold;
            box-shadow: 0 4px 8px rgba(255, 75, 75, 0.4);
            transition: all 0.3s ease;
        }}
        .stButton>button:hover {{
            background-color: #ff6666;
            box-shadow: 0 6px 12px rgba(255, 75, 75, 0.6);
            transform: translateY(-2px);
        }}
        .stButton {{
            margin-bottom: 10px; 
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
    # 2. แสดงผล Title/Header 
    # ----------------------------------------------------
    st.title(custom_title)
    
    st.markdown("---")

    # โหลดและเก็บข้อมูลใน Session State
    if 'emp_df' not in st.session_state:
        emp_df, prize_df = load_data() 
        st.session_state.emp_df = emp_df
        st.session_state.prize_df = prize_df
        st.session_state.draw_history = [] 
        st.session_state.current_group_results = [] 
        st.session_state.current_group_name = ""
        st.session_state.selected_group = None 

    if st.session_state.emp_df.empty:
         return 

    groups = st.session_state.emp_df['กลุ่มจับรางวัล'].unique().tolist()
    groups = [str(g).strip() for g in groups]
    groups = [g for g in groups if g != "" and g.lower() != "nan"]
    groups = sorted(list(set(groups))) 
    
    # ----------------------------------------------------
    # 3. ส่วนเลือกกลุ่ม (ปุ่มกด จัดกึ่งกลาง)
    # ----------------------------------------------------
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
        st.warning("⚠️ ไม่พบกลุ่มจับรางวัลที่ถูกต้องในไฟล์ข้อมูล โปรดตรวจสอบคอลัมน์ 'กลุ่มจับรางวัล' ในไฟล์พนักงานว่ามีข้อมูลหรือไม่")

    st.markdown("---")
    
    # ----------------------------------------------------
    # 4. ปุ่มสุ่มหลัก (จัดกึ่งกลาง)
    # ----------------------------------------------------
    if st.session_state.selected_group:
        selected_group = st.session_state.selected_group
        
        col_dummy_left, col_btn_center, col_dummy_right = st.columns([1, 1, 1])
        
        with col_btn_center:
            st.markdown(f"**💡 กลุ่มที่พร้อมสุ่ม:** <span style='color:#4beaff; font-weight:bold;'>{selected_group}</span>", unsafe_allow_html=True)

            if st.button(f"🔴 เริ่มสุ่มรางวัลกลุ่ม: **{selected_group}**", key="main_draw_btn", use_container_width=True):
                
                draw_results = run_draw(selected_group, st.session_state.emp_df, st.session_state.prize_df)
                
                if draw_results:
                    st.session_state.current_group_results = [] 
                    st.session_state.current_group_name = selected_group

                    st.subheader(f"✨ เริ่มการสุ่มกลุ่ม **{selected_group}** ✨")
                    
                    current_winner_box = st.empty() 
                    
                    col_left_balloons, col_center_content, col_right_balloons = st.columns([1, 4, 1])
                    
                    with col_left_balloons:
                        st.balloons() 
                    with col_right_balloons:
                        st.balloons() 
                        

                    for i, item in enumerate(draw_results):
                        
                        try:
                            (winner_name, winner_dept), prize = item
                        except (ValueError, TypeError):
                            st.error(f"❌ โครงสร้างข้อมูลผลลัพธ์ผิดพลาดในรายการที่ {i+1} : {item}")
                            continue
                        
                        # A. Show rolling animation 
                        with current_winner_box.container():
                            st.markdown(f"## 🥁 กำลังสุ่มผู้โชคดีรายการที่ **{i+1}**... 🥁") 
                        time.sleep(0.5)
                        
                        # B. Announce Winner (ชั่วคราว)
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
                            
                        # C. อัปเดตสถานะและเก็บประวัติ
                        idx_emp = st.session_state.emp_df.index[st.session_state.emp_df['ชื่อ-นามสกุล'] == winner_name].tolist()
                        if idx_emp:
                            st.session_state.emp_df.loc[idx_emp[0], 'สถานะ'] = 'ได้รับแล้ว'
                        
                        idx_prize = st.session_state.prize_df.index[st.session_state.prize_df['ชื่อของขวัญ'] == prize].tolist()
                        if idx_prize:
                            current_qty = st.session_state.prize_df.loc[idx_prize[0], 'จำนวนคงเหลือ']
                            st.session_state.prize_df.loc[idx_prize[0], 'จำนวนคงเหลือ'] = current_qty - 1
                        
                        result_item = (winner_name, winner_dept, prize)
                        st.session_state.draw_history.append({'ชื่อ-นามสกุล': winner_name, 
                                                              'แผนก': winner_dept, 
                                                              'รายการของขวัญ': prize})
                        st.session_state.current_group_results.append(result_item) 
                        
                        time.sleep(3.0) 
                        
                    # D. Grand Finale และ Rerun 
                    st.empty() 
                    
                    with col_left_balloons:
                        st.balloons()
                    with col_right_balloons:
                        st.balloons()
                        
                    st.success("✨🎉 **จบการสุ่มรางวัลกลุ่มนี้แล้ว!** ดูผลลัพธ์ถาวรด้านบน! 🎉✨")
                    st.rerun() 
        
    else:
         st.info("กรุณาเลือกกลุ่มจับรางวัลจากปุ่มด้านบนเพื่อเริ่มสุ่ม")
    
    st.markdown("---")


    # ----------------------------------------------------
    # 5. แสดงผลผู้โชคดีล่าสุด (รูปแบบ Card จัดเรียงแบบ Flexbox - ครึ่งจอ)
    # ----------------------------------------------------
    if st.session_state.current_group_results:
        
        summary_group_name = st.session_state.current_group_name.replace('<', '').replace('>', '').replace('(', '').replace(')', '').strip()
        
        col_summary_left, col_summary_center, col_summary_right = st.columns([1, 2, 1])
        
        with col_summary_center: 
            with st.container(border=True): 
                st.markdown(f"## ✅ สรุปผลผู้โชคดีกลุ่ม **{summary_group_name}** 🏆", unsafe_allow_html=True) 
                st.markdown("---")
    
                result_html = ""
                for i, (winner_name, winner_dept, prize) in enumerate(st.session_state.current_group_results):
                    
                    # *** แก้ไข: ลบการสร้าง QR Code รายบุคคลออก ***

                    bg_color = "#1f2a37" if i % 2 == 0 else "#253040" 
                    border_color = "#ff4b4b" if i % 2 == 0 else "#4beaff" 
    
                    result_html += f"""
                    <div style='
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center;
                        margin-bottom: 8px; 
                        padding: 10px 15px; 
                        border-radius: 8px; 
                        background-color: {bg_color}; 
                        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3); 
                        border-left: 5px solid {border_color}; 
                        transition: transform 0.2s;
                    '>
                        <div style='flex-grow: 1;'>
                            <span style='font-size: 1.8em; font-weight: 800; color: #ff4b4b; text-shadow: 1px 1px 1px #000; line-height: 1.1;'>
                                👤 {winner_name}
                            </span> 
                            <br>
                            <span style='font-size: 1.0em; color: #adb5bd;'>แผนก: {winner_dept}</span>
                        </div>
                        <div style='text-align: right; min-width: 35%; display: flex; align-items: center; justify-content: flex-end;'>
                            <div style='text-align: right; margin-right: 15px;'>
                                <span style='font-size: 1.2em; font-weight: bold; color: #ffffff; display: block; line-height: 1.1;'>
                                    🎁 รางวัล: 
                                </span>
                                <span style='font-size: 1.5em; font-weight: 800; color: #4beaff; display: block; line-height: 1.1;'>
                                    {prize}
                                </span>
                            </div>
                        </div>
                    </div>
                    """
                st.markdown(result_html, unsafe_allow_html=True)
                
        st.markdown("---") 

   # ----------------------------------------------------
    # 6. ส่วนแสดงผลประวัติ, ปุ่มดาวน์โหลด, และ QR Code สรุปผลรวม
    # ----------------------------------------------------
    if st.session_state.draw_history:
        st.subheader("⬇️ ไฟล์ผลรางวัลและการตรวจสอบ")
        
        # --- แสดง QR Code สรุปผล ---
        st.markdown("### 📢 QR Code สำหรับการตรวจสอบผลรางวัลรวม")
        
        # *** เปลี่ยนข้อความนี้เป็น URL สาธารณะจริงของคุณ ***
        # ใช้ URL ที่ขึ้นต้นด้วย https://
        summary_link = "https://raffle-draw-app-kstkwaon.streamlit.app"
        
        # สร้าง QR Code จาก URL ใหม่
        qr_base64_summary = create_qrcode_base64(summary_link)
        
        if qr_base64_summary:
            
            # ... (ส่วนแสดงผล QR Code เหมือนเดิม) ...
            
            # แบ่งคอลัมน์ [1 (ว่าง), 2 (QR), 1 (ว่าง)]
            col_qr_left, col_qr_center, col_qr_right = st.columns([1, 1, 1])
            
            with col_qr_center:
                # แสดงผล QR Code ด้วย HTML 
                st.markdown(f"""
                <div style='text-align: center; background-color: white; padding: 10px; border-radius: 5px; border: 2px solid #4beaff;'>
                    <img src="{qr_base64_summary}" alt="Summary QR Code" style="width: 200px; height: 200px; display: block; margin: auto;">
                    <p style='color: black; margin-top: 10px; font-weight: bold;'>สแกนเพื่อดูผลรางวัลทั้งหมด</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")


        excel_data = create_print_ready_excel()
        
        if excel_data:
            col_d_left, col_d_center, col_d_right = st.columns([1, 1, 1])
            with col_d_center:
                st.download_button(
                    label="✅ ดาวน์โหลดไฟล์ Excel (พร้อมช่องเซ็นต์รับ)",
                    data=excel_data,
                    file_name=f'Raffle_Results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        # แสดงตารางประวัติ (ซ่อนอยู่ภายใต้ Checkbox)
        if st.checkbox("แสดงตารางประวัติการสุ่มทั้งหมด (เพื่อการตรวจสอบ)", value=False):
             history_display_df = pd.DataFrame(st.session_state.draw_history)
             st.dataframe(history_display_df[['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ']], use_container_width=True)

if __name__ == '__main__':

    main()

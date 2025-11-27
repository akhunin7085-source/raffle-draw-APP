import streamlit as st
import pandas as pd
import numpy as np
import os
import io

# ----------------------------------------------------
# --- CONFIGURATION ---
# ----------------------------------------------------
EMPLOYEE_FILE = 'employees.csv'
PRIZE_FILE = 'prizes.csv'
HISTORY_FILE = 'draw_history.csv'

# Set wide layout and page title
st.set_page_config(layout="wide", page_title="LWS Raffle Draw App")

# ----------------------------------------------------
# --- FUNCTIONS ---
# ----------------------------------------------------

def load_data(emp_file=EMPLOYEE_FILE, prize_file=PRIZE_FILE):
    """Load employee and prize data from CSV files."""
    
    # Load Employee Data
    if os.path.exists(emp_file):
        df_emp = pd.read_csv(emp_file)
        if 'กลุ่มจับรางวัล' not in df_emp.columns:
            st.error(f"ไฟล์ {emp_file} ต้องมีคอลัมน์ชื่อ 'กลุ่มจับรางวัล'")
            return None, None
        if 'ชื่อ-นามสกุล' not in df_emp.columns:
            st.error(f"ไฟล์ {emp_file} ต้องมีคอลัมน์ชื่อ 'ชื่อ-นามสกุล'")
            return None, None
        if 'แผนก' not in df_emp.columns:
            st.error(f"ไฟล์ {emp_file} ต้องมีคอลัมน์ชื่อ 'แผนก'")
            return None, None
    else:
        st.error(f"ไม่พบไฟล์ข้อมูลพนักงาน: {emp_file}")
        return None, None

    # Load Prize Data
    if os.path.exists(prize_file):
        df_prize = pd.read_csv(prize_file)
        if 'ชื่อของขวัญ' not in df_prize.columns or 'จำนวนคงเหลือ' not in df_prize.columns or 'กลุ่มจับรางวัล' not in df_prize.columns:
            st.error(f"ไฟล์ {prize_file} ต้องมีคอลัมน์ 'ชื่อของขวัญ', 'จำนวนคงเหลือ', และ 'กลุ่มจับรางวัล'")
            return None, None
    else:
        st.error(f"ไม่พบไฟล์ข้อมูลของรางวัล: {prize_file}")
        return None, None
    
    # Clean up and validate
    df_emp['Drawn'] = False 
    
    return df_emp, df_prize

def load_history(history_file=HISTORY_FILE):
    """Load the history of drawn winners."""
    if os.path.exists(history_file):
        try:
            df_history = pd.read_csv(history_file)
            return df_history
        except Exception as e:
            st.warning(f"ไม่สามารถโหลดประวัติการสุ่มได้: {e}")
            return pd.DataFrame(columns=['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ', 'กลุ่มจับรางวัล'])
    else:
        return pd.DataFrame(columns=['ชื่อ-นามสกุล', 'แผนก', 'รายการของขวัญ', 'กลุ่มจับรางวัล'])

def save_history(df_history, history_file=HISTORY_FILE):
    """Save the updated history of drawn winners to CSV."""
    try:
        df_history.to_csv(history_file, index=False)
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการบันทึกประวัติ: {e}")

# ----------------------------------------------------
# --- SESSION STATE MANAGEMENT (Initialization) ---
# ----------------------------------------------------

if 'df_emp' not in st.session_state or 'df_prize' not in st.session_state:
    df_emp_loaded, df_prize_loaded = load_data()
    if df_emp_loaded is not None and df_prize_loaded is not None:
        st.session_state['df_emp'] = df_emp_loaded
        st.session_state['df_prize'] = df_prize_loaded
    else:
        st.stop() 

if 'draw_history' not in st.session_state:
    st.session_state['draw_history'] = load_history()

if 'remaining_prizes' not in st.session_state:
    st.session_state['remaining_prizes'] = st.session_state['df_prize'].set_index('ชื่อของขวัญ')['จำนวนคงเหลือ'].to_dict()

# ----------------------------------------------------
# --- MAIN DRAWING LOGIC ---
# ----------------------------------------------------

def perform_draw(selected_group, selected_prize, num_winners):
    df_emp = st.session_state['df_emp'].copy()
    
    # 1. Filter employees by group and not yet drawn
    eligible_employees = df_emp[
        (df_emp['กลุ่มจับรางวัล'] == selected_group) & 
        (df_emp['Drawn'] == False)
    ]
    
    if eligible_employees.empty:
        st.warning(f"ไม่มีพนักงานที่เข้าเกณฑ์ในกลุ่ม **{selected_group}** หรือถูกสุ่มไปหมดแล้ว")
        return

    if len(eligible_employees) < num_winners:
        st.warning(f"มีพนักงานที่เข้าเกณฑ์เพียง {len(eligible_employees)} คน แต่ต้องการสุ่ม {num_winners} คน")
        num_winners = len(eligible_employees)

    # 2. Perform Random Selection
    winners_df = eligible_employees.sample(n=num_winners, replace=False)

    # 3. Update Employee Data (Mark as Drawn)
    for index in winners_df.index:
        st.session_state['df_emp'].loc[index, 'Drawn'] = True
    
    # 4. Update Prize Count
    st.session_state['remaining_prizes'][selected_prize] -= num_winners
    
    # 5. Prepare New Winner History
    new_winners_data = []
    for index, row in winners_df.iterrows():
        new_winners_data.append({
            'ชื่อ-นามสกุล': row['ชื่อ-นามสกุล'],
            'แผนก': row['แผนก'],
            'รายการของขวัญ': selected_prize,
            'กลุ่มจับรางวัล': selected_group 
        })
    
    new_winners_df = pd.DataFrame(new_winners_data)
    
    # 6. Append and Save History
    st.session_state['draw_history'] = pd.concat([st.session_state['draw_history'], new_winners_df], ignore_index=True)
    save_history(st.session_state['draw_history']) 

    # Display Results
    st.balloons()
    st.success(f"🎉 สุ่มรางวัล **{selected_prize}** สำเร็จ! ได้ผู้โชคดี {num_winners} ท่าน")
    
    st.dataframe(new_winners_df, use_container_width=True)


# ----------------------------------------------------
# --- STREAMLIT UI ---
# ----------------------------------------------------

def main_app():
    st.title("🎰 ระบบจับฉลากรางวัล")
    st.markdown("---")
    
    # Extract unique groups from employee data
    all_groups = st.session_state['df_emp']['กลุ่มจับรางวัล'].unique().tolist()
    
    # --- Sidebar ---
    with st.sidebar:
        st.header("ข้อมูลคงเหลือ")
        
        for prize, count in st.session_state['remaining_prizes'].items():
            st.markdown(f"**{prize}**: {count} ชิ้น")
        
        st.markdown("---")
        st.header("สถิติพนักงาน")
        total_employees = len(st.session_state['df_emp'])
        drawn_employees = st.session_state['df_emp']['Drawn'].sum()
        remaining_employees = total_employees - drawn_employees
        
        st.markdown(f"**พนักงานทั้งหมด:** {total_employees} คน")
        st.markdown(f"**สุ่มไปแล้ว:** {drawn_employees} คน")
        st.markdown(f"**คงเหลือ:** {remaining_employees} คน")
        st.markdown("---")

    # --- Draw Controls ---
    st.header("ตั้งค่าการจับรางวัล")
    
    col1, col2, col3 = st.columns(3)
    
    # *** เริ่มส่วนที่แก้ไข: ใช้ Selectbox แทน Buttons ***
    with col1:
        selected_group = st.selectbox(
            "1. เลือกกลุ่มจับรางวัล",
            options=all_groups
        )
    # *** สิ้นสุดส่วนที่แก้ไข ***
        
    # Filter available prizes for the selected group
    available_prizes_for_group = st.session_state['df_prize'][
        (st.session_state['df_prize']['กลุ่มจับรางวัล'] == selected_group) & 
        (st.session_state['df_prize']['จำนวนคงเหลือ'] > 0)
    ]
    
    prize_options = available_prizes_for_group['ชื่อของขวัญ'].tolist()
    
    with col2:
        selected_prize = st.selectbox(
            "2. เลือกรายการของขวัญ",
            options=prize_options
        )
        
    # Get remaining quantity for the selected prize
    max_winners = st.session_state['remaining_prizes'].get(selected_prize, 0)
    
    # Calculate max possible winners (limited by remaining employees in the group)
    eligible_count = len(st.session_state['df_emp'][
        (st.session_state['df_emp']['กลุ่มจับรางวัล'] == selected_group) & 
        (st.session_state['df_emp']['Drawn'] == False)
    ])
    
    max_to_draw = min(max_winners, eligible_count)
    
    # *** แก้ไขส่วนนี้เพื่อแก้ปัญหา StreamlitMixedNumericTypesError ***
    with col3:
        # กำหนด min_value เป็น 0 หรือ 1 ขึ้นอยู่กับว่ามีของรางวัลให้สุ่มหรือไม่
        input_min_value = 1 if max_to_draw > 0 else 0
        # กำหนด value เริ่มต้นเป็น 1 หรือ 0
        input_value = min(1, max_to_draw) if max_to_draw > 0 else 0

        num_winners = st.number_input(
            "3. จำนวนผู้โชคดีที่ต้องการสุ่ม",
            min_value=input_min_value,
            max_value=max_to_draw,
            value=input_value,
            disabled=(max_to_draw == 0)
        )
    # *** สิ้นสุดการแก้ไขแก้ Error ***
    
    st.markdown("---")
    
    if st.button("🔴 สุ่มผู้โชคดี!", type="primary", use_container_width=True, disabled=(max_to_draw == 0)):
        if selected_prize and num_winners > 0:
            perform_draw(selected_group, selected_prize, num_winners)
        else:
            st.error("กรุณาเลือกของรางวัลและจำนวนผู้โชคดีที่ต้องการสุ่ม")

    if st.button("🔄 รีเซ็ตการสุ่มทั้งหมด (ยกเลิกข้อมูลผู้โชคดีทั้งหมด)"):
        if st.warning("คุณแน่ใจหรือไม่ว่าต้องการรีเซ็ตข้อมูลทั้งหมด? ข้อมูลผู้โชคดีจะถูกลบ!"):
             st.session_state.pop('df_emp')
             st.session_state.pop('draw_history')
             st.session_state.pop('remaining_prizes')
             
             if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
             
             st.rerun() 

if __name__ == '__main__':
    main_app()

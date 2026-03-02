import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CẤU HÌNH GIAO DIỆN TƯƠNG PHẢN CAO
st.set_page_config(page_title="Sổ Điểm Danh Pro", layout="wide")

st.markdown("""
    <style>
    /* Nền trắng sáng để chữ rõ nét nhất */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Khung chứa tên học sinh trong Nhật Ký */
    .student-header-box {
        background-color: #E7F1FF;
        padding: 15px;
        border-radius: 12px;
        border-left: 8px solid #007BFF;
        margin-bottom: 20px;
    }
    .student-header-name {
        color: #004085;
        font-size: 1.5rem !important;
        font-weight: 800;
        margin: 0;
    }

    /* Thẻ học sinh ở Tab Tổng hợp */
    .summary-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 18px;
        background-color: #F8F9FA;
        border-radius: 10px;
        margin-bottom: 8px;
        border: 1px solid #DEE2E6;
    }

    /* Màu số buổi xanh dương đậm */
    .total-count {
        color: #0056b3;
        font-weight: 800;
        font-size: 1.3rem;
    }

    /* Tên học sinh ở các mục khác */
    .st-student-name {
        font-weight: 700;
        color: #212529; /* Chữ gần đen để dễ đọc */
        font-size: 1.1rem;
    }

    /* Tab Label - Làm đậm chữ ở Tab */
    button[data-baseweb="tab"] p {
        font-weight: 700 !important;
        font-size: 1rem !important;
    }

    /* Tùy chỉnh Checkbox Điểm danh - To và Rõ */
    div[data-testid="stCheckbox"] {
        padding: 15px !important;
        border-radius: 10px !important;
        border: 2px solid #CED4DA !important;
        background-color: #FFFFFF !important;
        margin-bottom: 10px;
    }
    div[data-testid="stCheckbox"]:has(input:checked) {
        background-color: #E7F1FF !important;
        border-color: #007BFF !important;
    }
    div[data-testid="stCheckbox"] label p {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #1A1A1A !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- XỬ LÝ DỮ LIỆU (Giữ nguyên cấu trúc) ---
DATA_FILE = "attendance_data.csv"
STUDENT_FILE = "student_list.csv"
ADJUST_FILE = "adjustments.csv"

THU_VN = {'Monday': 'Thứ Hai', 'Tuesday': 'Thứ Ba', 'Wednesday': 'Thứ Tư', 'Thursday': 'Thứ Năm', 'Friday': 'Thứ Sáu', 'Saturday': 'Thứ Bảy', 'Sunday': 'Chủ Nhật'}

def load_data():
    if 'students' not in st.session_state:
        st.session_state.students = pd.read_csv(STUDENT_FILE)['name'].tolist() if os.path.exists(STUDENT_FILE) else []
    if 'attendance_df' not in st.session_state:
        st.session_state.attendance_df = pd.read_csv(DATA_FILE) if os.path.exists(DATA_FILE) else pd.DataFrame(columns=['Student', 'Date'])
    if 'adjustments' not in st.session_state:
        if os.path.exists(ADJUST_FILE):
            adj_df = pd.read_csv(ADJUST_FILE)
            st.session_state.adjustments = dict(zip(adj_df['Student'], adj_df['Value']))
        else:
            st.session_state.adjustments = {s: 0 for s in st.session_state.students}

def save_data():
    pd.DataFrame({'name': st.session_state.students}).to_csv(STUDENT_FILE, index=False)
    st.session_state.attendance_df.to_csv(DATA_FILE, index=False)
    pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']).to_csv(ADJUST_FILE, index=False)

load_data()

# --- GIAO DIỆN ---
st.markdown("<h2 style='text-align: center; color: #000000;'>📋 QUẢN LÝ ĐIỂM DANH</h2>", unsafe_allow_html=True)

tab1, tab_log, tab2, tab3 = st.tabs(["📍 ĐIỂM DANH", "📑 NHẬT KÝ", "📊 TỔNG HỢP", "⚙️ CÀI ĐẶT"])

# --- TAB 1: ĐIỂM DANH ---
with tab1:
    col_d, _ = st.columns([3, 2])
    with col_d:
        selected_date = st.date_input("Chọn ngày", label_visibility="collapsed")
    date_str = selected_date.strftime("%Y-%m-%d")
    st.markdown(f"🗓️ **{THU_VN.get(selected_date.strftime('%A'))}, {selected_date.strftime('%d/%m/%Y')}**")
    
    st.write("")
    for s in st.session_state.students:
        is_checked = not st.session_state.attendance_df[(st.session_state.attendance_df['Student'] == s) & (st.session_state.attendance_df['Date'] == date_str)].empty
        
        if st.checkbox(s, value=is_checked, key=f"ck_{s}_{date_str}"):
            if not is_checked:
                new_row = pd.DataFrame({'Student': [s], 'Date': [date_str]})
                st.session_state.attendance_df = pd.concat([st.session_state.attendance_df, new_row], ignore_index=True)
                save_data()
        else:
            if is_checked:
                st.session_state.attendance_df = st.session_state.attendance_df[~((st.session_state.attendance_df['Student'] == s) & (st.session_state.attendance_df['Date'] == date_str))]
                save_data()

# --- TAB 2: NHẬT KÝ (SỬA LẠI THEO YÊU CẦU) ---
with tab_log:
    if st.session_state.students:
        s_view = st.selectbox("Chọn học sinh:", st.session_state.students)
        history = st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s_view]
        
        # Ô TÊN HỌC SINH TO DỄ NHÌN
        st.markdown(f"""
            <div class="student-header-box">
                <p style="font-size: 0.9rem; color: #666; margin-bottom: 5px;">Đang xem nhật ký của:</p>
                <h1 class="student-header-name">👤 {s_view}</h1>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"**Tổng số buổi tích lịch:** <span style='color:#007bff; font-size:24px; font-weight:bold;'>{len(history)} buổi</span>", unsafe_allow_html=True)
        st.write("---")
        
        if not history.empty:
            sorted_days = sorted(history['Date'].tolist(), reverse=True)
            for d in sorted_days:
                dt = datetime.strptime(d, "%Y-%m-%d")
                st.markdown(f"🔹 **{THU_VN.get(dt.strftime('%A'))}**, {dt.strftime('%d/%m/%Y')}")

# --- TAB 3: TỔNG HỢP ---
with tab2:
    st.write("")
    for s in st.session_state.students:
        auto_count = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s])
        adj_val = st.session_state.adjustments.get(s, 0)
        total = auto_count + adj_val
        
        col_name, col_btns, col_res = st.columns([2.5, 1, 1.5])
        
        col_name.markdown(f"<div style='padding-top:8px;'><span class='st-student-name'>👤 {s}</span></div>", unsafe_allow_html=True)
        
        b1, b2 = col_btns.columns(2)
        if b1.button("➖", key=f"s_{s}"):
            if total > 0:
                st.session_state.adjustments[s] = adj_val - 1
                save_data(); st.rerun()
        if b2.button("➕", key=f"a_{s}"):
            st.session_state.adjustments[s] = adj_val + 1
            save_data(); st.rerun()
            
        col_res.markdown(f"<div style='text-align:right; padding-top:4px;'><span class='total-count'>{total} buổi</span></div>", unsafe_allow_html=True)
        st.markdown("<div style='height:1px; background-color:#DEE2E6; margin:4px 0px;'></div>", unsafe_allow_html=True)

# --- TAB 4: CÀI ĐẶT ---
with tab3:
    new_name = st.text_input("Nhập tên học sinh mới:")
    if st.button("Lưu học sinh"):
        if new_name and new_name not in st.session_state.students:
            st.session_state.students.append(new_name); st.session_state.adjustments[new_name] = 0
            save_data(); st.rerun()
    
    st.write("---")
    for s in st.session_state.students:
        c1, c2 = st.columns([5, 1])
        c1.write(f"👤 {s}")
        if c2.button("🗑️", key=f"d_{s}"):
            st.session_state.students.remove(s); save_data(); st.rerun()

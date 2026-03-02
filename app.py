import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Quản Lý Lớp Học", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    
    .header-box {
        background-color: #E7F1FF;
        padding: 15px;
        border-radius: 12px;
        border-left: 8px solid #28A745;
        margin-bottom: 20px;
    }
    
    .fee-card {
        background-color: #F8F9FA;
        padding: 15px;
        border-radius: 12px;
        border: 1px solid #DEE2E6;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .fee-amount {
        color: #28A745;
        font-weight: 800;
        font-size: 1.4rem;
    }

    .total-count {
        color: #0056b3;
        font-weight: 800;
        font-size: 1.1rem;
    }

    div[data-testid="stCheckbox"] {
        padding: 12px !important;
        border-radius: 10px !important;
        border: 2px solid #CED4DA !important;
        background-color: #FFFFFF !important;
        margin-bottom: 8px;
    }
    div[data-testid="stCheckbox"]:has(input:checked) {
        background-color: #E7F1FF !important;
        border-color: #007BFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- XỬ LÝ DỮ LIỆU ---
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

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h2 style='text-align: center; color: #000;'>📒 QUẢN LÝ LỚP HỌC</h2>", unsafe_allow_html=True)

tab1, tab_log, tab_sum, tab_total, tab3 = st.tabs(["📍 ĐIỂM DANH", "📑 NHẬT KÝ", "📊 TỔNG HỢP", "📊 TỔNG KẾT", "⚙️ CÀI ĐẶT"])

# --- TAB 1: ĐIỂM DANH ---
with tab1:
    selected_date = st.date_input("Chọn ngày", label_visibility="collapsed")
    date_str = selected_date.strftime("%Y-%m-%d")
    st.markdown(f"🗓️ **{THU_VN.get(selected_date.strftime('%A'))}, {selected_date.strftime('%d/%m/%Y')}**")
    
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

# --- TAB 2: NHẬT KÝ ---
with tab_log:
    if st.session_state.students:
        s_view = st.selectbox("Chọn học sinh xem lịch:", st.session_state.students)
        history = st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s_view]
        st.markdown(f"<div class='header-box'><h1 style='margin:0; color:#004085;'>👤 {s_view}</h1></div>", unsafe_allow_html=True)
        st.write(f"Tổng buổi từ lịch: **{len(history)} buổi**")
        if not history.empty:
            for d in sorted(history['Date'].tolist(), reverse=True):
                dt = datetime.strptime(d, "%Y-%m-%d")
                st.markdown(f"🔹 **{THU_VN.get(dt.strftime('%A'))}**, {dt.strftime('%d/%m/%Y')}")

# --- TAB 3: TỔNG HỢP ---
with tab_sum:
    st.markdown("### 📊 Chốt số buổi")
    for s in st.session_state.students:
        auto_count = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s])
        adj_val = st.session_state.adjustments.get(s, 0)
        total = auto_count + adj_val
        
        col_name, col_btns, col_res = st.columns([2.5, 1, 1.5])
        col_name.markdown(f"<div style='padding-top:8px;'><b>{s}</b></div>", unsafe_allow_html=True)
        
        b1, b2 = col_btns.columns(2)
        if b1.button("➖", key=f"s_{s}"):
            if total > 0:
                st.session_state.adjustments[s] = adj_val - 1
                save_data(); st.rerun()
        if b2.button("➕", key=f"a_{s}"):
            st.session_state.adjustments[s] = adj_val + 1
            save_data(); st.rerun()
            
        col_res.markdown(f"<div style='text-align:right; padding-top:4px;'><span class='total-count'>{total} buổi</span></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:4px 0px; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

# --- TAB 4: TỔNG KẾT (ĐÃ SỬA) ---
with tab_total:
    st.markdown("### 📊 Tổng kết")
    
    # Lựa chọn cách tính
    mode = st.radio("Chế độ tính:", ["Tính tất cả", "Chọn từng học sinh"], horizontal=True)
    
    # Ô nhập số tiền chung
    unit_price = st.number_input("Nhập số:", min_value=0, value=0, step=1000)
    
    st.write("---")
    
    grand_total = 0
    
    # Lọc danh sách hiển thị
    display_students = st.session_state.students
    if mode == "Chọn từng học sinh":
        display_students = st.multiselect("Chọn học sinh cần tính:", st.session_state.students, default=st.session_state.students)

    for s in display_students:
        auto_count = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s])
        adj_val = st.session_state.adjustments.get(s, 0)
        total_sessions = auto_count + adj_val
        
        # Tính tiền
        student_money = total_sessions * unit_price
        grand_total += student_money
        
        # Hiển thị thẻ
        st.markdown(f"""
            <div class="fee-card">
                <div>
                    <b style="font-size:1.1rem;">👤 {s}</b><br>
                    <small>Số buổi: {total_sessions} buổi x {unit_price:,}</small>
                </div>
                <div class="fee-amount">{student_money:,}</div>
            </div>
            """, unsafe_allow_html=True)
            
    st.divider()
    st.markdown(f"<h3 style='text-align:right;'>Tổng: <span style='color:#28A745;'>{grand_total:,}</span></h3>", unsafe_allow_html=True)

# --- TAB 5: CÀI ĐẶT ---
with tab3:
    new_name = st.text_input("Thêm học sinh mới:")
    if st.button("Lưu học sinh"):
        if new_name and new_name not in st.session_state.students:
            st.session_state.students.append(new_name); st.session_state.adjustments[new_name] = 0
            save_data(); st.rerun()
    st.write("---")
    for s in st.session_state.students:
        c1, c2 = st.columns([5, 1])
        c1.write(f"• {s}")
        if c2.button("🗑️", key=f"d_{s}"):
            st.session_state.students.remove(s); save_data(); st.rerun()

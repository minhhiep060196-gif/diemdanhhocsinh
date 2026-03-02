import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Cấu hình trang
st.set_page_config(page_title="Sổ Điểm Danh Thông Minh", layout="wide")

# Tên file lưu trữ
DATA_FILE = "attendance_data.csv"
STUDENT_FILE = "student_list.csv"
ADJUST_FILE = "adjustments.csv" # Lưu số buổi cộng/trừ thêm

# --- HÀM XỬ LÝ DỮ LIỆU ---
def load_data():
    if 'students' not in st.session_state:
        if os.path.exists(STUDENT_FILE):
            st.session_state.students = pd.read_csv(STUDENT_FILE)['name'].tolist()
        else:
            st.session_state.students = []
            
    if 'attendance_df' not in st.session_state:
        if os.path.exists(DATA_FILE):
            st.session_state.attendance_df = pd.read_csv(DATA_FILE)
        else:
            st.session_state.attendance_df = pd.DataFrame(columns=['Student', 'Date'])

    if 'adjustments' not in st.session_state:
        if os.path.exists(ADJUST_FILE):
            adj_df = pd.read_csv(ADJUST_FILE)
            st.session_state.adjustments = dict(zip(adj_df['Student'], adj_df['Value']))
        else:
            st.session_state.adjustments = {}

def save_all():
    pd.DataFrame({'name': st.session_state.students}).to_csv(STUDENT_FILE, index=False)
    st.session_state.attendance_df.to_csv(DATA_FILE, index=False)
    adj_df = pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value'])
    adj_df.to_csv(ADJUST_FILE, index=False)

load_data()

# --- GIAO DIỆN SIDEBAR (CÀI ĐẶT) ---
with st.sidebar:
    st.header("⚙️ Cài đặt lớp học")
    new_student = st.text_input("Thêm học sinh mới:", placeholder="Nhập họ tên...")
    if st.button("➕ Thêm vào danh sách"):
        if new_student and new_student not in st.session_state.students:
            st.session_state.students.append(new_student)
            st.session_state.adjustments[new_student] = 0
            save_all()
            st.rerun()
    
    st.divider()
    st.subheader("Danh sách lớp")
    for s in st.session_state.students:
        cols = st.columns([4, 1])
        cols[0].write(f"👤 {s}")
        if cols[1].button("🗑️", key=f"del_{s}"):
            st.session_state.students.remove(s)
            if s in st.session_state.adjustments: del st.session_state.adjustments[s]
            save_all()
            st.rerun()

# --- GIAO DIỆN CHÍNH ---
st.title("📚 Quản Lý Buổi Học Học Sinh")

tab1, tab2 = st.tabs(["📍 Điểm danh hàng ngày", "📊 Bảng tổng hợp chuyên cần"])

# --- TAB 1: ĐIỂM DANH ---
with tab1:
    col_date, _ = st.columns([2, 2])
    with col_date:
        # Lịch Việt Nam
        selected_date = st.date_input("Chọn ngày điểm danh:", datetime.now())
        date_vn = selected_date.strftime("%d/%m/%Y")
        date_iso = selected_date.strftime("%Y-%m-%d")
    
    st.info(f"Đang điểm danh cho ngày: **{date_vn}**")
    
    if not st.session_state.students:
        st.warning("Vui lòng thêm học sinh ở cột bên trái trước.")
    else:
        # Hiển thị danh sách checkbox
        for s in st.session_state.students:
            # Kiểm tra xem đã tích chưa
            is_checked = not st.session_state.attendance_df[
                (st.session_state.attendance_df['Student'] == s) & 
                (st.session_state.attendance_df['Date'] == date_iso)
            ].empty
            
            checked = st.checkbox(f"Học sinh: **{s}**", value=is_checked, key=f"chk_{s}_{date_iso}")
            
            # Cập nhật dữ liệu khi bấm
            if checked and not is_checked:
                new_row = pd.DataFrame({'Student': [s], 'Date': [date_iso]})
                st.session_state.attendance_df = pd.concat([st.session_state.attendance_df, new_row], ignore_index=True)
                save_all()
            elif not checked and is_checked:
                st.session_state.attendance_df = st.session_state.attendance_df[
                    ~((st.session_state.attendance_df['Student'] == s) & (st.session_state.attendance_df['Date'] == date_iso))
                ]
                save_all()

# --- TAB 2: TỔNG HỢP ---
with tab2:
    st.header("Bảng tổng kết số buổi")
    
    if not st.session_state.students:
        st.write("Chưa có dữ liệu.")
    else:
        # Tạo bảng dữ liệu hiển thị
        for s in st.session_state.students:
            # Tính số buổi từ lịch
            auto_count = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s])
            # Lấy số buổi điều chỉnh (cộng/trừ thêm)
            adj_val = st.session_state.adjustments.get(s, 0)
            total = auto_count + adj_val
            
            # Hiển thị hàng ngang
            col_name, col_auto, col_ctrl, col_total = st.columns([3, 2, 3, 2])
            
            col_name.write(f"**{s}**")
            col_auto.write(f"Từ lịch: `{auto_count}`")
            
            # Cụm nút Cộng/Trừ
            c1, c2, c3 = col_ctrl.columns([1,1,1])
            if c1.button("➖", key=f"sub_{s}"):
                st.session_state.adjustments[s] = adj_val - 1
                save_all()
                st.rerun()
            c2.write(f"{adj_val:+}") # Hiển thị dạng +1 hoặc -1
            if c3.button("➕", key=f"add_{s}"):
                st.session_state.adjustments[s] = adj_val + 1
                save_all()
                st.rerun()
                
            col_total.subheader(f"{total} buổi")
            st.divider()

st.caption("Ứng dụng tự động lưu dữ liệu mỗi khi bạn thay đổi.")

import streamlit as st
import pandas as pd
import os

# Tên file lưu trữ dữ liệu
DATA_FILE = "attendance_data.csv"
STUDENT_FILE = "student_list.csv"

# Hàm tải dữ liệu
def load_data():
    if os.path.exists(STUDENT_FILE):
        st.session_state.students = pd.read_csv(STUDENT_FILE)['name'].tolist()
    else:
        st.session_state.students = []
        
    if os.path.exists(DATA_FILE):
        st.session_state.attendance_df = pd.read_csv(DATA_FILE)
    else:
        st.session_state.attendance_df = pd.DataFrame(columns=['Student', 'Date', 'Status'])

# Hàm lưu dữ liệu
def save_data():
    pd.DataFrame({'name': st.session_state.students}).to_csv(STUDENT_FILE, index=False)
    st.session_state.attendance_df.to_csv(DATA_FILE, index=False)

if 'students' not in st.session_state:
    load_data()

st.title("📲 Quản lý Điểm danh Online")

tab1, tab2, tab3 = st.tabs(["📍 Điểm danh", "📊 Tổng hợp", "⚙️ Cài đặt"])

with tab3:
    st.subheader("Danh sách học sinh")
    name = st.text_input("Thêm tên học sinh:")
    if st.button("Thêm"):
        if name and name not in st.session_state.students:
            st.session_state.students.append(name)
            save_data()
            st.rerun()
    
    for s in st.session_state.students:
        cols = st.columns([3, 1])
        cols[0].write(s)
        if cols[1].button("Xóa", key=f"del_{s}"):
            st.session_state.students.remove(s)
            save_data()
            st.rerun()

with tab1:
    date = st.date_input("Chọn ngày").strftime("%Y-%m-%d")
    for s in st.session_state.students:
        # Kiểm tra trạng thái đã lưu
        is_checked = not st.session_state.attendance_df[(st.session_state.attendance_df['Student'] == s) & 
                                                       (st.session_state.attendance_df['Date'] == date)].empty
        
        val = st.checkbox(f"Học sinh: {s}", value=is_checked, key=f"ck_{s}_{date}")
        
        # Cập nhật DataFrame
        if val and not is_checked:
            new_row = pd.DataFrame({'Student': [s], 'Date': [date], 'Status': [True]})
            st.session_state.attendance_df = pd.concat([st.session_state.attendance_df, new_row])
            save_data()
        elif not val and is_checked:
            st.session_state.attendance_df = st.session_state.attendance_df[~((st.session_state.attendance_df['Student'] == s) & 
                                                                           (st.session_state.attendance_df['Date'] == date))]
            save_data()

with tab2:
    st.subheader("Tổng số buổi học")
    if not st.session_state.attendance_df.empty:
        summary = st.session_state.attendance_df.groupby('Student').size().reset_index(name='Tổng buổi')
        st.table(summary)
    else:
        st.write("Chưa có dữ liệu điểm danh.")

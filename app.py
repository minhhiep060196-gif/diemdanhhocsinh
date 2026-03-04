import streamlit as st
import pandas as pd
import requests
import base64
import os

# --- CẤU HÌNH GITHUB ---
# Các thông tin này bạn sẽ điền vào mục Settings -> Secrets trên Streamlit Cloud
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"] # Ví dụ: minhhiep060196-gif/LOP5D
FILE_ATTENDANCE = "attendance_data.csv"
FILE_STUDENTS = "student_list.csv"
FILE_ADJUST = "adjustments.csv"

def save_to_github(file_name, df):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_name}"
    content = df.to_csv(index=False)
    
    # Lấy SHA để ghi đè file
    r = requests.get(url, headers={"Authorization": f"token {GITHUB_TOKEN}"})
    sha = r.json().get("sha", None)
    
    payload = {
        "message": f"Update {file_name} from App",
        "content": base64.b64encode(content.encode()).decode(),
        "sha": sha
    }
    requests.put(url, json=payload, headers={"Authorization": f"token {GITHUB_TOKEN}"})

# --- PHẦN QUẢN LÝ DỮ LIỆU ---
def load_data():
    if 'students' not in st.session_state:
        # Thử đọc từ GitHub, nếu lỗi thì tạo danh sách trống
        try:
            url = f"https://raw.githubusercontent.com/{REPO_NAME}/chính/{FILE_STUDENTS}"
            st.session_state.students = pd.read_csv(url)['name'].tolist()
        except:
            st.session_state.students = []

    if 'attendance_df' not in st.session_state:
        try:
            url = f"https://raw.githubusercontent.com/{REPO_NAME}/chính/{FILE_ATTENDANCE}"
            st.session_state.attendance_df = pd.read_csv(url)
        except:
            st.session_state.attendance_df = pd.DataFrame(columns=['Student', 'Date'])

    if 'adjustments' not in st.session_state:
        try:
            url = f"https://raw.githubusercontent.com/{REPO_NAME}/chính/{FILE_ADJUST}"
            adj_df = pd.read_csv(url)
            st.session_state.adjustments = dict(zip(adj_df['Student'], adj_df['Value']))
        except:
            st.session_state.adjustments = {s: 0 for s in st.session_state.students}

def save_all_data():
    # Lưu danh sách học sinh
    save_to_github(FILE_STUDENTS, pd.DataFrame({'name': st.session_state.students}))
    # Lưu điểm danh
    save_to_github(FILE_ATTENDANCE, st.session_state.attendance_df)
    # Lưu điều chỉnh số buổi
    df_adj = pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value'])
    save_to_github(FILE_ADJUST, df_adj)

load_data()

# --- GIAO DIỆN CHÍNH (GIỮ NGUYÊN NHƯ BẢN TRƯỚC CỦA BẠN) ---
# ... (Bạn dán phần giao diện Tabs và tính toán tiền vào đây) ...
# Lưu ý: Mỗi khi nhấn nút Lưu hoặc tính tiền, hãy gọi hàm save_all_data()

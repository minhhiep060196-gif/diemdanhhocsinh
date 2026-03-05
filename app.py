import streamlit as st
import pandas as pd
import requests
import base64
import io
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Quản Lý Lớp Học LOP5D", layout="wide")

# Lấy cấu hình từ Secrets
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
    BRANCH = st.secrets.get("BRANCH", "main")
    APP_TITLE = st.secrets.get("APP_TITLE", "QUẢN LÝ LỚP HỌC LOP5D")
except:
    st.error("⚠️ Thiếu cấu hình Secrets! Vui lòng kiểm tra lại Settings > Secrets.")
    st.stop()

STUDENT_FILE = "student_list.csv"
DATA_FILE = "attendance_data.csv"
ADJUST_FILE = "adjustments.csv"

# --- 2. HÀM XỬ LÝ GITHUB ---
def get_github_file(file_name):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_name}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode('utf-8')
        return pd.read_csv(io.StringIO(content))
    return None

def save_to_github(file_name, df):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r_get = requests.get(url + f"?ref={BRANCH}", headers=headers)
    sha = r_get.json().get("sha") if r_get.status_code == 200 else None
    content_encoded = base64.b64encode(df.to_csv(index=False).encode()).decode()
    payload = {"message": f"Update {file_name}", "content": content_encoded, "branch": BRANCH}
    if sha: payload["sha"] = sha
    requests.put(url, json=payload, headers=headers)

# --- 3. KHỞI TẠO DỮ LIỆU ---
THU_VN = {'Monday': 'Thứ Hai', 'Tuesday': 'Thứ Ba', 'Wednesday': 'Thứ Tư', 'Thursday': 'Thứ Năm', 'Friday': 'Thứ Sáu', 'Saturday': 'Thứ Bảy', 'Sunday': 'Chủ Nhật'}

if 'students' not in st.session_state:
    df = get_github_file(STUDENT_FILE)
    st.session_state.students = df['name'].tolist() if df is not None else []
if 'attendance_df' not in st.session_state:
    df = get_github_file(DATA_FILE)
    st.session_state.attendance_df = df if df is not None else pd.DataFrame(columns=['Student', 'Date'])
if 'adjustments' not in st.session_state:
    df = get_github_file(ADJUST_FILE)
    if df is not None:
        st.session_state.adjustments = dict(zip(df['Student'].astype(str), df['Value']))
    else:
        st.session_state.adjustments = {str(s): 0 for s in st.session_state.students}

# --- 4. GIAO DIỆN CHÍNH ---
st.markdown(f"<h2 style='text-align: center; color: #000;'>📒 {APP_TITLE}</h2>", unsafe_allow_html=True)
tab1, tab_log, tab_sum, tab_total, tab_set = st.tabs(["📍 ĐIỂM DANH", "📑 NHẬT KÝ", "📊 TỔNG HỢP", "💰 TỔNG KẾT", "⚙️ CÀI ĐẶT"])

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
                save_to_github(DATA_FILE, st.session_state.attendance_df)
        else:
            if is_checked:
                st.session_state.attendance_df = st.session_state.attendance_df[~((st.session_state.attendance_df['Student'] == s) & (st.session_state.attendance_df['Date'] == date_str))]
                save_to_github(DATA_FILE, st.session_state.attendance_df)

with tab_log:
    if st.session_state.students:
        s_view = st.selectbox("Chọn học học sinh:", st.session_state.students)
        history = st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s_view]
        st.write(f"Tổng buổi: {len(history)}")
        for d in sorted(history['Date'].tolist(), reverse=True):
            st.write(f"🔹 {d}")

with tab_sum:
    st.markdown("### 📊 Chốt buổi")
    for s in st.session_state.students:
        auto = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s])
        adj = st.session_state.adjustments.get(str(s), 0)
        c1, c2, c3 = st.columns([2, 1, 1])
        c1.write(f"**{s}**: {auto + adj} buổi")
        if c2.button("➕", key=f"a_{s}"):
            st.session_state.adjustments[str(s)] = adj + 1
            save_to_github(ADJUST_FILE, pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']))
            st.rerun()
        if c3.button("➖", key=f"s_{s}"):
            st.session_state.adjustments[str(s)] = adj - 1
            save_to_github(ADJUST_FILE, pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']))
            st.rerun()

with tab_total:
    price = st.number_input("Giá 1 buổi:", min_value=0, value=0)
    for s in st.session_state.students:
        total = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s]) + st.session_state.adjustments.get(str(s), 0)
        st.write(f"👤 {s}: {total * price:,}đ")

with tab_set:
    name = st.text_input("Tên học sinh mới:")
    if st.button("Lưu"):
        if name and name not in st.session_state.students:
            st.session_state.students.append(name)
            st.session_state.adjustments[str(name)] = 0
            save_to_github(STUDENT_FILE, pd.DataFrame({'name': st.session_state.students}))
            save_to_github(ADJUST_FILE, pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']))
            st.rerun()

import streamlit as st
import pandas as pd
import requests
import base64
import io  # QUAN TRỌNG: Sửa lỗi AttributeError
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
        return pd.read_csv(io.StringIO(content)) # Dùng io.StringIO để sửa lỗi
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

def load_data():
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

load_data()

# --- 4. GIAO DIỆN CHÍNH ---
st.markdown(f"<h2 style='text-align: center; color: #000;'>📒 {APP_TITLE}</h2>", unsafe_allow_html=True)
tab1, tab_log, tab_sum, tab_total, tab3 = st.tabs(["📍 ĐIỂM DANH", "📑 NHẬT KÝ", "📊 TỔNG HỢP", "📊 TỔNG KẾT", "⚙️ CÀI ĐẶT"])

# --- NỘI DUNG CÁC TAB (GIỮ NGUYÊN NHƯ BẢN BẠN GỬI) ---
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
        s_view = st.selectbox("Chọn học sinh xem lịch:", st.session_state.students)
        history = st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s_view]
        st.write(f"Tổng buổi: **{len(history)} buổi**")
        if not history.empty:
            for d in sorted(history['Date'].tolist(), reverse=True):
                dt = datetime.strptime(d, "%Y-%m-%d")
                st.markdown(f"🔹 **{THU_VN.get(dt.strftime('%A'))}**, {dt.strftime('%d/%m/%Y')}")

with tab_sum:
    st.markdown("### 📊 Chốt số buổi")
    for s in st.session_state.students:
        auto_count = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s])
        adj_val = st.session_state.adjustments.get(str(s), 0)
        total = auto_count + adj_val
        col1, col2, col3 = st.columns([2, 1, 1])
        col1.write(f"**{s}**")
        if col2.button("➕", key=f"add_{s}"):
            st.session_state.adjustments[str(s)] = adj_val + 1
            save_to_github(ADJUST_FILE, pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']))
            st.rerun()
        if col3.button("➖", key=f"sub_{s}"):
            st.session_state.adjustments[str(s)] = max(-20, adj_val - 1)
            save_to_github(ADJUST_FILE, pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']))
            st.rerun()

with tab_total:
    st.markdown("### 💰 Tổng kết tiền")
    unit_price = st.number_input("Giá 1 buổi (đ):", min_value=0, value=0, step=1000)
    grand_total = 0
    for s in st.session_state.students:
        count = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s]) + st.session_state.adjustments.get(str(s), 0)
        money = count * unit_price
        grand_total += money
        st.write(f"👤 {s}: {count} buổi = **{money:,}đ**")
    st.divider()
    st.markdown(f"### Tổng cộng: {grand_total:,}đ")

with tab3:
    new_name = st.text_input("Thêm học sinh mới:")
    if st.button("Lưu"):
        if new_name and new_name not in st.session_state.students:
            st.session_state.students.append(new_name)
            st.session_state.adjustments[str(new_name)] = 0
            save_to_github(STUDENT_FILE, pd.DataFrame({'name': st.session_state.students}))
            save_to_github(ADJUST_FILE, pd.DataFrame(list(st.





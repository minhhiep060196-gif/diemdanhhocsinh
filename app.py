import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Quản Lý Lớp Học LOP5D", layout="wide")

# Lấy cấu hình từ Secrets
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    REPO_NAME = st.secrets["REPO_NAME"]
except:
    st.error("Thiếu cấu hình Secrets! Hãy thêm GITHUB_TOKEN và REPO_NAME vào Settings > Secrets trên Streamlit Cloud.")
    st.stop()

BRANCH = "chính" 
FILES = {
    "attendance": "attendance_data.csv",
    "students": "student_list.csv",
    "adjustments": "adjustments.csv"
}

st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; }
    .header-box { background-color: #E7F1FF; padding: 15px; border-radius: 12px; border-left: 8px solid #28A745; margin-bottom: 20px; }
    .fee-card { background-color: #F8F9FA; padding: 15px; border-radius: 12px; border: 1px solid #DEE2E6; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    .fee-amount { color: #28A745; font-weight: 800; font-size: 1.4rem; }
    .total-count { color: #0056b3; font-weight: 800; font-size: 1.1rem; }
    div[data-testid="stCheckbox"] { padding: 12px !important; border-radius: 10px !important; border: 2px solid #CED4DA !important; background-color: #FFFFFF !important; margin-bottom: 8px; }
    div[data-testid="stCheckbox"]:has(input:checked) { background-color: #E7F1FF !important; border-color: #007BFF !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HÀM XỬ LÝ DỮ LIỆU GITHUB ---
def get_github_file(file_name):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_name}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        content = base64.b64decode(r.json()["content"]).decode('utf-8')
        return pd.read_csv(pd.compat.StringIO(content)), r.json()["sha"]
    return None, None

def save_to_github(file_name, df):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r_get = requests.get(url + f"?ref={BRANCH}", headers=headers)
    sha = r_get.json().get("sha") if r_get.status_code == 200 else None
    content_base64 = base64.b64encode(df.to_csv(index=False).encode()).decode()
    payload = {"message": f"Update {file_name}", "content": content_base64, "branch": BRANCH}
    if sha: payload["sha"] = sha
    requests.put(url, json=payload, headers=headers)

# --- 3. KHỞI TẠO DỮ LIỆU ---
def init_data():
    if 'students' not in st.session_state:
        df, _ = get_github_file(FILES["students"])
        st.session_state.students = df['name'].tolist() if df is not None else []
    if 'attendance_df' not in st.session_state:
        df, _ = get_github_file(FILES["attendance"])
        st.session_state.attendance_df = df if df is not None else pd.DataFrame(columns=['Student', 'Date'])
    if 'adjustments' not in st.session_state:
        df, _ = get_github_file(FILES["adjustments"])
        if df is not None:
            st.session_state.adjustments = dict(zip(df['Student'].astype(str), df['Value']))
        else:
            st.session_state.adjustments = {str(s): 0 for s in st.session_state.students}

init_data()

# --- 4. GIAO DIỆN CHÍNH ---
st.markdown("<h2 style='text-align: center;'>📒 QUẢN LÝ LỚP HỌC LOP5D</h2>", unsafe_allow_html=True)
tab1, tab_log, tab_sum, tab_total, tab_set = st.tabs(["📍 ĐIỂM DANH", "📑 NHẬT KÝ", "📊 TỔNG HỢP", "💰 TỔNG KẾT", "⚙️ CÀI ĐẶT"])

# TAB 1: ĐIỂM DANH
with tab1:
    selected_date = st.date_input("Chọn ngày", value=datetime.now())
    date_str = selected_date.strftime("%Y-%m-%d")
    for s in st.session_state.students:
        is_checked = not st.session_state.attendance_df[(st.session_state.attendance_df['Student'] == s) & (st.session_state.attendance_df['Date'] == date_str)].empty
        if st.checkbox(s, value=is_checked, key=f"ck_{s}_{date_str}"):
            if not is_checked:
                new_row = pd.DataFrame({'Student': [s], 'Date': [date_str]})
                st.session_state.attendance_df = pd.concat([st.session_state.attendance_df, new_row], ignore_index=True)
                save_to_github(FILES["attendance"], st.session_state.attendance_df)
        else:
            if is_checked:
                st.session_state.attendance_df = st.session_state.attendance_df[~((st.session_state.attendance_df['Student'] == s) & (st.session_state.attendance_df['Date'] == date_str))]
                save_to_github(FILES["attendance"], st.session_state.attendance_df)

# TAB 3: TỔNG HỢP (Chốt số buổi)
with tab_sum:
    st.markdown("### 📊 Chốt số buổi")
    for s in st.session_state.students:
        auto_count = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s])
        adj_val = st.session_state.adjustments.get(str(s), 0)
        total = auto_count + adj_val
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"<div style='padding-top:10px;'><b>{s}</b>: {total} buổi</div>", unsafe_allow_html=True)
        if c2.button("➕", key=f"add_{s}"):
            st.session_state.adjustments[str(s)] = adj_val + 1
            save_to_github(FILES["adjustments"], pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']))
            st.rerun()
        if c3.button("➖", key=f"sub_{s}"):
            st.session_state.adjustments[str(s)] = max(0, adj_val - 1)
            save_to_github(FILES["adjustments"], pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']))
            st.rerun()

# TAB 4: TỔNG KẾT (Giao diện mới theo yêu cầu)
with tab_total:
    st.markdown("### 💰 Tổng kết học phí")
    mode = st.radio("Chế độ:", ["Tính tất cả", "Chọn từng học sinh"], horizontal=True)
    unit_price = st.number_input("Nhập số tiền 1 buổi (đ):", min_value=0, value=0, step=1000)
    display_list = st.session_state.students
    if mode == "Chọn từng học sinh":
        display_list = st.multiselect("Chọn học sinh:", st.session_state.students, default=st.session_state.students)
    
    grand_total = 0
    for s in display_list:
        count = len(st.session_state.attendance_df[st.session_state.attendance_df['Student'] == s]) + st.session_state.adjustments.get(str(s), 0)
        money = count * unit_price
        grand_total += money
        st.markdown(f"<div class='fee-card'><div><b>👤 {s}</b><br><small>{count} buổi x {unit_price:,}đ</small></div><div class='fee-amount'>{money:,}đ</div></div>", unsafe_allow_html=True)
    st.divider()
    st.markdown(f"<h3 style='text-align:right;'>Tổng: <span style='color:#28A745;'>{grand_total:,}đ</span></h3>", unsafe_allow_html=True)

# TAB 5: CÀI ĐẶT
with tab_set:
    new_name = st.text_input("Thêm học sinh mới:")
    if st.button("Lưu học sinh"):
        if new_name and new_name not in st.session_state.students:
            st.session_state.students.append(new_name)
            st.session_state.adjustments[str(new_name)] = 0
            save_to_github(FILES["students"], pd.DataFrame({'name': st.session_state.students}))
            save_to_github(FILES["adjustments"], pd.DataFrame(list(st.session_state.adjustments.items()), columns=['Student', 'Value']))
            st.rerun()
    st.divider()
    for s in st.session_state.students:
        c1, c2 = st.columns([5, 1])
        c1.write(f"• {s}")
        if c2.button("🗑️", key=f"del_{s}"):
            st.session_state.students.remove(s)
            save_to_github(FILES["students"], pd.DataFrame({'name': st.session_state.students}))
            st.rerun()

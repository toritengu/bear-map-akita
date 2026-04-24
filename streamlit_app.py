import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Bear Safety Map Akita", page_icon="🐻")

# --- データベース機能 ---
DB_FILE = "bear_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # 空のファイルだった場合の処理
        if df.empty:
            return []
        return df.to_dict('records')
    return []

def save_all_data(data_list):
    df = pd.DataFrame(data_list)
    df.to_csv(DB_FILE, index=False)

if 'bear_reports' not in st.session_state:
    st.session_state.bear_reports = load_data()

SHOP_COORD = (39.71225270635445, 140.11889314232894)

st.title("🐻 Bear Safety Map Akita")

# --- サイドバー：店主専用（入力と管理） ---
with st.sidebar:
    st.header("🛠 店主専用パネル")
    master_password = st.secrets.get("PASSWORD", "admin123")
    pw_input = st.text_input("パスワード", type="password")
    
    if pw_input == master_password:
        st.success("認証完了")
        
        tab1, tab2 = st.tabs(["新規登録", "データ管理"])
        
        with tab1:
            st.info("地図をタップして場所を指定してください")
            if 'clicked_lat' not in st.session_state:
                st.session_state.clicked_lat, st.session_state.clicked_lon = 39.715, 140.120

            with st.form("input_form", clear_on_submit=True):
                st.write(f"座標: {round(st.session_state.clicked_lat, 4)}, {round(st.session_state.clicked_lon, 4)}")
                input_date = st.date_input("目撃日", datetime.now())
                input_time = st.time_input("目撃時間")
                input_place = st.text_input("場所の名称")
                input_detail = st.text_area("詳細")
                
                if st.form_submit_button("この場所にピンを立てる"):
                    new_data = {
                        "date": input_date.strftime("%Y-%m-%d"),
                        "time": input_time.strftime("%H:%M"),
                        "place_jp": input_place,
                        "lat": st.session_state.clicked_lat,
                        "lon": st.session_state.clicked_lon,
                        "detail_jp": input_detail,
                    }
                    st.session_state.bear_reports.insert(0, new_data)
                    save_all_data(st.session_state.bear_reports)
                    st.rerun()

        with tab2:
            st.subheader("登録済みデータの削除")
            if not st.session_state.bear_reports:
                st.write("データがありません")
            else:
                for i, b in enumerate(st.session_state.bear_reports):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(f"{b['date']} {b['place_jp']}")
                    with col2:
                        if st.button("削除", key=f"del_{i}"):
                            st.session_state.bear_reports.pop(i)
                            save_all_data(st.session_state.bear_reports)
                            st.rerun()
    else:
        st.warning("パスワードを入力してください")

# --- メイン画面：地図 ---
search_radius = st.slider("表示範囲 (km)", 1, 30, 5)
days_range = st.selectbox("表示対象期間", [3, 7, 14, 30], index=1)

m = folium.Map(location=SHOP_COORD, zoom_start=13)
folium.Marker(SHOP_COORD, icon=folium.Icon(color="blue", icon="home"), tooltip="鳥天狗").add_to(m)

# フィルタリングとピン立て
today = datetime.now()
threshold_date = today - timedelta(days=days_range)
display_list = []

for i, b in enumerate(st.session_state.bear_reports):
    b_date = datetime.strptime(b["date"], "%Y-%m-%d")
    dist = geodesic(SHOP_COORD, (b["lat"], b["lon"])).km
    if b_date >= threshold_date and dist <= search_radius:
        b["current_dist"] = round(dist, 1)
        display_list.append(b)
        folium.Marker(
            [b["lat"], b["lon"]],
            icon=folium.DivIcon(html=f'<div style="background:#e60000; color:white; border-radius:50%; width:24px; height:24px; text-align:center; line-height:24px; font-weight:bold; border:2px solid white;">{len(display_list)}</div>'),
        ).add_to(m)

st_data = st_folium(m, width=700, height=500)

if st_data and st_data.get("last_clicked"):
    st.session_state.clicked_lat = st_data["last_clicked"]["lat"]
    st.session_state.clicked_lon = st_data["last_clicked"]["lng"]
    st.rerun()

if display_list:
    st.markdown("### 📋 詳細リスト")
    for i, b in enumerate(display_list):
        with st.expander(f"No.{i+1} 📍 鳥天狗から {b['current_dist']} km"):
            st.write(f"📅 **日時:** {b['date']} {b['time']}")
            st.write(f"📍 **場所:** {b['place_jp']}")
            st.write(f"💬 **詳細:** {b['detail_jp']}")

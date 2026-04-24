import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import folium_static, st_folium  # st_foliumを追加
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Bear Safety Map Akita", page_icon="🐻")

# --- データベース機能 ---
DB_FILE = "bear_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE).to_dict('records')
    return []

def save_data(new_record):
    data = load_data()
    data.insert(0, new_record)
    pd.DataFrame(data).to_csv(DB_FILE, index=False)
    return data

if 'bear_reports' not in st.session_state:
    st.session_state.bear_reports = load_data()

# 鳥天狗の座標
SHOP_COORD = (39.71225270635445, 140.11889314232894)

st.title("🐻 Bear Safety Map Akita")
st.subheader("クマ安心距離チェッカー / Real-time Bear Alert")

# --- サイドバー：店主専用入力 ---
with st.sidebar:
    st.header("🛠 店主専用入力")
    master_password = st.secrets.get("PASSWORD", "admin123")
    pw_input = st.text_input("パスワード", type="password")
    
    if pw_input == master_password:
        st.success("認証完了")
        st.info("👇 下の地図をタップして場所を指定してください")
        
        # セッションでクリック座標を保持
        if 'clicked_lat' not in st.session_state:
            st.session_state.clicked_lat = 39.715
        if 'clicked_lon' not in st.session_state:
            st.session_state.clicked_lon = 140.120

        with st.form("input_form", clear_on_submit=True):
            # 表示のみ（クリックで連動）
            st.write(f"選択中の座標: {round(st.session_state.clicked_lat, 4)}, {round(st.session_state.clicked_lon, 4)}")
            
            input_date = st.date_input("目撃日", datetime.now())
            input_time = st.time_input("目撃時間")
            input_place = st.text_input("場所の名称 (例: ○○公園付近)")
            input_detail = st.text_area("詳細 (例: クマ2頭)")
            
            if st.form_submit_button("この場所にピンを立てる"):
                new_data = {
                    "date": input_date.strftime("%Y-%m-%d"),
                    "time": input_time.strftime("%H:%M"),
                    "place_jp": input_place,
                    "lat": st.session_state.clicked_lat,
                    "lon": st.session_state.clicked_lon,
                    "detail_jp": input_detail,
                }
                st.session_state.bear_reports = save_data(new_data)
                st.balloons()
                
                # SNS投稿用テキスト
                x_text = f"【クマ目撃情報】\n{input_time.strftime('%H:%M')}頃、{input_place}にて目撃情報あり。\n詳細：{input_detail}\n鳥天狗へお越しのお客様は十分ご注意ください。\n#秋田市 #クマ出没 #鳥天狗"
                st.code(x_text, language="text")
    else:
        st.warning("パスワードを入力してください")

# --- メイン画面：地図 ---
search_radius = st.slider("表示範囲 (km)", 1, 30, 5)

# 編集用マップの作成（クリック取得用）
m = folium.Map(location=SHOP_COORD, zoom_start=13)
folium.Marker(SHOP_COORD, icon=folium.Icon(color="blue", icon="home"), tooltip="鳥天狗").add_to(m)

# 登録済みピンを表示
for i, b in enumerate(st.session_state.bear_reports):
    dist = geodesic(SHOP_COORD, (b["lat"], b["lon"])).km
    if dist <= search_radius:
        folium.Marker(
            [b["lat"], b["lon"]],
            icon=folium.DivIcon(html=f'<div style="background:#e60000; color:white; border-radius:50%; width:24px; height:24px; text-align:center; line-height:24px; font-weight:bold; border:2px solid white;">{i+1}</div>'),
        ).add_to(m)

# 地図を表示し、クリックイベントを取得
st_data = st_folium(m, width=700, height=500)

# クリックされたら座標を保存して再描画
if st_data and st_data.get("last_clicked"):
    st.session_state.clicked_lat = st_data["last_clicked"]["lat"]
    st.session_state.clicked_lon = st_data["last_clicked"]["lng"]
    st.rerun()

if st.session_state.bear_reports:
    st.markdown("### 📋 詳細リスト")
    for i, b in enumerate(st.session_state.bear_reports):
        dist = round(geodesic(SHOP_COORD, (b["lat"], b["lon"])).km, 1)
        if dist <= search_radius:
            with st.expander(f"No.{i+1} 📍 鳥天狗から {dist} km"):
                st.write(f"📅 **日時:** {b['date']} {b['time']}")
                st.write(f"📍 **場所:** {b['place_jp']}")
                st.write(f"💬 **詳細:** {b['detail_jp']}")

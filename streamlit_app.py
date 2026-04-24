import streamlit as st
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta
import os

# ページ設定
st.set_page_config(page_title="Bear Safety Map Akita", page_icon="🐻")

# --- 簡易データベース機能（テキストファイル保存） ---
DB_FILE = "bear_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        return df.to_dict('records')
    return []

def save_data(new_record):
    data = load_data()
    data.insert(0, new_record)
    df = pd.DataFrame(data)
    df.to_csv(DB_FILE, index=False)
    return data

# 初期データ読み込み
if 'bear_reports' not in st.session_state:
    st.session_state.bear_reports = load_data()

# 【確定座標】鳥天狗
SHOP_COORD = (39.71225270635445, 140.11889314232894)
SHOP_NAME_JP = "鳥天狗"
SHOP_NAME_EN = "Toritengu"

# --- サイドバー：店主専用入力 ---
with st.sidebar:
    st.header("🛠 店主専用：情報入力")
    
    # パスワードチェック（後でStreamlitの設定画面でパスワードを決めます）
    master_password = st.secrets.get("PASSWORD", "admin123") # 設定前は admin123
    pw_input = st.text_input("パスワードを入力", type="password")
    
    if pw_input == master_password:
        st.success("認証完了")
        with st.form("input_form", clear_on_submit=True):
            input_date = st.date_input("目撃日", datetime.now())
            input_time = st.time_input("目撃時間")
            input_place = st.text_input("場所 (例: エリアなかいち付近)")
            input_lat = st.number_input("緯度", value=39.715, format="%.6f")
            input_lon = st.number_input("経度", value=140.120, format="%.6f")
            input_detail = st.text_area("詳細 (例: 1mと80cmの2頭)")
            
            if st.form_submit_button("情報を登録・投稿文作成"):
                new_data = {
                    "date": input_date.strftime("%Y-%m-%d"),
                    "time": input_time.strftime("%H:%M"),
                    "place_jp": input_place,
                    "lat": input_lat,
                    "lon": input_lon,
                    "detail_jp": input_detail,
                }
                st.session_state.bear_reports = save_data(new_data)
                st.balloons()
                
                # X（旧Twitter）投稿用テキスト
                x_text = f"【クマ目撃情報】\n{input_time.strftime('%H:%M')}頃、{input_place}にて目撃情報あり。\n詳細：{input_detail}\n鳥天狗へお越しのお客様は十分ご注意ください。\n#秋田市 #クマ出没 #鳥天狗"
                st.code(x_text, language="text")
    else:
        st.warning("パスワードを入力してください")

# --- メイン画面 ---
st.title("🐻 Bear Safety Map Akita")
st.subheader("クマ安心距離チェッカー / Real-time Bear Alert")

days_range = st.selectbox("表示対象期間", [3, 7, 14, 30], index=1, format_func=lambda x: f"直近 {x} 日間")
search_radius = st.slider("検索範囲 (km)", 1, 30, 5)

def display_map(radius, days):
    my_coord = SHOP_COORD
    today = datetime.now()
    threshold_date = today - timedelta(days=days)
    
    near_bears = []
    
    # フィルタリング
    for b in st.session_state.bear_reports:
        b_date = datetime.strptime(b["date"], "%Y-%m-%d")
        dist = geodesic(my_coord, (b["lat"], b["lon"])).km
        if b_date >= threshold_date and dist <= radius:
            b["current_dist"] = round(dist, 1)
            near_bears.append(b)

    # 地図描画
    zoom_level = 15 if radius <= 2 else 13 if radius <= 5 else 12 if radius <= 10 else 10
    m = folium.Map(location=my_coord, zoom_start=zoom_level)
    folium.Marker(my_coord, icon=folium.Icon(color="blue", icon="home"), tooltip=SHOP_NAME_JP).add_to(m)

    for i, b in enumerate(near_bears):
        folium.Marker(
            [b["lat"], b["lon"]],
            icon=folium.DivIcon(html=f'<div style="background:#e60000; color:white; border-radius:50%; width:24px; height:24px; text-align:center; line-height:24px; font-weight:bold; border:2px solid white;">{i+1}</div>'),
        ).add_to(m)

    if near_bears:
        st.error(f"⚠️ **CAUTION: {len(near_bears)} sightings found.**\n\n**【注意】直近{days}日間・半径{radius}km以内に {len(near_bears)} 件の情報があります。**")
    else:
        st.success(f"✅ **CLEAR: No sightings found.**\n\n**【安全】直近{days}日間・半径{radius}km以内に情報はありません。**")

    folium_static(m, width=700, height=450)

    if near_bears:
        st.markdown(f"### 📋 詳細情報")
        st.info(f"📏 距離は「鳥天狗」からの直線距離です。")
        for i, b in enumerate(near_bears):
            with st.expander(f"No.{i+1} 📍 {b['current_dist']} km from Toritengu"):
                st.write(f"📅 **日時:** {b['date']} {b['time']}")
                st.write(f"📍 **場所:** {b['place_jp']}")
                st.write(f"💬 **詳細:** {b['detail_jp']}")

display_map(search_radius, days_range)

st.divider()
st.caption("※店主が直接入力した周辺情報を表示しています。")

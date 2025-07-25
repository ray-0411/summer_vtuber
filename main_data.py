import sqlite3
import pandas as pd
import streamlit as st

# 連線資料庫
db_path = "data.db"
with sqlite3.connect(db_path) as conn:
    # 讀取所有資料
    df = pd.read_sql_query("SELECT * FROM main", conn)

# 轉成時間戳記方便排序
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])

# 建立頻道選單
channels = sorted(df['channel'].unique())
selected_channel = st.selectbox("請選擇頻道", channels)

# 篩選出該頻道的所有紀錄
df_selected = df[df['channel'] == selected_channel].copy()

# 顯示平均
yt_avg = df_selected[df_selected['youtube'] >= 10]['youtube'].mean()
tw_avg = df_selected[df_selected['twitch'] >= 10]['twitch'].mean()

yt_avg_display = f"{yt_avg:.1f}" if not pd.isna(yt_avg) else "無資料"
tw_avg_display = f"{tw_avg:.1f}" if not pd.isna(tw_avg) else "無資料"


col1, col2 = st.columns(2)
col1.metric("📺 YouTube 平均觀看數", yt_avg_display)
col2.metric("🎮 Twitch 平均觀看數", tw_avg_display)

# 顯示該頻道的所有紀錄（可排序）
st.subheader(f"{selected_channel} 的觀看紀錄")
df_display = df_selected[['datetime', 'youtube', 'twitch', 'yt_number', 'tw_number']].sort_values('datetime')
st.dataframe(df_display, use_container_width=True)

import sqlite3
import pandas as pd
import streamlit as st

# 連線資料庫
db_path = "data.db"
with sqlite3.connect(db_path) as conn:
    # 讀取所有資料
    df = pd.read_sql_query("SELECT * FROM main", conn)
    df_streamer = pd.read_sql_query("SELECT * FROM streamer", conn)



# 轉成時間戳記方便排序
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])


# 根據 streamer.channel_id 排序，只留下在 main 表出現過的頻道
streamer_channels = df_streamer['channel_id'].tolist()
channels_in_data = df['channel'].unique()
channels = [ch for ch in streamer_channels if ch in channels_in_data]

# 建立頻道名稱與 ID 的對應字典
channel_dict = df_streamer.set_index('channel_name')['channel_id'].to_dict()

# 中文選單
selected_name = st.selectbox("請選擇頻道", list(channel_dict.keys()))
selected_channel = channel_dict[selected_name]  # 對應 channel_id

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

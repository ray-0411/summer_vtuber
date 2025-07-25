import sqlite3
import pandas as pd
import streamlit as st

# 資料庫路徑
db_path = "data.db"

# 讀取資料
with sqlite3.connect(db_path) as conn:
    df = pd.read_sql_query("SELECT * FROM main", conn)
    df_streamer = pd.read_sql_query("SELECT * FROM streamer", conn)

# 合併日期與時間
df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'])

# 🔽 檢視模式選單
view_mode = st.selectbox("選擇檢視模式", ["總觀看統計","單一頻道"])

# ---------- 單一頻道模式 ----------
if view_mode == "單一頻道":
    # 頻道依 streamer.channel_id 排序
    streamer_channels = df_streamer['channel_id'].tolist()
    channels_in_data = df['channel'].unique()
    channels = [ch for ch in streamer_channels if ch in channels_in_data]

    selected_channel = st.selectbox("請選擇頻道", channels)
    df_selected = df[df['channel'] == selected_channel].copy()

    # 平均觀看數（排除 <10）
    yt_avg = df_selected[df_selected['youtube'] >= 10]['youtube'].mean()
    tw_avg = df_selected[df_selected['twitch'] >= 10]['twitch'].mean()

    yt_avg_display = f"{yt_avg:.1f}" if not pd.isna(yt_avg) else "無資料"
    tw_avg_display = f"{tw_avg:.1f}" if not pd.isna(tw_avg) else "無資料"

    col1, col2 = st.columns(2)
    col1.metric("📺 YouTube 平均觀看數", yt_avg_display)
    col2.metric("🎮 Twitch 平均觀看數", tw_avg_display)

    # YouTube 統計
    df_youtube = df_selected[df_selected['yt_number'] != 0]
    df_yt_summary = df_youtube.groupby('yt_number').agg(
        yt_avg=('youtube', lambda x: x[x >= 10].mean()),
        count=('datetime', 'count'),
        start_time=('datetime', 'min'),
        end_time=('datetime', 'max')
    ).reset_index()
    df_yt_summary.columns = ['YouTube 直播 ID', 'YouTube 平均觀看數', '筆數', '開始時間', '結束時間']

    # Twitch 統計
    df_twitch = df_selected[df_selected['tw_number'] != 0]
    df_tw_summary = df_twitch.groupby('tw_number').agg(
        tw_avg=('twitch', lambda x: x[x >= 10].mean()),
        count=('datetime', 'count'),
        start_time=('datetime', 'min'),
        end_time=('datetime', 'max')
    ).reset_index()
    df_tw_summary.columns = ['Twitch 直播 ID', 'Twitch 平均觀看數', '筆數', '開始時間', '結束時間']

    # 顯示表格
    st.markdown("### 📺 YouTube 直播統計")
    st.dataframe(
        df_yt_summary.style.format({"YouTube 平均觀看數": "{:.1f}"}),
        use_container_width=True
    )

    st.markdown("### 🎮 Twitch 直播統計")
    st.dataframe(
        df_tw_summary.style.format({"Twitch 平均觀看數": "{:.1f}"}),
        use_container_width=True
    )

# ---------- 總統計模式 ----------
elif view_mode == "總觀看統計":
    st.subheader("📊 所有頻道的平均觀看統計")

    # 取 streamer 資料
    df_streamer = df_streamer[['channel_id', 'channel_name']]
    valid_channels = df_streamer['channel_id'].tolist()

    # 過濾 main 表只保留出現在 streamer 的頻道
    df_filtered = df[df['channel'].isin(valid_channels)].copy()

    # 平均統計（先用 channel_id 為主）
    grouped = df_filtered.groupby('channel').agg(
        yt_avg=('youtube', lambda x: x[x >= 10].mean()),
        tw_avg=('twitch', lambda x: x[x >= 10].mean()),
        count=('datetime', 'count')
    ).reset_index()

    # merge streamer 表取得中文名
    grouped = grouped.merge(df_streamer, left_on='channel', right_on='channel_id', how='left')

    # 根據 streamer.channel_id 的順序排序
    grouped['order'] = grouped['channel_id'].apply(lambda x: valid_channels.index(x))
    grouped = grouped.sort_values('order')
    
    # 重新排序 index，讓前面數字正常
    grouped = grouped.reset_index(drop=True)

    # 選擇與顯示欄位
    grouped = grouped[['channel_name', 'yt_avg', 'tw_avg', 'count']]
    grouped.columns = ['頻道', 'YouTube 平均觀看數', 'Twitch 平均觀看數', '紀錄筆數']

    st.dataframe(
        grouped.style.format({
            "YouTube 平均觀看數": "{:.1f}",
            "Twitch 平均觀看數": "{:.1f}"
        }),
        use_container_width=True
    )

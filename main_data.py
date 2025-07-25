import sqlite3
import pandas as pd
import streamlit as st

#streamlit run main_data.py

# 資料庫路徑
db_path = "data.db"

# 讀取資料
with sqlite3.connect(db_path) as conn:
    df = pd.read_sql_query("SELECT * FROM main", conn)
    df_streamer = pd.read_sql_query("SELECT * FROM streamer", conn)
    df_stream = pd.read_sql_query("SELECT * FROM stream", conn)

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
        yt_max=('youtube', lambda x: x[x >= 10].max()),
        yt_min=('youtube', lambda x: x[x >= 10].min()),
        count=('datetime', 'count'),
        start_time=('datetime', 'min'),
        end_time=('datetime', 'max')
    ).reset_index()
    df_yt_summary.columns = ['直播ID', '平均觀看數', '最大觀看數', '最小觀看數', '資料筆數', '開始時間', '結束時間']

    # Twitch 統計
    df_twitch = df_selected[df_selected['tw_number'] != 0]
    df_tw_summary = df_twitch.groupby('tw_number').agg(
        tw_avg=('twitch', lambda x: x[x >= 10].mean()),
        tw_max=('twitch', lambda x: x[x >= 10].max()),
        tw_min=('twitch', lambda x: x[x >= 10].min()),
        count=('datetime', 'count'),
        start_time=('datetime', 'min'),
        end_time=('datetime', 'max')
    ).reset_index()
    df_tw_summary.columns = ['直播ID', '平均觀看數', '最大觀看數', '最小觀看數', '資料筆數', '開始時間', '結束時間']

    # 轉成字串欄位，方便顯示
    df_yt_summary['日期'] = df_yt_summary['開始時間'].dt.strftime("%Y-%m-%d").fillna("")
    df_yt_summary['開始時間_str'] = df_yt_summary['開始時間'].dt.strftime("%H:%M").fillna("")
    df_yt_summary['結束時間_str'] = df_yt_summary['結束時間'].dt.strftime("%H:%M").fillna("")

    df_tw_summary['日期'] = df_tw_summary['開始時間'].dt.strftime("%Y-%m-%d").fillna("")
    df_tw_summary['開始時間_str'] = df_tw_summary['開始時間'].dt.strftime("%H:%M").fillna("")
    df_tw_summary['結束時間_str'] = df_tw_summary['結束時間'].dt.strftime("%H:%M").fillna("")

    # 刪除 datetime 原欄位（若還有）
    df_yt_summary.drop(columns=['開始時間', '結束時間'], inplace=True)
    df_tw_summary.drop(columns=['開始時間', '結束時間'], inplace=True)

    # 合併直播名稱（stream表）
    df_yt_summary = pd.merge(df_yt_summary, df_stream[['id', 'name']], how='left', left_on='直播ID', right_on='id')
    df_tw_summary = pd.merge(df_tw_summary, df_stream[['id', 'name']], how='left', left_on='直播ID', right_on='id')

    # 顯示 YouTube 統計（拆成三欄）
    st.markdown("### 📺 YouTube 直播統計")
    st.dataframe(
        df_yt_summary[[
            '直播ID', '平均觀看數', '最大觀看數', '最小觀看數',
            '資料筆數', '日期', '開始時間_str', '結束時間_str', 'name'
        ]].rename(columns={
            'name': '直播名稱',
            '開始時間_str': '開始時間',
            '結束時間_str': '結束時間',
        }).style.format({
            "平均觀看數": "{:.1f}",
            "最大觀看數": "{:.0f}",
            "最小觀看數": "{:.0f}"
        }),
        use_container_width=True
    )

    st.markdown("### ➕ 新增資料到 same_stream")

    with st.form("add_same_stream_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            from_id = st.number_input("來源 ID（from_id）", min_value=1, step=1)
        with col2:
            to_id = st.number_input("合併至 ID（to_id）", min_value=1, step=1)

        submitted = st.form_submit_button("新增")
        if submitted:
            try:
                with sqlite3.connect(db_path) as conn:
                    conn.execute("INSERT INTO same_stream (from_id, to_id) VALUES (?, ?)", (from_id, to_id))
                    st.success(f"✅ 已成功新增 from_id = {from_id} → to_id = {to_id}")
            except Exception as e:
                st.error(f"❌ 新增失敗：{e}")

    # 顯示 Twitch 統計（拆成三欄）
    st.markdown("### 🎮 Twitch 直播統計")
    st.dataframe(
        df_tw_summary[[
            '直播ID', '平均觀看數', '最大觀看數', '最小觀看數',
            '資料筆數', '日期', '開始時間_str', '結束時間_str', 'name'
        ]].rename(columns={
            'name': '直播名稱',
            '開始時間_str': '開始時間',
            '結束時間_str': '結束時間',
        }).style.format({
            "平均觀看數": "{:.1f}",
            "最大觀看數": "{:.0f}",
            "最小觀看數": "{:.0f}"
        }),
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

    # YouTube 直播場數計算（非0的 yt_number 計數）
    yt_counts = df_filtered[df_filtered['yt_number'] != 0].groupby('channel')['yt_number'].nunique().rename('YouTube 直播場數')

    # Twitch 直播場數計算（非0的 tw_number 計數）
    tw_counts = df_filtered[df_filtered['tw_number'] != 0].groupby('channel')['tw_number'].nunique().rename('Twitch 直播場數')


    # 平均統計（先用 channel_id 為主）
    grouped = df_filtered.groupby('channel').agg(
        yt_avg=('youtube', lambda x: x[x >= 10].mean()),
        tw_avg=('twitch', lambda x: x[x >= 10].mean()),
        count=('datetime', 'count')
    ).reset_index()
    
    # 合併直播場數
    grouped = grouped.merge(yt_counts, on='channel', how='left')
    grouped = grouped.merge(tw_counts, on='channel', how='left')

    # merge streamer 表取得中文名
    grouped = grouped.merge(df_streamer, left_on='channel', right_on='channel_id', how='left')

    # 根據 streamer.channel_id 的順序排序
    grouped['order'] = grouped['channel_id'].apply(lambda x: valid_channels.index(x))
    grouped = grouped.sort_values('order')
    
    # 重新排序 index，讓前面數字正常
    grouped = grouped.reset_index(drop=True)

    # 填補直播場數的 NaN 為 0
    grouped['YouTube 直播場數'] = grouped['YouTube 直播場數'].fillna(0).astype(int)
    grouped['Twitch 直播場數'] = grouped['Twitch 直播場數'].fillna(0).astype(int)


    # 選擇與顯示欄位
    grouped = grouped[['channel_name', 'yt_avg', 'tw_avg', 'count', 'YouTube 直播場數', 'Twitch 直播場數']]
    grouped.columns = ['頻道', 'YouTube 平均觀看數', 'Twitch 平均觀看數', '紀錄筆數', 'YouTube 直播場數', 'Twitch 直播場數']


    st.dataframe(
        grouped.style.format({
            "YouTube 平均觀看數": "{:.1f}",
            "Twitch 平均觀看數": "{:.1f}"
        }),
        use_container_width=True
    )

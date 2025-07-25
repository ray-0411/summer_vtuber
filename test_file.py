import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
import plotly.graph_objects as go

# --- Streamlit UI ---
st.title("直播資料抓取日誌")
db_path = "data.db"  # ← 你的 SQLite 檔案

# 連線抓資料
with sqlite3.connect(db_path) as conn:
    df_all = pd.read_sql_query("SELECT * FROM working", conn)

# 檢查欄位
timestamp_col = 'time'  # 確認你時間欄位叫這個
df_all[timestamp_col] = pd.to_datetime(df_all[timestamp_col])
available_dates = sorted(df_all[timestamp_col].dt.date.unique())

# 選擇日期
selected_date = st.date_input("選擇基準日期（從中午開始）", value=available_dates[-1], min_value=available_dates[0], max_value=available_dates[-1])
selected_datetime = datetime.combine(selected_date, datetime.strptime("12:00:00", "%H:%M:%S").time())

# 建立從中午到隔天中午的 96 個時間區段（每 15 分鐘）
time_slots = [selected_datetime + timedelta(minutes=15 * i) for i in range(96)]
start_range = time_slots[0]
end_range = time_slots[-1]

# 篩選該區段資料
df_range = df_all[(df_all[timestamp_col] >= start_range) & (df_all[timestamp_col] <= end_range)]
df_range['rounded'] = df_range[timestamp_col].dt.floor('15min')
captured_times = set(df_range['rounded'])
flags = [1 if t in captured_times else 0 for t in time_slots]

# 建表畫圖
plot_df = pd.DataFrame({
    "時間": time_slots,
    "有資料": flags
})

fig = go.Figure()
fig.add_trace(go.Bar(
    x=plot_df["時間"],
    y=plot_df["有資料"],
    marker_color=['green' if v == 1 else 'lightgray' for v in flags],
    hoverinfo='x+y',
    showlegend=False,
))

fig.update_layout(
    title=f"抓取紀錄：{start_range.strftime('%Y-%m-%d %H:%M')} ➜ {end_range.strftime('%Y-%m-%d %H:%M')}",
    xaxis_title="時間",
    yaxis=dict(showticklabels=False),
    bargap=0.1,
    height=300,
    margin=dict(l=40, r=40, t=60, b=40),
    xaxis=dict(
        tickangle=45,
        rangeslider=dict(visible=True),  # ✅ 可滑動時間軸
        tickformat="%m-%d %H:%M",
        tickfont=dict(size=12)
    ),
    title_font=dict(size=20),
    xaxis_title_font=dict(size=16),
)

st.plotly_chart(fig, use_container_width=True)

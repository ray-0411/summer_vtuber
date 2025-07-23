import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

# --- Streamlit UI ---
st.title("直播資料抓取日誌")
db_path = "data.db"  # 改成你的資料庫路徑

# 選擇日期
with sqlite3.connect(db_path) as conn:
    df_all = pd.read_sql_query("SELECT time FROM working", conn)

df_all['time'] = pd.to_datetime(df_all['time'])
available_dates = sorted(df_all['time'].dt.date.unique())

selected_date = st.date_input("選擇日期", value=available_dates[-1], min_value=available_dates[0], max_value=available_dates[-1])
selected_date_str = selected_date.strftime("%Y-%m-%d")

# --- 過濾並處理資料 ---
df_day = df_all[df_all['time'].dt.date == selected_date]

start_time = datetime.strptime(f"{selected_date_str} 00:00:00", "%Y-%m-%d %H:%M:%S")
time_slots = [start_time + timedelta(minutes=15 * i) for i in range(96)]

df_day['rounded'] = df_day['time'].dt.floor('15min')
captured_times = set(df_day['rounded'])
flags = [1 if t in captured_times else 0 for t in time_slots]

# --- 畫圖 ---
fig, ax = plt.subplots(figsize=(12, 2))
ax.imshow([flags], cmap='Greens', aspect='auto')
ax.set_yticks([])
ax.set_xticks(np.linspace(0, 95, 13))
ax.set_xticklabels([(start_time + timedelta(minutes=15 * int(i))).strftime("%H:%M") for i in np.linspace(0, 95, 13)])
ax.set_title(f"抓取紀錄 - {selected_date_str}")
ax.set_xlabel("時間")

st.pyplot(fig)

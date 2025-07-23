import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

# --- Streamlit UI ---
st.title("直播資料抓取日誌")
db_path = "data.db"  # ← 請改成你的實際檔案路徑

# 連線抓資料
with sqlite3.connect(db_path) as conn:
    df_all = pd.read_sql_query("SELECT * FROM working", conn)

# 確認欄位名稱
st.write("欄位：", df_all.columns.tolist())

# 假設你時間欄位是 'time'
timestamp_col = 'time'  # ← 改成實際欄位名
df_all[timestamp_col] = pd.to_datetime(df_all[timestamp_col])
available_dates = sorted(df_all[timestamp_col].dt.date.unique())

# 選擇日期（以中午為基準）
selected_date = st.date_input("選擇基準日期（從中午開始）", value=available_dates[-1], min_value=available_dates[0], max_value=available_dates[-1])
selected_datetime = datetime.combine(selected_date, datetime.strptime("12:00:00", "%H:%M:%S").time())

# 建立從當天中午 → 隔天中午的 15 分鐘區間（共 96 個）
time_slots = [selected_datetime + timedelta(minutes=15 * i) for i in range(96)]

# 篩選該區段資料
start_range = time_slots[0]
end_range = time_slots[-1]
df_range = df_all[(df_all[timestamp_col] >= start_range) & (df_all[timestamp_col] <= end_range)]

# 四捨五入到 15 分鐘
df_range['rounded'] = df_range[timestamp_col].dt.floor('15min')
captured_times = set(df_range['rounded'])

# 產生 0-1 資料
flags = [1 if t in captured_times else 0 for t in time_slots]

# 畫圖（橫向拉長）
fig, ax = plt.subplots(figsize=(50, 6))  # ← 調整這裡可以拉更長

ax.imshow([flags], cmap='Greens', aspect='auto')
ax.set_yticks([])
xtick_locs = np.linspace(0, 95, 13)  # 每 2 小時顯示一次
xtick_labels = [(time_slots[int(i)].strftime("%m-%d %H:%M")) for i in xtick_locs]
ax.set_xticks(xtick_locs)
ax.set_xticklabels(xtick_labels, rotation=45)

ax.set_title(f"抓取紀錄：{start_range.strftime('%Y-%m-%d %H:%M')} ➜ {end_range.strftime('%Y-%m-%d %H:%M')}")
ax.set_xlabel("時間")
st.pyplot(fig)

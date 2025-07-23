import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime
import matplotlib.ticker as ticker
from matplotlib.dates import DateFormatter
import matplotlib

# 設定中文字體（Windows 用 微軟正黑體）
matplotlib.rcParams['font.family'] = 'Microsoft JhengHei'

# 連接資料庫
conn = sqlite3.connect("data.db")
cursor = conn.cursor()

# 指定日期
date = '2025-07-08'

# 抓取資料
cursor.execute('''
    SELECT time, "create", kind
    FROM working
    WHERE time LIKE ?
    ORDER BY time
''', (f'{date}%',))
rows = cursor.fetchall()
conn.close()

# 整理資料
times = [datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") for row in rows]
creates = [float(row[1]) for row in rows]
kinds = [row[2] if row[2] else '未知' for row in rows]

# 顏色對應
kind_color_map = {
    '手動': "#23f4e9",
    '排程': "#4eff0e",
    '啟動': "#ecf337",
    '未知': "#ff1f1f"
}

# 畫圖
plt.figure(figsize=(12, 6))
plt.plot(times, creates, color='gray', linewidth=1, alpha=0.5, label='Create 折線')

for kind_label in kind_color_map:
    xs = [t for t, k in zip(times, kinds) if k == kind_label]
    ys = [c for c, k in zip(creates, kinds) if k == kind_label]
    if xs:
        plt.scatter(xs, ys,
                    color=kind_color_map[kind_label],
                    label=kind_label,
                    edgecolor='black',
                    s=100)

# Y 軸整數
plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

# X 軸顯示小時（正確顯示）
plt.gca().xaxis.set_major_formatter(DateFormatter('%H'))

# 顯示中文圖例與格式設定
plt.legend()
plt.title(f'{date} 抓取記錄（Create 值 vs 小時，點色為 Kind）')
plt.xlabel('小時')
plt.ylabel('Create（整數）')
plt.xticks(rotation=0)
plt.grid(True)
plt.tight_layout()
plt.show()

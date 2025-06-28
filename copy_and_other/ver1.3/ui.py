import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
import time
import datetime
import threading
import sqlite3

from main import main

task_lock = threading.Lock()

DB_PATH = "viewer_data.db"



# 模擬你之前的 main() 程式
def main_task(log_callback, clear_callback,kind):
    if not task_lock.acquire(blocking=False):
        log_callback("❌ 目前已有任務在執行，請稍後再試\n")
        return
    try:
        clear_callback()  # 清空日誌
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if kind == 0:
            log_callback(f"🕒 手動執行觸發\n執行時間:{now}\n\n")
        else:
            log_callback(f"🕒 排程任務觸發\n執行時間:{now}\n\n")
        log_callback("開始執行抓取工作...\n")
        # 你的抓取主程式
        main(log_callback)
        log_callback("抓取完成！\n")
    finally:
        task_lock.release()


class App:
    def __init__(self, root):
        
        
        self.root = root
        self.root.title("直播觀看數抓取系統")
        self.root.geometry("800x600")
        
        self.font=("微軟正黑體", 14)

        # 設定視窗圖示
        button_frame = tk.Frame(root)
        button_frame.pack(pady=5,fill='x')

        # 建立按鈕
        self.btn_run = tk.Button(button_frame, text="手動執行", command=self.manual_run, font=self.font)
        self.btn_run.pack(padx=10,pady=5,anchor='w', side='left')
        
        self.add_show_live_button(button_frame)  # 加入新按鈕

        # 顯示排程狀態
        self.label_status = tk.Label(root, text="排程狀態：未啟動", font=self.font)
        self.label_status.pack(padx=10,pady=5, anchor='w')

        # 日誌輸出框
        self.log_box = ScrolledText(root, state='disabled', height=15, font=self.font)
        self.log_box.pack(fill='both', expand=True, padx=10, pady=5)

        # APScheduler 背景排程
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.scheduled_job, 'cron', minute='0,15,30,45')
        self.scheduler.start()
        self.label_status.config(text="排程狀態：已啟動     每小時0,15,30,45分執行")

    def log(self, message):
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, message)
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

    def clear_log(self):
        self.log_box.config(state='normal')
        self.log_box.delete(1.0, tk.END)  # 清空整個 Text
        self.log_box.config(state='disabled')

    def manual_run(self):
        Thread(target=main_task, args=(self.log,self.clear_log,0)).start()

    # 定時排程觸發
    def scheduled_job(self):
        Thread(target=main_task, args=(self.log,self.clear_log,1)).start()

    # 新增顯示最近開台頻道按鈕
    def add_show_live_button(self, button_frame):
            btn_show_live = tk.Button(button_frame, text="開台狀態", command=self.show_latest_live_channels, font=self.font)
            btn_show_live.pack(anchor="w", padx=10, pady=5, side='left')

    # 顯示最近開台頻道
    def show_latest_live_channels(self):
        
        if task_lock.locked():
            self.log("⚠️ 正在抓取資料，請稍後再查看開台狀態...\n")
            return
        
        self.clear_log()  # 清空日誌
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 獲取當前時間，並計算最近的15分鐘時間點
        now = datetime.datetime.now()
        minute = now.minute
        nearest_minute = max(m for m in [0, 15, 30, 45] if m <= minute)
        
        # 設定開始時間為最近的15分鐘時間點
        start_time = now.replace(minute=nearest_minute, second=0, microsecond=0)
        
        # 計算結束時間，跳到下一個15分鐘刻度
        next_minute_candidates = [m for m in [0, 15, 30, 45] if m > nearest_minute]
        if next_minute_candidates:
            next_minute = min(next_minute_candidates)
            end_time = start_time.replace(minute=next_minute)
        else:
            # 如果沒有更大的刻度，代表要跳到下一小時的0分
            end_time = (start_time + datetime.timedelta(hours=1)).replace(minute=0)
        
        
        # 轉換時間格式為字串
        start_date = start_time.strftime("%Y-%m-%d")
        start_time_str = start_time.strftime("%H:%M:%S")
        start_time_output = start_time.strftime("%H:%M")
        end_date = end_time.strftime("%Y-%m-%d")
        end_time_str = end_time.strftime("%H:%M:%S")
        end_time_output = end_time.strftime("%H:%M")
        
        
        self.log(f"📅 查詢時間區間：{start_date} {start_time_output} ~ {end_date} {end_time_output}\n")

        # 如果區間跨日，需要分成兩個條件查詢
        if start_date == end_date:
            cursor.execute("""
                SELECT channel, MAX(youtube) as youtube, MAX(twitch) as twitch
                FROM viewers
                WHERE date=? AND time >= ? AND time < ? AND (youtube>0 OR twitch>0)
                GROUP BY channel
            """, (start_date, start_time_str, end_time_str))
        else:
            cursor.execute("""
                SELECT channel, MAX(youtube) as youtube, MAX(twitch) as twitch
                FROM viewers
                WHERE
                    (date = ? AND time >= ?)
                    OR
                    (date = ? AND time < ?)
                    AND (youtube>0 OR twitch>0)
                GROUP BY channel
            """, (start_date, start_time_str, end_date, end_time_str))
        
        rows = cursor.fetchall()
        
        if not rows:
            self.log(f"沒有頻道正在開台\n")
        else:
            self.log("🎥 目前開台頻道：\n")
            for channel, yt, tw in rows:
                if yt !=0 and tw != 0:
                    self.log(f"● {channel} 在 YouTube 和 Twitch 都開台\n")
                elif yt != 0:
                    self.log(f"● {channel} 在 YouTube 開台\n")
                elif tw != 0:
                    self.log(f"● {channel} 在 Twitch 開台\n")
        conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

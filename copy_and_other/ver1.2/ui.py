import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
import time
from datetime import datetime
import threading

from main import main

task_lock = threading.Lock()



# 模擬你之前的 main() 程式
def main_task(log_callback, clear_callback,kind):
    if not task_lock.acquire(blocking=False):
        log_callback("❌ 目前已有任務在執行，請稍後再試\n")
        return
    try:
        clear_callback()  # 清空日誌
        if kind == 0:
            log_callback("🕒 手動執行觸發\n")
        else:
            log_callback("🕒 排程任務觸發\n")
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
        self.root.geometry("600x400")

        # 建立按鈕
        self.btn_run = tk.Button(root, text="手動執行", command=self.manual_run)
        self.btn_run.pack(pady=5)

        # 顯示排程狀態
        self.label_status = tk.Label(root, text="排程狀態：未啟動")
        self.label_status.pack()

        # 日誌輸出框
        self.log_box = ScrolledText(root, state='disabled', height=15)
        self.log_box.pack(fill='both', expand=True, padx=10, pady=10)

        # APScheduler 背景排程
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.scheduled_job, 'cron', minute='0,15,30,45')
        self.scheduler.start()
        self.label_status.config(text="排程狀態：已啟動，每小時0,15,30,45分執行")

    def log(self, message):
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, message)
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

    def manual_run(self):
        #self.clear_log()  # ✅ 先清空
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #self.log(f"🕒 手動執行觸發 - {now}\n")
        Thread(target=main_task, args=(self.log,self.clear_log,0)).start()

    # 定時排程觸發
    def scheduled_job(self):
        #self.clear_log()  # ✅ 先清空
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #self.log(f"🕒 排程任務觸發 - {now}\n")
        Thread(target=main_task, args=(self.log,self.clear_log,1)).start()

    def clear_log(self):
        self.log_box.config(state='normal')
        self.log_box.delete(1.0, tk.END)  # 清空整個 Text
        self.log_box.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

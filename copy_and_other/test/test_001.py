from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

# ---------- 設定參數 ----------
target_url = "https://www.youtube.com/@%E6%A9%99Yuzumi/streams"  # 改成你要的網址
#target_url = "https://www.youtube.com/@%E6%BE%AARei/streams"
save_path = r"C:\Users\Ray\Desktop\coding\summer_project\vtuber\test\003\picture\live_capture_01.png"
# 存圖路徑，可改為其他資料夾與檔名

# ---------- 啟動 headless Chrome ----------
options = Options()
options.add_argument('--headless')              # 不開視窗
options.add_argument('--disable-gpu')           # 關閉 GPU 加速（headless 常見設定）
options.add_argument('--window-size=2560,1440')  # 可自訂視窗大小

driver = webdriver.Chrome(options=options)

try:
    driver.get(target_url)
    time.sleep(5)  # 等網頁載入，可視情況增減
    
    # 設定縮放為 50%
    driver.execute_script("document.body.style.zoom='130%'")
    time.sleep(1)  # 稍微等一下縮放生效

    # 建立資料夾（若不存在）
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 擷取畫面並儲存
    driver.save_screenshot(save_path)
    print(f"截圖已儲存至：{save_path}")

except Exception as e:
    print("錯誤發生：", e)

finally:
    driver.quit()

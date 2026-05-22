import csv
import time
import sqlite3
import easyocr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import subprocess
import socket
import urllib3
import os
import sys


from youtube import (
    youtube_capture_screenshot,
    youtube_find_and_crop,  
    youtube_extract_viewer_count
)

from twitch import (
    twitch_capture_screenshot,
    twitch_find_and_crop,
    twitch_extract_viewer_count,
)

from sql import (
    init_db,
    add_streamer,
    save_viewer_count,
    load_channels_from_db,
    yt_number_get,
    tw_number_get,
    insert_working
)

OCR_READER = easyocr.Reader(['ch_tra', 'en'], gpu=False)  
DB_PATH = "data.db"


def yt_part(log, cid, name, yt_url, driver):
    
    log(f"📺 處理 YouTube 頻道：{name}")
    screenshot_path = f"pictures/yt_picture/{cid}_capture.png"
    cropped_path = f"pictures/yt_crop/{cid}_crop.png"
    template_path = "find/yt_find.png"
    
    # 步驟 1：截圖網頁
    ok, driver,error = youtube_capture_screenshot(yt_url, screenshot_path, driver)
    if not ok:
        log("❌ 截圖失敗，略過此頻道")
        return 0, False, error, driver
    

    
    # 步驟 2：裁切圖片和確認是否再開台
    yt_find_and_crop_rt, find_x, find_y = \
        youtube_find_and_crop(
            screenshot_path, 
            template_path, 
            cropped_path,
            offset_x=-500,
            offset_y=110,
            crop_height=30,
            crop_width=350
        )
        # 較長的標題
        
    if yt_find_and_crop_rt==1:
        log(f"❌ {name} youtube沒在開台")
        return 0 ,False,error, driver
    elif yt_find_and_crop_rt==2:
        log("❌ 圖片開啟失敗")
        return 0 ,False,error, driver
    
    log(f"✅ {name} youtube正在開台")
    
    # 步驟 3：OCR 提取觀看人數
    yt_count = youtube_extract_viewer_count(cropped_path, OCR_READER)
    yt_count = int(yt_count) if isinstance(yt_count, str) else yt_count  # 確保是整數
    
    
    if yt_count == -1:
        
        yt_find_and_crop_rt, find_x, find_y = \
            youtube_find_and_crop(
                screenshot_path, 
                template_path, 
                cropped_path,
                80
            )
            
        if yt_find_and_crop_rt==1:
            log(f"❌ {name} youtube沒在開台")
            return 0 ,False,error, driver
        elif yt_find_and_crop_rt==2:
            log("❌ 圖片開啟失敗")
            return 0 ,False,error, driver
        
        yt_count = youtube_extract_viewer_count(cropped_path, OCR_READER)
        yt_count = int(yt_count) if isinstance(yt_count, str) else yt_count
        
        if(yt_count == -1):
            log(f"❌ [{name}] OCR 辨識失敗")
            return 0 ,False,error, driver
    
    if yt_count == -2:
        log(f"❌ OCR 處理時發生錯誤")
        return 0 ,False,error, driver
    else:
        log(f"🎉 [{name}] 正在觀看人數：{yt_count} 人")
        return yt_count ,True,error, driver


def tw_part(log, cid, name, tw_url , driver):
    log(f"🎮 處理 Twitch 頻道：{name}")
    screenshot_path = f"pictures/tw_picture/{cid}_capture.png"
    cropped_path = f"pictures/tw_crop/{cid}_crop.png"
    template_path = "find/tw_find_2.png"
    template_path_2 = "find/tw_find_1.png"
    
    
    max_retries = 3
    retry_count = 0
    success = False

    while retry_count < max_retries:
        # 步驟 1：截圖
        ok, driver,error = twitch_capture_screenshot(tw_url, screenshot_path, driver)
        if not ok:
            log("❌ 截圖失敗，略過此頻道")
            return 0, False,error, driver 

        # 步驟 2：先比對 path1（開台畫面）
        rt1 = twitch_find_and_crop(screenshot_path, template_path, cropped_path)
        
        if rt1 == 0:
            log(f"✅ {name} twitch正在開台")
            success = True
            break

        elif rt1 == 2:
            log("❌ 圖片開啟失敗（path1）")
            return 0, False,error, driver

        # 若 rt1 == 1，進入第二層判斷，用 path2（沒開台畫面）確認
        rt2 = twitch_find_and_crop(screenshot_path, template_path_2, cropped_path)
        
        if rt2 == 0:
            log(f"❌ {name} twitch沒在開台")
            return 0, False,error, driver

        elif rt2 == 2:
            log("❌ 圖片開啟失敗（path2）")
            return 0, False,error, driver

        # 兩個都沒找到，屬於畫面異常，重試
        log("⚠️ 無法確認開台狀態，重新截圖中...")
        retry_count += 1

    if not success:
        log(f"❌ {name} twitch疑似開台但畫面錯誤（已重試 {max_retries} 次）")
        return 0, False,error, driver


    # 步驟 3：OCR 提取觀看人數
    tw_count = twitch_extract_viewer_count(cropped_path, OCR_READER)
    tw_count = int(tw_count) # 確保是整數
    
    if tw_count == -2:
        log(f"❌ OCR 處理時發生錯誤")
        return 0 , False, error, driver
    elif tw_count == -1:
        log(f"❌ [{name}] 沒有找到觀看人數")
        return 0 , False, error, driver
    else:
        log(f"🎉 [{name}] 正在觀看人數：{tw_count} 人")
        return tw_count , True, error, driver


def cleanup_headless_chrome():
    """僅清理 Selenium 啟動的 headless Chrome 進程"""
    try:
        # 尋找所有帶 "--headless" 的 Chrome 進程
        result = subprocess.run(
            'wmic process where "name=\'chrome.exe\' and commandline like \'%%--headless%%\'" get processid',
            shell=True, capture_output=True, text=True
        )

        # 擷取 process ID
        pids = [pid.strip() for pid in result.stdout.split() if pid.strip().isdigit()]
        if pids:
            for pid in pids:
                subprocess.run(f"taskkill /PID {pid} /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"🧹 已清理 {len(pids)} 個 headless Chrome 進程。 test")
        else:
            print("✅ 沒有發現殘留的 headless Chrome。test")

        # 一併清理殘留的 chromedriver
        subprocess.run("taskkill /f /im chromedriver.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"⚠️ 清理過程出錯：{e}")
        



def create_driver():
    urllib3.PoolManager().clear()
    cleanup_headless_chrome()

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=2560,1440')
    options.add_argument('--mute-audio')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--dns-prefetch-disable')  # ✅ 避免 TCP DNS hang
    options.add_argument("--disable-breakpad")
    options.add_argument("--disable-crash-reporter")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument('--disable-features=NetworkService,NetworkServiceInProcess')

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)   # ✅ 加上載入逾時保護
        driver.set_script_timeout(20)
        return driver
    except Exception as e:
        print(f"❌ ChromeDriver 初始化失敗：{e}")
        time.sleep(3)
        cleanup_headless_chrome()
        return webdriver.Chrome(options=options)




def reset_socket_layer():
    try:
        urllib3.PoolManager().clear()
        socket.setdefaulttimeout(10)
    except Exception as e:
        print(f"⚠️ socket 清理失敗：{e}")

def restart_ui():
    print("🚨 錯誤過多，正在重新啟動 UI 程式...")
    cleanup_headless_chrome()
    python = sys.executable
    ui_path = os.path.join(os.path.dirname(__file__), "ui.py")
    os.execl(python, python, ui_path)


def main(log_callback=None,kind=0):
    """
    主函數：整合所有步驟
    """
    
    #程式計時器
    start_time = time.time()
    
    fail_count = 0
    
    # 初始化資料庫
    init_db()
    
    working_id = insert_working(True,False,None,0,kind,0)  
    
    cleanup_headless_chrome()
    
    
    # 設定 Selenium WebDriver
    # options = Options()
    # options.add_argument('--headless=new')     # 新版 headless 模式，支援 GPU
    # options.add_argument('--use-gl=angle')     # 使用 ANGLE (DirectX)
    # options.add_argument('--window-size=2560,1440')
    # options.add_argument('--mute-audio')
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--ignore-ssl-errors')
    
    

    driver = create_driver()

    
    # 日誌輸出函數
    def log(msg):
        if log_callback:
            log_callback(msg + "\n")
        else:
            print(msg)
    
    
    log("🎯 開始執行直播觀看人數提取程序")
    log("=" * 30)
    
    # 讀取頻道清單
    channel_list = load_channels_from_db(DB_PATH)
    
    
    create = 0
    # 主程式開始
    for cid, name, yt_url, tw_url in channel_list:
        
        
        ytstreaming = False  # 是否正在 YouTube 開台
        twstreaming = False  # 是否正在 Twitch 開台
        yt_count = 0  # YouTube 觀看人數
        tw_count = 0  # Twitch 觀看人數
        
        log(f"\n🔍 處理頻道：{name} (ID: {cid})")
        
        # 處理 YouTube 頻道
        if yt_url:
            yt_count ,ytstreaming,error,driver = yt_part(log, cid, name, yt_url, driver)
        else:
            log(f"❌ {name} 沒有提供 YouTube 連結，跳過")
        
        if not error:
            fail_count += 1
            if fail_count >=5:
                fail_count = 0
                restart_ui()
        
        # 處理 Twitch 頻道
        
        if tw_url:
            tw_count ,twstreaming,error,driver = tw_part(log, cid, name, tw_url, driver)
        else:
            log(f"❌ {name} 沒有提供 Twitch 直播連結，跳過")
        
        if not error:
            fail_count += 1
            if fail_count >=5:
                restart_ui()
        
        if ytstreaming or twstreaming:
            log(f"✅ {name} 直播狀態：YouTube: {str(yt_count)+"人" if ytstreaming else "沒有開台"}, Twitch: {str(tw_count)+"人" if twstreaming else "沒有開台"}")
            
            if ytstreaming:
                create = create + 1
            
            if twstreaming:
                create = create + 1
            
            
            if ytstreaming:
                args ={
                    "driver": driver,
                    "cid": cid,
                    "yt_url": yt_url,
                    "screenshot_path" : f"pictures/yt_picture/{cid}_capture.png",
                    "cropped_path" : f"pictures/yt_crop/{cid}_crop.png",
                    "template_path" : "find/yt_find.png",
                    "OCR_READER": OCR_READER
                } 
                yt_number = yt_number_get(cid, args, DB_PATH)
            else:
                
                yt_number = 0
            
            if twstreaming:
                args ={
                    "screenshot_path" : f"pictures/tw_picture/{cid}_capture.png",
                    "cropped_path" : f"pictures/tw_crop/{cid}_crop.png",
                    "OCR_READER": OCR_READER
                }
                #tw_number = 0
                tw_number = tw_number_get(cid, args, DB_PATH)
            else:
                tw_number = 0
            
            save_viewer_count(cid, yt_count, tw_count, yt_number, tw_number, DB_PATH)
            
        reset_socket_layer()
        time.sleep(0.5)

    
    log("\n✅ 所有頻道處理完成")
    print("\n✅ 所有頻道處理完成")
    
    driver.quit()  # 關閉 WebDriver
    
    end_time = time.time()
    elapsed = end_time - start_time
    log(f"\n⏱️ 程式總共執行了 {elapsed:.2f} 秒")
    
    insert_working(False,True,elapsed,working_id,kind,create)  # 更新工作紀錄為完成
    

if __name__ == "__main__":
    main()
    """
    scheduler = BlockingScheduler()
    scheduler.add_job(job, 'cron', minute='15,45')
    print("排程啟動，等待中...")
    scheduler.start()
    """

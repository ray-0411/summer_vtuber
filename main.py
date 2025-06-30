import csv
import time
import sqlite3
import easyocr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


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

OCR_READER = easyocr.Reader(['ch_tra', 'en'])
DB_PATH = "data.db"



def yt_part(log, cid, name, yt_url, driver):
    
    log(f"📺 處理 YouTube 頻道：{name}")
    screenshot_path = f"pictures/yt_picture/{cid}_capture.png"
    cropped_path = f"pictures/yt_crop/{cid}_crop.png"
    template_path = "find/yt_find.png"
    
    # 步驟 1：截圖網頁
    if not youtube_capture_screenshot(yt_url, screenshot_path, driver):
        log("❌ 截圖失敗，略過此頻道")
        return 0 ,False
    
    # 步驟 2：裁切圖片和確認是否再開台
    yt_find_and_crop_rt, find_x, find_y= youtube_find_and_crop(screenshot_path, template_path, cropped_path,80)
    if yt_find_and_crop_rt==1:
        log(f"❌ {name} youtube沒在開台")
        return 0 ,False
    elif yt_find_and_crop_rt==2:
        log("❌ 圖片開啟失敗")
        return 0 ,False
    
    log(f"✅ {name} youtube正在開台")
    
    # 步驟 3：OCR 提取觀看人數
    yt_count = youtube_extract_viewer_count(cropped_path, OCR_READER)
    yt_count = int(yt_count) if isinstance(yt_count, str) else yt_count  # 確保是整數
    
    
    if yt_count == -1:
        
        yt_find_and_crop_rt, find_x, find_y= youtube_find_and_crop(screenshot_path, template_path, cropped_path,100)
        if yt_find_and_crop_rt==1:
            log(f"❌ {name} youtube沒在開台")
            return 0 ,False
        elif yt_find_and_crop_rt==2:
            log("❌ 圖片開啟失敗")
            return 0 ,False
        
        yt_count = youtube_extract_viewer_count(cropped_path, OCR_READER)
        yt_count = int(yt_count) if isinstance(yt_count, str) else yt_count
        
        if(yt_count == -1):
            log(f"❌ [{name}] OCR 辨識失敗")
            return 0 ,False
    
    if yt_count == -2:
        log(f"❌ OCR 處理時發生錯誤")
        return 0 ,False
    else:
        log(f"🎉 [{name}] 正在觀看人數：{yt_count} 人")
        return yt_count ,True


def tw_part(log, cid, name, tw_url , driver):
    log(f"🎮 處理 Twitch 頻道：{name}")
    screenshot_path = f"pictures/tw_picture/{cid}_capture.png"
    cropped_path = f"pictures/tw_crop/{cid}_crop.png"
    template_path = "find/tw_find_2.png"
    
    # 步驟 1：截圖網頁
    if not twitch_capture_screenshot(tw_url, screenshot_path,driver):
        log("❌ 截圖失敗，略過此頻道")
        return 0 ,False
    
    # 步驟 2：裁切圖片和確認是否再開台
    tw_find_and_crop_rt = twitch_find_and_crop(screenshot_path, template_path, cropped_path)
    if tw_find_and_crop_rt==1:
        log(f"❌ {name} twitch沒在開台")
        return 0 ,False
    elif tw_find_and_crop_rt==2:
        log("❌ 圖片開啟失敗")
        return 0 ,False
    log(f"✅ {name} twitch正在開台")
    
    # 步驟 3：OCR 提取觀看人數
    tw_count = twitch_extract_viewer_count(cropped_path, OCR_READER)
    tw_count = int(tw_count) # 確保是整數
    
    if tw_count == -2:
        log(f"❌ OCR 處理時發生錯誤")
        return 0 ,False
    elif tw_count == -1:
        log(f"❌ [{name}] 沒有找到觀看人數")
        return 0 ,False
    else:
        log(f"🎉 [{name}] 正在觀看人數：{tw_count} 人")
        return tw_count ,True


def main(log_callback=None,kind=0):
    """
    主函數：整合所有步驟
    """
    
    #程式計時器
    start_time = time.time()
    
    # 初始化資料庫
    init_db()
    
    working_id = insert_working(True,False,None,0,kind,0)  
    
    # 設定 Selenium WebDriver
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=2560,1440')
    options.add_argument('--mute-audio')

    driver = webdriver.Chrome(options=options)
    
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
            yt_count ,ytstreaming = yt_part(log, cid, name, yt_url, driver)
        else:
            log(f"❌ {name} 沒有提供 YouTube 連結，跳過")
        
        # 處理 Twitch 頻道
        
        if tw_url:
            tw_count ,twstreaming = tw_part(log, cid, name, tw_url, driver)
        else:
            log(f"❌ {name} 沒有提供 Twitch 直播連結，跳過")
        
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

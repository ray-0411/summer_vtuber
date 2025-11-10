from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import easyocr
import streamlit as st
import pandas as pd




from youtube import (
    youtube_capture_screenshot,
    youtube_find_and_crop,  
    youtube_extract_viewer_count,
    youtube_extract_name,
    youtube_click_for_link
)

from twitch import (
    twitch_capture_screenshot,
    twitch_find_and_crop,
    twitch_extract_viewer_count,
    twitch_extract_name_2
)   

from sql import (
    add_streamer,
    import_streamers_from_csv,
    get_channel_name_by_id
)

from main import cleanup_headless_chrome  # 匯入清理函數

from main_data_fun import plot_time_distribution  # 匯入函數

if __name__ == "__main__":
    
    
    #import_streamers_from_csv("copy_and_other/channels.csv", "data.db")
    
    # test_yt_url = "https://www.youtube.com/@ItsukiIanvs/streams"  # 替換為實際的 YouTube 直播連結
    # test_twitch_url = "https://www.twitch.tv/kirali_neon"  # 替換為實際的 Twitch 直播連結
    #test_save_path = f"pictures/tw_picture/mizuki_capture.png"
    #crop_path = "test/test_crop.png"
    #crop_path = "test/japanese_title.png"
    db_path = "data.db"
    
    cleanup_headless_chrome()  # 呼叫清理函數
    
    # 假設 df_selected 已經篩選好
    
    #plot_time_distribution(df_selected, st)
    
    # options = Options()
    # options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    # options.add_argument('--window-size=2560,1440')
    # options.add_argument('--mute-audio')
    # driver = webdriver.Chrome(options=options)
    
    # OCR_READER = easyocr.Reader(['ch_tra', 'en'])
    # DB_PATH = "data.db"
    
    # youtube_capture_screenshot(test_yt_url, test_save_path, driver)
    # nouse,find_x,find_y = youtube_find_and_crop(test_save_path, "find/yt_find.png", crop_path,45,crop_height=100,crop_width=420)
    # name = youtube_extract_name(crop_path, OCR_READER)
    # link = youtube_click_for_link(driver,test_yt_url,find_x,find_y)
    
    #print (f"{name} 的連結是 {link}")
    #youtube_extract_viewer_count(crop_path, OCR_READER)
    
    
    #import_streamers_from_csv("channels.csv", DB_PATH)
    
    #print(get_channel_name_by_id("mizuki", DB_PATH))
    
    # twitch_capture_screenshot(test_twitch_url, test_save_path, driver,140)
    # twitch_find_and_crop(test_save_path, "find/tw_find_1.png", crop_path,
    #                 offset_x=-1490,offset_y=-20, crop_height=100, crop_width=1200)
    
    # twitch_extract_viewer_count(crop_path,OCR_READER)
    
    #twitch_extract_name_2(crop_path)
    
    # #100 -150 0 100 25
    
    # driver.quit()  # 關閉瀏覽器
    
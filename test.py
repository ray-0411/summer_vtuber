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

from main import (
    cleanup_headless_chrome,
    create_driver
)  # 匯入清理函數

from main_data_fun import plot_time_distribution  # 匯入函數

if __name__ == "__main__":
    
    
    #import_streamers_from_csv("copy_and_other/channels.csv", "data.db")
    
    test_yt_url = "https://www.youtube.com/@%E5%AE%9FHitomi/streams"  # 替換為實際的 YouTube 直播連結
    # test_twitch_url = "https://www.twitch.tv/kirali_neon"  # 替換為實際的 Twitch 直播連結
    #test_save_path = f"pictures/tw_picture/mizuki_capture.png"
    #crop_path = "test/test_crop.png"
    #crop_path = "test/japanese_title.png"
    #db_path = "data.db"
    
    #cleanup_headless_chrome()  # 呼叫清理函數
    
    
    # OCR_READER = easyocr.Reader(['ch_tra', 'en'])
    # DB_PATH = "data.db"
    
    # youtube_capture_screenshot(test_yt_url, test_save_path, driver)
    # nouse,find_x,find_y = youtube_find_and_crop(test_save_path, "find/yt_find.png", crop_path,45,crop_height=100,crop_width=420)
    # name = youtube_extract_name(crop_path, OCR_READER)
    # link = youtube_click_for_link(driver,test_yt_url,find_x,find_y)
    
    # -----------------------------------------------------
    #yt 調整擷取位置
    
    # youtube_capture_screenshot(
    #     test_yt_url, 
    #     "test/yt_capture.png", 
    #     driver
    # )
    
    youtube_find_and_crop(
        "test/yt_capture.png", 
        "find/yt_find.png", 
        "test/test_crop.png",
        offset_x=-500,
        offset_y=110,
        crop_height=30,
        crop_width=350
    )
    
    #driver.quit()
    
    #-----------------------------------------------------
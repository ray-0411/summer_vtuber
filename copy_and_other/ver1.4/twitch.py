import os
import time
import cv2
import re
import numpy as np
import easyocr
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def twitch_capture_screenshot(target_url, save_path, driver=None,zoom=140):
    
    own_driver = False
    
    if driver is None:
        # 沒傳入 driver 才自己創建
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=2560,1440')
        options.add_argument('--mute-audio')
        driver = webdriver.Chrome(options=options)
        own_driver = True

    try:
        driver.get(target_url)
        #time.sleep(3)  # 等網頁載入，可視情況增減
        """
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)  
        """
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR, "button[aria-label='更多選項'][title='更多選項']"
        )))
        
        
        # 設定縮放為 130%
        driver.execute_script(f"document.body.style.zoom='{zoom}%'")
        #time.sleep(1)  # 稍微等一下縮放生效
        
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        

        # 建立資料夾（若不存在）
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # 擷取畫面並儲存
        driver.save_screenshot(save_path)
        print(f"✅ 截圖已儲存至：{save_path}")
        return True

    except Exception as e:
        print("❌ 截圖時發生錯誤：", e)
        return False

    finally:
        if own_driver:
            driver.quit()  # 只有自己產生的才關閉

def twitch_find_and_crop \
    (img_path, 
    template_path, 
    crop_output_path,
    offset_x=-220,
    offset_y=0,
    crop_width=150,
    crop_height=40):
    
    """
    使用 OpenCV 尋找目標圖案並裁切指定區域
    """
    print("🔍 開始尋找目標圖案...")
    
    # ---------- 載入圖片 ----------
    img = cv2.imread(img_path)       # 原始大圖
    template_orig = cv2.imread(template_path)    # 要找的小圖
    
    if img is None or template_orig is None:
        print("❌ 無法載入圖片檔案")
        return 2
    
    template_gray = cv2.cvtColor(template_orig, cv2.COLOR_BGR2GRAY)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 設定門檻與縮放比例範圍
    threshold = 0.8
    found = False
    top_left = None
    w, h = 0, 0

    for scale in np.linspace(0.5, 1.5, 20):  # 20 個比例：從 0.5 到 1.5
        # 縮放 template
        resized = cv2.resize(template_gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h, w = resized.shape[:2]

        # 跳過太大圖的情況
        if img_gray.shape[0] < h or img_gray.shape[1] < w:
            continue

        result = cv2.matchTemplate(img_gray, resized, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            print(f"✅ 找到了！比例 {scale:.2f}，相似度 {max_val:.3f}")
            top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)
            found = True
            break  # 找到就跳出

    if found:
        # 儲存標記結果
        cv2.imwrite("pictures/result_match.png", img)
        print("✅ 已儲存標記畫面 result_match.png")
        
        # ---------- 加上擷取附近區域 ----------
        #offset_x = -150
        #offset_y = 0
        crop_x = top_left[0] + offset_x
        crop_y = top_left[1] + offset_y
        #crop_width = 100
        #crop_height = 25

        # 避免越界
        crop_x = max(0, crop_x)
        crop_y = max(0, crop_y)
        end_x = min(crop_x + crop_width, img.shape[1])
        end_y = min(crop_y + crop_height, img.shape[0])

        # 擷取區域
        cropped = img[crop_y:end_y, crop_x:end_x]
        os.makedirs(os.path.dirname(crop_output_path), exist_ok=True)
        cv2.imwrite(crop_output_path, cropped)
        print(f"✅ 已儲存截圖區域 {crop_output_path}")
        return 0
    else:
        print("❌ 沒找到符合的圖案")
        return 1

def twitch_extract_viewer_count(cropped_image_path, OCR_READER=None):
    """
    使用 EasyOCR 從裁切的圖片中提取觀看人數
    """
    print("📖 開始 OCR 文字識別...")
    
    try:
        # 建立 OCR 讀取器（指定繁體中文 + 英文）
        #reader = easyocr.Reader(['ch_tra', 'en'])  # ch_tra = 繁體中文

        # 讀取圖片
        result = OCR_READER.readtext(cropped_image_path, detail=0)

        # 辨識後的文字
        text = ' '.join(result)
        print("OCR 原始結果：", text)

        # 嘗試修正常見錯誤
        cleaned_text = clean_ocr_text(text)
        

        #3,598 -> 3598
        #2:5 -> 25
        
        
        cleaned_text = cleaned_text.replace(',', '')  # 移除逗號
        cleaned_text = cleaned_text.replace(':', '')  # 移除冒號
        
        print("OCR 修正後結果：", cleaned_text)
        
        numbers = re.findall(r"\d+", cleaned_text)
        
        if numbers[0] == '9':
            match = numbers[1]
        elif len(numbers[0]) > 1 :
            if numbers[0][0] == '9':
                match = numbers[0][1:]  # 取第一個數字，通常是觀看人數
            else:
                match = numbers[0]
        else:
            match = None
        
        
        #print(f"找到的數字：{match}")
        
        
        if match:
            
            print(f"✅ 找到觀看人數：{match}")
            return match
        else:
            print("❌ 沒找到觀看人數")
            return -1
            
    except Exception as e:
        print(f"❌ OCR 處理時發生錯誤：{e}")
        return -2


def clean_ocr_text(text):
    # 常見誤判修正表
    replacements = {
        'O': '0', 'o': '0',
        'I': '1', 'l': '1', '|': '1',
        'Z': '2',
        'S': '5', '$': '5',
        'B': '8',
        'T': '7'  # ← 這個是你的重點
    }
    return ''.join(replacements.get(c, c) for c in text)

def twitch_extract_name(cropped_image_path, OCR_READER=None):
    """
    使用 EasyOCR 從裁切的圖片中提取觀看人數
    """
    print("📖 開始 OCR 文字識別...")
    
    try:
        # 建立 OCR 讀取器（指定繁體中文 + 英文）
        #reader = easyocr.Reader(['ch_tra', 'en'])  # ch_tra = 繁體中文

        # 讀取圖片
        result = OCR_READER.readtext(cropped_image_path, detail=0)

        # 辨識後的文字
        text = ' '.join(result)
        print("OCR 原始結果：", text)


        #print(f"找到的數字：{match}")
        
        
        if text:
            return text
        else:
            print("❌ 沒找到觀看人數")
            return -1
            
    except Exception as e:
        print(f"❌ OCR 處理時發生錯誤：{e}")
        return -2

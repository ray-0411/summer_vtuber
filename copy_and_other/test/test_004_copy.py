from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import cv2
import numpy as np
import easyocr
import re
import os
import time

def capture_youtube_screenshot(target_url, save_path):
    """
    使用 Selenium 截取 YouTube 頁面截圖
    """
    print("🚀 開始截取網頁...")
    
    # ---------- 啟動 headless Chrome ----------
    options = Options()
    options.add_argument('--headless')              # 不開視窗
    options.add_argument('--disable-gpu')           # 關閉 GPU 加速（headless 常見設定）
    options.add_argument('--window-size=2560,1440')  # 可自訂視窗大小

    driver = webdriver.Chrome(options=options)

    try:
        driver.get(target_url)
        time.sleep(5)  # 等網頁載入，可視情況增減
        
        # 設定縮放為 130%
        driver.execute_script("document.body.style.zoom='130%'")
        time.sleep(1)  # 稍微等一下縮放生效

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
        driver.quit()

def find_and_crop_target(img_path, template_path, crop_output_path):
    """
    使用 OpenCV 尋找目標圖案並裁切指定區域
    """
    print("🔍 開始尋找目標圖案...")
    
    # ---------- 載入圖片 ----------
    img = cv2.imread(img_path)       # 原始大圖
    template_orig = cv2.imread(template_path)    # 要找的小圖
    
    if img is None or template_orig is None:
        print("❌ 無法載入圖片檔案")
        return False
    
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
        cv2.imwrite("result_match.png", img)
        print("✅ 已儲存標記畫面 result_match.png")
        
        # ---------- 加上擷取附近區域 ----------
        offset_x = -350
        offset_y = 100
        crop_x = top_left[0] + offset_x
        crop_y = top_left[1] + offset_y
        crop_width = 250
        crop_height = 40

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
        return True
    else:
        print("❌ 沒找到符合的圖案")
        return False

def extract_viewer_count(cropped_image_path):
    """
    使用 EasyOCR 從裁切的圖片中提取觀看人數
    """
    print("📖 開始 OCR 文字識別...")
    
    try:
        # 建立 OCR 讀取器（指定繁體中文 + 英文）
        reader = easyocr.Reader(['ch_tra', 'en'])  # ch_tra = 繁體中文

        # 讀取圖片
        result = reader.readtext(cropped_image_path, detail=0)

        # 將辨識文字合併成一行
        text = ' '.join(result)
        print("OCR 結果：", text)

        # 擷取「x 人正在觀看」
        match = re.search(r"(\d[\d,]*)\s*人", text)
        if match:
            count = match.group(1).replace(",", "")
            print(f"✅ 找到觀看人數：{count}")
            return count
        else:
            print("❌ 沒找到觀看人數")
            return None
            
    except Exception as e:
        print(f"❌ OCR 處理時發生錯誤：{e}")
        return None

def main():
    """
    主函數：整合所有步驟
    """
    print("🎯 開始執行 YouTube 直播觀看人數提取程序")
    print("=" * 50)
    
    # ---------- 設定參數 ----------
    #target_url = "https://www.youtube.com/@%E6%A9%99Yuzumi/streams"  # 改成你要的網址
    #target_url = "https://www.youtube.com/@%E6%BE%AARei/streams"
    target_url = "https://www.youtube.com/@erycyoo/streams"
    #
    
    screenshot_path = r"picture\live_capture_01.png"
    template_path = "find.png"
    cropped_path = "crop/cropped_area.png"
    
    # 步驟 1：截取網頁
    if not capture_youtube_screenshot(target_url, screenshot_path):
        print("❌ 截圖失敗，程序終止")
        return
    
    # 步驟 2：尋找目標並裁切
    if not find_and_crop_target(screenshot_path, template_path, cropped_path):
        print("❌ 圖案匹配失敗，程序終止")
        return
    
    # 步驟 3：OCR 提取觀看人數
    viewer_count = extract_viewer_count(cropped_path)
    
    if viewer_count:
        print("=" * 50)
        print(f"🎉 成功提取觀看人數：{viewer_count} 人")
        
        # 可以在這裡加入其他處理，例如儲存到檔案或資料庫
        with open("viewer_count.txt", "w", encoding="utf-8") as f:
            f.write(f"觀看人數：{viewer_count}\n")
            f.write(f"提取時間：{time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        print("✅ 結果已儲存至 viewer_count.txt")
    else:
        print("❌ 無法提取觀看人數")

if __name__ == "__main__":
    main()

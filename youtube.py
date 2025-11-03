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
from selenium.webdriver.common.action_chains import ActionChains
import pytesseract
from PIL import Image
import subprocess
import urllib3

def cleanup_chrome():
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
            print(f"🧹 已清理 {len(pids)} 個 headless Chrome 進程。")
        else:
            print("✅ 沒有發現殘留的 headless Chrome。")

        # 一併清理殘留的 chromedriver
        subprocess.run("taskkill /f /im chromedriver.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"⚠️ 清理過程出錯：{e}")
        


def create_driver():
    urllib3.PoolManager().clear()
    cleanup_chrome()

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
    options.add_argument('--disable-features=NetworkService,NetworkServiceInProcess')

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)   # ✅ 加上載入逾時保護
        driver.set_script_timeout(20)
        return driver
    except Exception as e:
        print(f"❌ ChromeDriver 初始化失敗：{e}")
        time.sleep(3)
        cleanup_chrome()
        return webdriver.Chrome(options=options)



# 使用 Selenium 截取 YouTube 頁面截圖
def youtube_capture_screenshot(target_url, save_path, driver=None):
    """
    使用 Selenium 截取 YouTube 頁面截圖（具備自動重啟保護）
    """
    print("🚀 開始截取網頁...")


    own_driver = False

    if driver is None:
        driver = create_driver()
        own_driver = True

    try:
        driver.get(target_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        driver.execute_script("document.body.style.zoom='130%'")
        time.sleep(1)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        driver.save_screenshot(save_path)
        print(f"✅ 截圖已儲存至：{save_path}")
        return True,driver,True

    except Exception as e:
        print(f"❌ 截圖時發生錯誤：{e}")
        try:
            driver.quit()
        except:
            pass

        # 🔁 嘗試自動重啟一次
        print("🔁 嘗試重新啟動 Chrome driver...")
        try:
            driver = create_driver()
            driver.get(target_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            driver.execute_script("document.body.style.zoom='130%'")
            time.sleep(1)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            driver.save_screenshot(save_path)
            print(f"✅ 截圖已儲存至：{save_path}（重試成功）")
            return True,driver,False
        except Exception as e2:
            print(f"❌ 重啟後仍失敗：{e2}")
            return False,driver,False
    finally:
        if own_driver:
            try:
                driver.quit()
            except:
                pass
            time.sleep(0.5)



# 使用 OpenCV 尋找目標圖案並裁切指定區域
def youtube_find_and_crop \
    (img_path, 
    template_path, 
    crop_output_path,
    offset_y=80, 
    offset_x=-350,
    crop_width=250, 
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
        return 2,0,0
    
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
        #offset_x = -350
        #offset_y = 80
        crop_x = top_left[0] + offset_x
        crop_y = top_left[1] + offset_y
        #crop_width = 250
        #crop_height = 40

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
        return 0,top_left[0], top_left[1]
    else:
        print("❌ 沒找到符合的圖案")
        return 1,0,0

# 使用 EasyOCR 提取觀看人數
def youtube_extract_viewer_count(cropped_image_path,OCR_READER=None):
    """
    使用 EasyOCR 從裁切的圖片中提取觀看人數
    """
    print("📖 開始 OCR 文字識別...")
    
    try:

        # 讀取圖片
        result = OCR_READER.readtext(cropped_image_path, detail=0)

        # 辨識後的文字
        text = ' '.join(result)
        print("OCR 原始結果：", text)

        # 嘗試修正常見錯誤
        cleaned_text = clean_ocr_text(text)
        print("OCR 修正後結果：", cleaned_text)

        # 擷取「x 人正在觀看」
        match = re.search(r"(\d[\d,]*)\s*人", cleaned_text)
        if match:
            count = match.group(1).replace(",", "")
            print(f"✅ 找到觀看人數：{count}")
            return count
        else:
            print("❌ 沒找到觀看人數")
            return -1
            
    except Exception as e:
        print(f"❌ OCR 處理時發生錯誤：{e}")
        return -2

# easyocr 修正函式 用於 extract_viewer
def clean_ocr_text(text):
    # 常見誤判修正表
    replacements = {
        'O': '0', 'o': '6',
        'I': '1', 'l': '1', '|': '1',
        'Z': '2',
        'S': '5', '$': '5',
        'B': '8',
        'T': '7', '/':'7' ,'b':'6' # ← 這個是你的重點
    }
    return ''.join(replacements.get(c, c) for c in text)


# 使用 EasyOCR 提取頻道名稱(無使用)
def youtube_extract_name(cropped_image_path,OCR_READER=None):
    """
    使用 EasyOCR 從裁切的圖片中提取觀看人數
    """
    print("📖 開始 OCR 文字識別...")
    
    try:

        # 讀取圖片
        result = OCR_READER.readtext(cropped_image_path, detail=0)

        # 辨識後的文字
        text = ' '.join(result)
        print("OCR 原始結果：", text)

        # 擷取「x 人正在觀看」
        text = re.sub(r"\s*\d+\s*人正在", "", text).strip()
        
        print("OCR 修正後結果：", text)
        return text if text else None
        
    except Exception as e:
        print(f"❌ OCR 處理時發生錯誤：{e}")
        return -1

# 使用 Tesseract OCR 提取頻道名稱或觀看人數等文字
def youtube_extract_name_2(cropped_image_path):
    """
    使用 Tesseract OCR 從裁切的圖片中提取頻道名稱或觀看人數等文字
    支援中英日混雜辨識。
    """
    print("📖 開始 Tesseract 文字識別...")

    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    try:
        # 讀取圖片
        img = Image.open(cropped_image_path)

        # 使用 tesseract 進行 OCR（支援繁體中文、日文、英文）
        text = pytesseract.image_to_string(img, lang="chi_tra+jpn+eng")

        print("OCR 原始結果：", text)

        # 清理字串（移除特殊符號、換行）
        cleaned = text.strip().replace('\n', ' ')
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)

        if cleaned:
            return cleaned
        else:
            print("❌ 沒找到任何文字")
            return -1

    except Exception as e:
        print(f"❌ OCR 處理時發生錯誤：{e}")
        return -2


# 使用 Selenium 點擊影片取得連結
def youtube_click_for_link(driver,first_link,x,y):
    
    try:
        driver.get(first_link)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        driver.execute_script("document.body.style.zoom='130%'")
        
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        print(f"🖱️ 點擊座標 ({x}, {y})...")

        actions = ActionChains(driver)
        actions.move_by_offset(x, y).click().perform()
        actions.move_by_offset(-x, -y).perform()  # 把滑鼠移回來，避免影響後續操作

        print("⏳ 等待頁面跳轉...")
        WebDriverWait(driver, 2).until(
            lambda d: "/watch?" in d.current_url
        )

        new_url = driver.current_url
        print(f"✅ 已進入影片頁：{new_url}")
        return new_url

    except Exception as e:
        print("❌ 點擊後未能成功跳轉影片頁：", e)
        return None


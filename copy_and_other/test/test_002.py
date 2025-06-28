import cv2
import numpy as np
import os

# ---------- 載入圖片 ----------
img = cv2.imread("picture\live_capture_01.png")       # 原始大圖
template_orig = cv2.imread("find.png")    # 要找的小圖
template_gray = cv2.cvtColor(template_orig, cv2.COLOR_BGR2GRAY)
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# 設定門檻與縮放比例範圍
threshold = 0.8
found = False

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
        break  # 如果你只想找一次，找到就跳出

if found:
    cv2.imwrite("result_match.png", img)
    print("已儲存畫面 result_match.png")
    
    
    # ---------- 加上擷取附近區域 ----------
    offset_x = -350
    offset_y = 100
    crop_x = top_left[0] + offset_x
    crop_y = top_left[1] + offset_y
    crop_width = 250
    crop_height = 40

    # 避免越界
    end_x = min(crop_x + crop_width, img.shape[1])
    end_y = min(crop_y + crop_height, img.shape[0])

    # 擷取區域
    cropped = img[crop_y:end_y, crop_x:end_x]
    os.makedirs("crop", exist_ok=True)
    cv2.imwrite("crop/cropped_area.png", cropped)
    print("已儲存截圖區域 crop/cropped_area.png")
    
    
else:
    print("❌ 沒找到符合的圖案")
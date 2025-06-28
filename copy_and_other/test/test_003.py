import easyocr
import re

# 建立 OCR 讀取器（指定繁體中文 + 英文）
reader = easyocr.Reader(['ch_tra', 'en'])  # ch_tra = 繁體中文

# 讀取圖片
result = reader.readtext('crop/cropped_area.png', detail=0)

# 將辨識文字合併成一行
text = ' '.join(result)
print("OCR 結果：", text)

# 擷取「x 人正在觀看」
match = re.search(r"(\d[\d,]*)\s*人", text)
if match:
    count = match.group(1).replace(",", "")
    print("✅ 找到觀看人數：", count)
else:
    print("❌ 沒找到觀看人數")

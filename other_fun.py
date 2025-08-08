import sqlite3
import requests
import os
import re

#用streamer表的yt_url來得到yt的頭貼
def youtube_icon_from_streamer_sql(db_path, save_folder):
    os.makedirs(save_folder, exist_ok=True)

    # 連接 SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 取得 channel_id 與 yt_url
    cursor.execute("SELECT channel_id, yt_url FROM streamer")
    rows = cursor.fetchall()

    for channel_id, yt_url in rows:
        if not yt_url:
            print(f"{channel_id} 無 yt_url，跳過")
            continue

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(yt_url, headers=headers, timeout=10)
            resp.raise_for_status()
            html = resp.text

            # 抓頭貼網址
            match = re.search(r'https://yt3\.googleusercontent\.com/[^\"]+', html)
            if not match:
                print(f"{channel_id} 找不到頭貼網址")
                continue

            avatar_url = match.group(0).split('=')[0] + '=s176-c'

            # 下載頭貼
            img_resp = requests.get(avatar_url, timeout=10)
            if img_resp.status_code == 200:
                save_path = os.path.join(save_folder, f"{channel_id}.jpg")
                with open(save_path, "wb") as f:
                    f.write(img_resp.content)
                print(f"{channel_id} 頭貼下載成功，存到 {save_path}")
            else:
                print(f"{channel_id} 下載頭貼失敗，狀態碼：{img_resp.status_code}")

        except Exception as e:
            print(f"{channel_id} 下載過程錯誤：{e}")

    conn.close()

def youtube_icon_from_input(yt_url, save_path):
    """
    yt_url: YouTube 頻道首頁網址
    save_path: 完整檔案路徑（含檔名，例如 "./avatars/myavatar.jpg"）
    """
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(yt_url, headers=headers, timeout=10)
        resp.raise_for_status()
        html = resp.text

        match = re.search(r'https://yt3\.googleusercontent\.com/[^\"]+', html)
        if not match:
            print("找不到頭貼網址")
            return False

        avatar_url = match.group(0).split('=')[0] + '=s176-c'

        img_resp = requests.get(avatar_url, timeout=10)
        if img_resp.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(img_resp.content)
            print(f"頭貼下載成功，存到 {save_path}")
            return True
        else:
            print(f"下載頭貼失敗，狀態碼：{img_resp.status_code}")
            return False
    except Exception as e:
        print(f"下載過程錯誤：{e}")
        return False

def batch_download_og_images_from_db(db_path, save_folder):
    """
    從資料庫 streamer 表抓 channel_id 和 yt_url，
    用 og:image / twitter:image 方式抓圖片網址並下載，
    存成 {channel_id}_image.jpg
    """
    os.makedirs(save_folder, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT channel_id, tw_url FROM streamer")
    rows = cursor.fetchall()

    for channel_id, url in rows:
        if not url:
            print(f"{channel_id} 無網址，跳過")
            continue

        print(f"處理頻道 {channel_id}，網址：{url}")

        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            html = resp.text

            # 抓 og:image
            og_image_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html, re.IGNORECASE)
            if og_image_match:
                img_url = og_image_match.group(1)
            else:
                # 抓 twitter:image
                twitter_image_match = re.search(r'<meta\s+name="twitter:image"\s+content="([^"]+)"', html, re.IGNORECASE)
                if twitter_image_match:
                    img_url = twitter_image_match.group(1)
                else:
                    print(f"{channel_id} 找不到 og:image 或 twitter:image")
                    continue

            # 下載圖片
            img_resp = requests.get(img_url, timeout=10)
            if img_resp.status_code == 200:
                save_path = os.path.join(save_folder, f"{channel_id}.jpg")
                with open(save_path, "wb") as f:
                    f.write(img_resp.content)
                print(f"{channel_id} 圖片下載成功，存到 {save_path}")
            else:
                print(f"{channel_id} 下載圖片失敗，狀態碼：{img_resp.status_code}")

        except Exception as e:
            print(f"{channel_id} 下載過程錯誤：{e}")

    conn.close()

# 使用範例
# db_path = "data.db"
# save_folder = "./pictures/yt_icon"
# youtube_icon_from_streamer_sql(db_path, save_folder)

# yt_url = "https://www.youtube.com/@998rrr"
# save_path = "./pictures/yt_icon/998.jpg"
# youtube_icon_from_input(yt_url, save_path)

db_path = "data.db"
save_folder = "./pictures/tw_icon"
batch_download_og_images_from_db(db_path, save_folder)
import sqlite3
import time
import datetime
import csv

from youtube import (
    youtube_find_and_crop,
    youtube_capture_screenshot,
    youtube_extract_name,
    youtube_extract_name_2,
    youtube_click_for_link,
)

from twitch import (
    twitch_find_and_crop,
    twitch_extract_name,
    twitch_extract_name_2
)


DB_PATH = "data.db"

# 初始化資料庫
# 如果資料庫不存在，會自動建立
def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS main (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        channel TEXT NOT NULL,
        youtube INTEGER NOT NULL,
        twitch INTEGER NOT NULL,
        yt_number INTEGER DEFAULT 0,
        tw_number INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS stream(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_name TEXT NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        url TEXT DEFAULT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS streamer(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT NOT NULL UNIQUE,
        channel_name TEXT NOT NULL,
        yt_url TEXT DEFAULT NULL,
        tw_url TEXT DEFAULT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS working(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL UNIQUE,
        finish TEXT NOT NULL,
        timer REAL DEFAULT NULL,
        kind TEXT DEFAULT NULL,
        "create" INTEGER DEFAULT NULL
    )
    ''')
    
    conn.commit()
    conn.close()


# 儲存觀看人數到資料庫
def save_viewer_count \
    (channel_id, 
    yt_count=0, 
    tw_count=0, 
    yt_number=0,
    tw_number=0,
    db_path=DB_PATH):
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    now = time.localtime()
    date_str = time.strftime('%Y-%m-%d', now)
    time_str = time.strftime('%H:%M:%S', now)



    cursor.execute('''
    INSERT INTO main (date, time, channel, youtube, twitch, yt_number, tw_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date_str, time_str, channel_id, yt_count, tw_count, yt_number, tw_number))

    conn.commit()
    conn.close()
    print(f"✅ 已儲存至資料庫：{channel_id} - YouTube: {yt_count} 人, Twitch: {tw_count} 人 ({date_str} {time_str})")


#stream 資料表相關操作

# yt_number_get 回傳 YouTube 直播紀錄的 ID
# 用在 main.py 中新增 main用
def yt_number_get(channel_id, args, db_path=DB_PATH):
    
    istreaming = is_straming(channel_id, 0, db_path)
    if istreaming:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE stream
            SET end_time = ?
            WHERE id = ?
        ''', (now, istreaming))

        conn.commit()
        conn.close()
        print(f"✅ 已更新 stream ID={istreaming} 的 end_time 為 {now}")
        
        return istreaming
    else:
        rtid = create_stream_yt(channel_id, args, db_path)
        return rtid


def tw_number_get(channel_id, args, db_path=DB_PATH):
    
    istreaming = is_straming(channel_id, 1, db_path)
    if istreaming:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE stream
            SET end_time = ?
            WHERE id = ?
        ''', (now, istreaming))

        conn.commit()
        conn.close()
        print(f"✅ 已更新 stream ID={istreaming} 的 end_time 為 {now}")
        
        return istreaming
    else:
        rtid = create_stream_tw(channel_id, args, db_path)
        return rtid


# is_straming 函數用於檢查頻道是否在最近30分鐘內有開台
# type 0 為 YouTube，1 為 Twitch
def is_straming(channel_id, type, db_path=DB_PATH):
    now = datetime.datetime.now()
    time_30min_ago = now - datetime.timedelta(minutes=35)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if type == 0:
        type = "youtube"
    else:
        type = "twitch"

    cursor.execute('''
        SELECT * FROM stream
        WHERE channel_name = ?
        AND end_time BETWEEN ? AND ?
        AND type = ?
    ''', (
        channel_id,
        time_30min_ago.strftime('%Y-%m-%d %H:%M:%S'),
        now.strftime('%Y-%m-%d %H:%M:%S'),
        type
    ))
    
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else 0


# create_stream_yt 函數用於新增 YouTube 的 stream
def create_stream_yt\
(channel_id, args, db_path=DB_PATH):
    
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    """
    args ={
                "driver": driver,
                "cid": cid,
                "yt_url": yt_url,
                "screenshot_path" : f"pictures/yt_picture/{cid}_capture.png",
                "cropped_path" : f"pictures/yt_crop/{cid}_crop.png",
                "template_path" : "find/yt_find.png",
                "OCR_READER": OCR_READER
            } 
    """
    
    #youtube_capture_screenshot(test_yt_url, test_save_path, driver)
    nouse,find_x,find_y = youtube_find_and_crop\
    (args["screenshot_path"], args["template_path"], args["cropped_path"], 45,crop_height=100,crop_width=420)
    name = youtube_extract_name_2(args["cropped_path"], args["OCR_READER"])
    url = youtube_click_for_link(args["driver"],args["yt_url"],find_x,find_y)
    
    #name = "space"
    #url = "space"  

    cursor.execute('''
        INSERT INTO stream (channel_name, name, type, url, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (channel_id, name, "youtube", url, now, now))

    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()

    print(f"✅ 已新增直播紀錄，ID = {inserted_id}")
    return inserted_id  # 回傳這筆資料的 id

# tw_number_get 回傳 Twitch 直播紀錄的 ID
# 用在 main.py 中新增 main用
# create_stream_tw 函數用於新增 Twitch 直播紀錄
def create_stream_tw\
(channel_id, args, db_path=DB_PATH):

    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    """
    args ={
                "screenshot_path" : f"pictures/yt_picture/{cid}_capture.png",
                "cropped_path" : f"pictures/yt_crop/{cid}_crop.png",
                "OCR_READER": OCR_READER
            } 
    """
    
    
    twitch_find_and_crop(args["screenshot_path"], "find/tw_find_2.png", args["cropped_path"],
                    offset_x=-1490,offset_y=-20, crop_height=100, crop_width=1200)
    name = twitch_extract_name_2(args["cropped_path"],args["OCR_READER"])
    url = "twitch"
    #name = "space"
    #url = "space"  

    cursor.execute('''
        INSERT INTO stream (channel_name, name, type, url, start_time, end_time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (channel_id, name, "twitch", url, now, now))

    conn.commit()
    inserted_id = cursor.lastrowid
    conn.close()

    print(f"✅ 已新增直播紀錄，ID = {inserted_id}")
    return inserted_id  # 回傳這筆資料的 id


# 插入或更新工作紀錄到 working 資料表
# start True開始時 False結束時
# finish True完成工作 False剛開始
def insert_working(start,finish, timer,id,kind,create):
    
    """將一筆資料插入 streamer 資料表中"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    fin_text = "Finish" if finish else "Problem" 
    
    if kind == 0:
        kind = "手動"
    elif kind == 1:
        kind = "排程"
    else:
        kind = "啟動"
    
    if start:
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO working (time, finish, timer,kind,"create")
                VALUES (?, ?, ?, ?, ?)
            ''', (now, fin_text, timer,kind,create))
            conn.commit()
            id = cursor.lastrowid
            
            print(f"✅ 成功新增一筆 streamer 紀錄{id}")
            
            return id
        except sqlite3.IntegrityError as e:
            print(f"❌ 新增失敗，時間可能重複：{e}")
        finally:
            conn.close()
    else:
        try:
            timer = round(timer, 2)
            cursor.execute('''
                UPDATE working
                SET finish = ?, timer = ?, "create" = ?
                WHERE id = ?
            ''', (fin_text, timer, create, id))  # 假設只更新第一筆資料
            conn.commit()
            print("✅ 成功更新 working 紀錄")
        except sqlite3.Error as e:
            print(f"❌ 更新失敗：{e}")
        finally:
            conn.close()



# streamers 資料表相關操作

# 新增直播主資料到資料庫
def add_streamer(channel_id, channel_name, yt_url=None, tw_url=None, db_path=DB_PATH):
    """
    新增一筆直播主資料到 streamer 資料表
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
        INSERT OR IGNORE INTO streamer (channel_id, channel_name, yt_url, tw_url)
        VALUES (?, ?, ?, ?)
        ''', (channel_id, channel_name, yt_url, tw_url))

        conn.commit()
        if cursor.rowcount == 0:
            print(f"⚠️ 已存在：{channel_id}，資料未更新")
        else:
            print(f"✅ 已新增直播主：{channel_name} ({channel_id})")
        return True

    except Exception as e:
        print("❌ 新增失敗：", e)
        return False

    finally:
        conn.close()

# 從 CSV 檔案匯入直播主資料到資料庫
def import_streamers_from_csv(csv_path, db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            channel_id = row['channel_id']
            channel_name = row['channel_name']
            yt_url = row['yt_url'] if row['yt_url'] != '' else None
            tw_url = row['tw_url'] if row['tw_url'] != '' else None

            add_streamer(channel_id, channel_name, yt_url, tw_url, db_path)

    conn.commit()
    conn.close()
    print("✅ 匯入完成！")

# 從資料庫讀取 streamer 表中的頻道資料
# return channel_list
def load_channels_from_db(db_path):
    """
    從資料庫讀取 streamer 表中的頻道資料
    回傳格式：[("channel_id", "channel_name", "yt_full_url", "tw_url"), ...]
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT channel_id, channel_name, yt_url, tw_url FROM streamer")
    rows = cursor.fetchall()
    conn.close()

    channel_list = []
    for channel_id, channel_name, yt_url, tw_url in rows:
        yt_full_url = yt_url.rstrip('/') + '/streams' if yt_url else None
        tw_url = tw_url.rstrip('/') if tw_url else None
        channel_list.append((channel_id, channel_name, yt_full_url, tw_url))

    return channel_list

# 其他資料庫操作

# 獲取最近15分鐘內正在開台的頻道
# 回傳格式：[("channel_id", youtube_viewers, twitch_viewers), ...]
def latest_live_channels(log):
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 獲取當前時間，並計算最近的15分鐘時間點
    now = datetime.datetime.now()
    minute = now.minute
    nearest_minute = max(m for m in [0, 15, 30, 45] if m <= minute)
    
    # 設定開始時間為最近的15分鐘時間點
    start_time = now.replace(minute=nearest_minute, second=0, microsecond=0)
    
    # 計算結束時間，跳到下一個15分鐘刻度
    next_minute_candidates = [m for m in [0, 15, 30, 45] if m > nearest_minute]
    if next_minute_candidates:
        next_minute = min(next_minute_candidates)
        end_time = start_time.replace(minute=next_minute)
    else:
        # 如果沒有更大的刻度，代表要跳到下一小時的0分
        end_time = (start_time + datetime.timedelta(hours=1)).replace(minute=0)
    
    
    # 轉換時間格式為字串
    start_date = start_time.strftime("%Y-%m-%d")
    start_time_str = start_time.strftime("%H:%M:%S")
    start_time_output = start_time.strftime("%H:%M")
    end_date = end_time.strftime("%Y-%m-%d")
    end_time_str = end_time.strftime("%H:%M:%S")
    end_time_output = end_time.strftime("%H:%M")
    
    
    log(f"📅 查詢時間區間：{start_date} {start_time_output} ~ {end_date} {end_time_output}\n")

    # 如果區間跨日，需要分成兩個條件查詢
    if start_date == end_date:
        cursor.execute("""
            SELECT channel, MAX(youtube) as youtube, MAX(twitch) as twitch
            FROM main
            WHERE date=? AND time >= ? AND time < ? AND (youtube>0 OR twitch>0)
            GROUP BY channel
        """, (start_date, start_time_str, end_time_str))
    else:
        cursor.execute("""
            SELECT channel, MAX(youtube) as youtube, MAX(twitch) as twitch
            FROM main
            WHERE
                (date = ? AND time >= ?)
                OR
                (date = ? AND time < ?)
                AND (youtube>0 OR twitch>0)
            GROUP BY channel
        """, (start_date, start_time_str, end_date, end_time_str))
    
    rows = cursor.fetchall()
    return rows


# 根據 channel_id 獲取對應的 channel_name
def get_channel_name_by_id(channel_id, db_path):
    """
    輸入 channel_id，回傳對應的 channel_name。
    找不到時回傳 None。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT channel_name FROM streamer WHERE channel_id = ?", (channel_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0]  # channel_name
    else:
        return None
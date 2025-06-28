import sqlite3
import time
import datetime
import csv

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
    
    conn.commit()
    conn.close()


# 儲存觀看人數到資料庫
def save_viewer_count(channel_id, yt_count=0, tw_count=0, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    now = time.localtime()
    date_str = time.strftime('%Y-%m-%d', now)
    time_str = time.strftime('%H:%M:%S', now)
    yt_number = yt_number_get()
    tw_number = 0  # 目前沒有使用 Twitch 的頻道號碼

    cursor.execute('''
    INSERT INTO main (date, time, channel, youtube, twitch, yt_number, tw_number)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date_str, time_str, channel_id, yt_count, tw_count, yt_number, tw_number))

    conn.commit()
    conn.close()
    print(f"✅ 已儲存至資料庫：{channel_id} - YouTube: {yt_count} 人, Twitch: {tw_count} 人 ({date_str} {time_str})")

def yt_number_get(db_path=DB_PATH):
    
    return 0

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



# 獲取最近15分鐘內正在開台的頻道
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
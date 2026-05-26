import requests
import time
import datetime
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask

# ================== CẤU HÌNH ==================

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

DAYS_AGO = 7
MIN_TOTAL_VIEWS = 50000

# 1800 giây = 30 phút
CHECK_INTERVAL = 1800

# Số keyword chạy cùng lúc
MAX_WORKERS = 5

KEYWORDS = [
    "bodycam",
    "police bodycam",
    "police body cam",
    "body cam footage",
    "PoliceActivity",
    "law & crime",
    "dui arrest bodycam",
    "police arrest",
    "police activity",
    "dash cam arrest",
]

# ================== FLASK KEEP ALIVE ==================

app = Flask(__name__)

@app.route("/")
def home():
    return "YouTube Agent Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================== CHỐNG GỬI TRÙNG ==================

sent_videos = set()
sent_lock = threading.Lock()

# ================== TELEGRAM ==================

def send_telegram(video):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("LỖI: Chưa cấu hình TELEGRAM_TOKEN hoặc TELEGRAM_CHAT_ID")
        return

    message = f"""
🚨 VIDEO BODYCAM ĐẠT VIEW CAO

📌 {video['title']}

👀 {video['views']:,} views

🕒 {video['published_at'][:10]}

🔗 https://youtube.com/watch?v={video['videoId']}
"""

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }

    try:
        print(f"📨 Đang gửi Telegram: {video['title'][:70]}")
        response = requests.post(url, data=data, timeout=20)

        if response.status_code == 200:
            print(f"✅ ĐÃ GỬI TELEGRAM: {video['title'][:70]}")
        else:
            print(f"❌ Telegram lỗi {response.status_code}: {response.text}")

    except Exception as e:
        print("❌ Lỗi gửi Telegram:", e)

# ================== THỜI GIAN ==================

def get_published_after():
    dt = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=DAYS_AGO)
    return dt.isoformat().replace("+00:00", "Z")

# ================== YOUTUBE SEARCH ==================

def search_videos(keyword):
    if not YOUTUBE_API_KEY:
        print("LỖI: Chưa cấu hình YOUTUBE_API_KEY")
        return []

    search_url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "order": "viewCount",
        "publishedAfter": get_published_after(),
        "maxResults": 5,
        "regionCode": "US",
        "key": YOUTUBE_API_KEY,
    }

    try:
        print(f"🔎 Search YouTube: {keyword}")
        response = requests.get(search_url, params=params, timeout=20)
        data = response.json()

        if response.status_code != 200:
            print(f"❌ YouTube Search lỗi {response.status_code} với keyword '{keyword}': {data}")
            return []

        items = data.get("items", [])
        print(f"✅ Search xong '{keyword}': tìm thấy {len(items)} video")
        return items

    except Exception as e:
        print(f"❌ Lỗi search keyword '{keyword}':", e)
        return []

# ================== VIDEO DETAILS ==================

def get_video_details(video_ids, keyword):
    if not video_ids:
        print(f"⚠️ Không có video mới để lấy details: {keyword}")
        return []

    detail_url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }

    try:
        print(f"📊 Lấy views/details cho {len(video_ids)} video: {keyword}")
        response = requests.get(detail_url, params=params, timeout=20)
        data = response.json()

        if response.status_code != 200:
            print(f"❌ YouTube Details lỗi {response.status_code} với keyword '{keyword}': {data}")
            return []

        items = data.get("items", [])
        print(f"✅ Details xong '{keyword}': có {len(items)} video")
        return items

    except Exception as e:
        print(f"❌ Lỗi detail keyword '{keyword}':", e)
        return []

# ================== XỬ LÝ 1 KEYWORD ==================

def process_keyword(keyword):
    print(f"\n================ KEYWORD: {keyword} ================")

    search_items = search_videos(keyword)

    if not search_items:
        print(f"⚠️ Keyword không có kết quả: {keyword}")
        return

    video_ids = []

    for item in search_items:
        try:
            video_id = item["id"]["videoId"]

            with sent_lock:
                already_sent = video_id in sent_videos

            if not already_sent:
                video_ids.append(video_id)

        except Exception as e:
            print(f"⚠️ Bỏ qua video lỗi dữ liệu ở keyword '{keyword}': {e}")

    details = get_video_details(video_ids, keyword)

    for v in details:
        try:
            video_id = v["id"]
            views = int(v["statistics"].get("viewCount", 0))
            title = v["snippet"]["title"]
            published_at = v["snippet"]["publishedAt"]

            print(f"📹 {views:,} views | {title[:90]}")

            if views >= MIN_TOTAL_VIEWS:
                with sent_lock:
                    if video_id in sent_videos:
                        continue

                    sent_videos.add(video_id)

                send_telegram({
                    "title": title,
                    "videoId": video_id,
                    "views": views,
                    "published_at": published_at,
                })

        except Exception as e:
            print(f"❌ Lỗi xử lý video keyword '{keyword}':", e)

    print(f"✅ Xong keyword: {keyword}")

# ================== MAIN ==================

def main():
    print("\n" + "=" * 70)
    print(f"🚀 BẮT ĐẦU QUÉT: {datetime.datetime.now()}")
    print(f"🔑 Tổng keyword: {len(KEYWORDS)}")
    print(f"⚙️ Chạy song song: {MAX_WORKERS} keyword cùng lúc")
    print(f"🎯 Điều kiện gửi: >= {MIN_TOTAL_VIEWS:,} views trong {DAYS_AGO} ngày")
    print("=" * 70)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_keyword, keyword) for keyword in KEYWORDS]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print("❌ Lỗi trong thread keyword:", e)

    print("\n✅ HOÀN TẤT 1 VÒNG QUÉT")

# ================== LOOP ==================

if __name__ == "__main__":
    print("🚀 YouTube Police Agent Started!")

    threading.Thread(target=run_flask, daemon=True).start()

    while True:
        try:
            main()
            print(f"\n⏳ Nghỉ {CHECK_INTERVAL // 60} phút rồi quét tiếp...\n")
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("❌ MAIN LOOP ERROR:", e)
            time.sleep(60)

```python
import requests
import time
import datetime
import os
import threading
from flask import Flask

# ================== CẤU HÌNH ==================

YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"

TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"

DAYS_AGO = 7
MIN_TOTAL_VIEWS = 50000

CHECK_INTERVAL = 900  # 15 phút

KEYWORDS = [
    "bodycam",
    "police body cam",
    "police bodycam",
    "body camera",
    "code blue cam",
    "real world police",
    "PoliceActivity",
    "police arrest",
    "police interaction",
    "true crime",
    "crime documentary",
    "police activity",
    "body cam footage",
    "law & crime",
    "DrInsanity",
    "POLICE INSIDER",
    "arrest cam",
    "news",
    "police",
    "dui",
    "law&crime",
    "live pd",
    "dash cam",
    "arrest camera"
]

# ================== FLASK KEEP ALIVE ==================

app = Flask(__name__)

@app.route('/')
def home():
    return "YouTube Agent Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ================== BIẾN CHỐNG GỬI TRÙNG ==================

sent_videos = set()

# ================== TELEGRAM ==================

def send_telegram(video):

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
        "text": message
    }

    try:
        response = requests.post(url, data=data, timeout=20)

        print("Telegram response:", response.text)

        if response.status_code == 200:
            print(f"✅ ĐÃ GỬI: {video['title'][:60]}")
        else:
            print(f"❌ Telegram lỗi: {response.text}")

    except Exception as e:
        print("❌ Lỗi gửi Telegram:", e)

# ================== THỜI GIAN ==================

def get_published_after():
    return (
        datetime.datetime.utcnow()
        - datetime.timedelta(days=DAYS_AGO)
    ).isoformat("T") + "Z"

# ================== YOUTUBE SEARCH ==================

def search_videos(keyword):

    search_url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "order": "viewCount",
        "publishedAfter": get_published_after(),
        "maxResults": 20,
        "regionCode": "US",
        "key": YOUTUBE_API_KEY
    }

    try:

        response = requests.get(search_url, params=params, timeout=30)

        data = response.json()

        if "items" not in data:
            print("❌ Không có items:", data)
            return []

        return data["items"]

    except Exception as e:
        print("❌ Lỗi search:", e)
        return []

# ================== VIDEO DETAILS ==================

def get_video_details(video_ids):

    if not video_ids:
        return []

    ids = ",".join(video_ids)

    detail_url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "statistics,snippet",
        "id": ids,
        "key": YOUTUBE_API_KEY
    }

    try:

        response = requests.get(detail_url, params=params, timeout=30)

        data = response.json()

        return data.get("items", [])

    except Exception as e:
        print("❌ Lỗi detail:", e)
        return []

# ================== MAIN ==================

def main():

    print("\n" + "=" * 60)
    print(f"🚀 BẮT ĐẦU QUÉT: {datetime.datetime.now()}")
    print("=" * 60)

    for keyword in KEYWORDS:

        print(f"\n🔍 Keyword: {keyword}")

        search_items = search_videos(keyword)

        if not search_items:
            continue

        video_ids = []

        for item in search_items:

            try:
                video_id = item["id"]["videoId"]

                if video_id not in sent_videos:
                    video_ids.append(video_id)

            except:
                continue

        details = get_video_details(video_ids)

        for v in details:

            try:

                video_id = v["id"]

                views = int(
                    v["statistics"].get("viewCount", 0)
                )

                title = v["snippet"]["title"]

                published_at = v["snippet"]["publishedAt"]

                print(f"   📹 {views:,} | {title[:60]}")

                if views >= MIN_TOTAL_VIEWS:

                    send_telegram({
                        "title": title,
                        "videoId": video_id,
                        "views": views,
                        "published_at": published_at
                    })

                    sent_videos.add(video_id)

            except Exception as e:
                print("❌ Lỗi xử lý video:", e)

# ================== LOOP ==================

if __name__ == "__main__":

    print("🚀 YouTube Police Agent Started!")

    while True:

        try:

            main()

            print(f"\n⏳ Sleep {CHECK_INTERVAL//60} phút...\n")

            time.sleep(CHECK_INTERVAL)

        except Exception as e:

            print("❌ MAIN LOOP ERROR:", e)

            time.sleep(60)
```

import requests
import time
import datetime
import os
import threading
from flask import Flask

YOUTUBE_API_KEY = os.environ.get("AIzaSyA_qHTbkd756XeAzgEuci1IIB8QWucXSoM")
TELEGRAM_TOKEN = os.environ.get("86600605994:AAFrc6w-WoHgSF4jJwZJC1QDUScUc7jgfZq")
TELEGRAM_CHAT_ID = os.environ.get("486709314")

DAYS_AGO = 7
MIN_TOTAL_VIEWS = 50000
CHECK_INTERVAL = 900

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
    "arrest camera",
]

app = Flask(__name__)

@app.route("/")
def home():
    return "YouTube Agent Running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

sent_videos = set()

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
        "text": message,
    }

    try:
        response = requests.post(url, data=data, timeout=20)
        print("Telegram response:", response.text)

        if response.status_code == 200:
            print(f"ĐÃ GỬI: {video['title'][:60]}")
        else:
            print(f"Telegram lỗi: {response.text}")

    except Exception as e:
        print("Lỗi gửi Telegram:", e)

def get_published_after():
    return (
        datetime.datetime.utcnow()
        - datetime.timedelta(days=DAYS_AGO)
    ).isoformat("T") + "Z"

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
        "key": YOUTUBE_API_KEY,
    }

    try:
        response = requests.get(search_url, params=params, timeout=30)
        data = response.json()

        if "items" not in data:
            print("Không có items:", data)
            return []

        return data["items"]

    except Exception as e:
        print("Lỗi search:", e)
        return []

def get_video_details(video_ids):
    if not video_ids:
        return []

    detail_url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "statistics,snippet",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }

    try:
        response = requests.get(detail_url, params=params, timeout=30)
        data = response.json()
        return data.get("items", [])

    except Exception as e:
        print("Lỗi detail:", e)
        return []

def main():
    print("\n" + "=" * 60)
    print(f"BẮT ĐẦU QUÉT: {datetime.datetime.now()}")
    print("=" * 60)

    for keyword in KEYWORDS:
        print(f"\nKeyword: {keyword}")

        search_items = search_videos(keyword)

        if not search_items:
            continue

        video_ids = []

        for item in search_items:
            try:
                video_id = item["id"]["videoId"]

                if video_id not in sent_videos:
                    video_ids.append(video_id)

            except Exception:
                continue

        details = get_video_details(video_ids)

        for v in details:
            try:
                video_id = v["id"]
                views = int(v["statistics"].get("viewCount", 0))
                title = v["snippet"]["title"]
                published_at = v["snippet"]["publishedAt"]

                print(f"{views:,} views | {title[:80]}")

                if views >= MIN_TOTAL_VIEWS:
                    send_telegram({
                        "title": title,
                        "videoId": video_id,
                        "views": views,
                        "published_at": published_at,
                    })

                    sent_videos.add(video_id)

            except Exception as e:
                print("Lỗi xử lý video:", e)

if __name__ == "__main__":
    print("YouTube Police Agent Started!")

    threading.Thread(target=run_flask, daemon=True).start()

    while True:
        try:
            main()
            print(f"\nSleep {CHECK_INTERVAL // 60} phút...\n")
            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("MAIN LOOP ERROR:", e)
            time.sleep(60)

import requests
import time
import datetime
import os
import threading
from flask import Flask
from telegram import Bot

# ================== CẤU HÌNH ==================
YOUTUBE_API_KEY = "AIzaSyD3g1nNRGTbNVqboQBTeL2PATWySGC_4kw"
TELEGRAM_TOKEN = "86600605994:AAFrc6w-WoHgSF4jJwZJC1QDUScUc7jgfZq"
TELEGRAM_CHAT_ID = 486709314

MIN_VPH = 10000
MIN_VIEWS = 100000
DAYS_AGO = 7

KEYWORDS = [
    "bodycam", "police body cam", "police bodycam", "body camera", "code blue cam",
    "real world police", "PoliceActivity", "police arrest", "police interaction",
    "true crime", "crime documentary", "police activity", "body cam footage",
    "law & crime", "DrInsanity", "POLICE INSIDER", "arrest cam"
]

bot = Bot(token=TELEGRAM_TOKEN)

# Dummy Flask server để Render không báo lỗi port
app = Flask(__name__)

@app.route('/')
def home():
    return "Police Bodycam Agent is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Chạy Flask trong thread riêng
threading.Thread(target=run_flask, daemon=True).start()

# ================== PHẦN CHÍNH ==================
def get_published_after():
    return (datetime.datetime.utcnow() - datetime.timedelta(days=DAYS_AGO)).isoformat() + "Z"

def calculate_vph(views, published_at):
    published = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    hours = (datetime.datetime.utcnow() - published).total_seconds() / 3600
    return round(int(views) / hours, 1) if hours > 0 else 0

def send_telegram(video):
    message = f"""
🚨 **VIDEO BODYCAM / TRUE CRIME VIRAL**

📌 **Tiêu đề**: {video['title']}
🔗 **Link**: https://youtube.com/watch?v={video['videoId']}
👀 **Views**: {video['views']:,} 
⚡ **VPH**: {video['vph']:,}
🕒 **Up**: {video['published_at'][:10]} ({video['hours']} giờ trước)
    """.strip()
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="HTML")
    print(f"✅ Đã gửi: {video['title'][:60]}...")

def main():
    published_after = get_published_after()
    print(f"🔍 Đang quét Police Bodycam & True Crime...")

    for keyword in KEYWORDS:
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "videoDuration": "long",
            "order": "viewCount",
            "publishedAfter": published_after,
            "maxResults": 15,
            "regionCode": "US",
            "key": YOUTUBE_API_KEY
        }

        resp = requests.get(search_url, params=params).json()

        for item in resp.get("items", []):
            video_id = item["id"]["videoId"]

            detail_url = "https://www.googleapis.com/youtube/v3/videos"
            detail_params = {
                "part": "statistics,contentDetails,snippet",
                "id": video_id,
                "key": YOUTUBE_API_KEY
            }
            detail = requests.get(detail_url, params=detail_params).json()

            if not detail.get("items"):
                continue

            v = detail["items"][0]
            views = v["statistics"].get("viewCount", "0")
            published_at = v["snippet"]["publishedAt"]
            vph = calculate_vph(views, published_at)

            if int(views) >= MIN_VIEWS and vph >= MIN_VPH:
                send_telegram({
                    "title": v["snippet"]["title"],
                    "videoId": video_id,
                    "views": int(views),
                    "vph": vph,
                    "published_at": published_at,
                    "hours": round((datetime.datetime.utcnow() - datetime.datetime.fromisoformat(published_at.replace("Z","+00:00"))).total_seconds()/3600, 1)
                })

if __name__ == "__main__":
    print("🚀 Agent đã khởi động thành công!")
    while True:
        try:
            main()
            print(f"⏳ Ngủ 15 phút... ({datetime.datetime.now().strftime('%H:%M:%S')})")
            time.sleep(900)
        except Exception as e:
            print("Lỗi:", e)
            time.sleep(60)

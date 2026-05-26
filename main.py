import requests
import time
import datetime
import os
import threading
import asyncio
from flask import Flask
from telegram import Bot

# ================== CẤU HÌNH TEST ==================
YOUTUBE_API_KEY = "AIzaSyA_qHTbkd756XeAzgEuci1IIB8QWucXSoM"
TELEGRAM_TOKEN = "86600605994:AAFrc6w-WoHgSF4jJwZJC1QDUScUc7jgfZq"
TELEGRAM_CHAT_ID = 486709314

DAYS_AGO = 7
MIN_TOTAL_VIEWS = 50000   # Chỉ cần 50.000 views là gửi

KEYWORDS = [
    "bodycam", "police body cam", "police bodycam", "body camera", "code blue cam",
    "real world police", "PoliceActivity", "police arrest", "police interaction",
    "true crime", "crime documentary", "police activity", "body cam footage",
    "law & crime", "DrInsanity", "POLICE INSIDER", "arrest cam", "news", "police",
    "dui", "law&crime", "live pd", "bodycam footage", "dash cam", "arrest camera"
]

bot = Bot(token=TELEGRAM_TOKEN)

# Dummy Flask server
app = Flask(__name__)
@app.route('/')
def home():
    return "Agent is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask, daemon=True).start()

# ================== HÀM GỬI TELEGRAM ==================
def send_telegram(video):
    message = f"""
🚨 **VIDEO BODYCAM ĐẠT 50K VIEWS**

📌 **Tiêu đề**: {video['title']}
🔗 **Link**: https://youtube.com/watch?v={video['videoId']}
👀 **Views**: {video['views']:,} 
🕒 **Up**: {video['published_at'][:10]}
    """.strip()
    try:
        asyncio.run(bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="HTML"))
        print(f"✅ ĐÃ GỬI: {video['title'][:60]}...")
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")

# ================== HÀM CHÍNH ==================
def get_published_after():
    return (datetime.datetime.utcnow() - datetime.timedelta(days=DAYS_AGO)).isoformat() + "Z"

def main():
    published_after = get_published_after()
    print(f"🔍 Đang quét Police Bodycam (chỉ cần >= 50k views trong 7 ngày)...")

    for keyword in KEYWORDS:
        print(f"   → Tìm với từ khóa: {keyword}")
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": published_after,
            "maxResults": 20,
            "regionCode": "US",
            "key": YOUTUBE_API_KEY
        }

        resp = requests.get(search_url, params=params).json()

        for item in resp.get("items", []):
            video_id = item["id"]["videoId"]

            detail_url = "https://www.googleapis.com/youtube/v3/videos"
            detail_params = {
                "part": "statistics,snippet",
                "id": video_id,
                "key": YOUTUBE_API_KEY
            }
            detail = requests.get(detail_url, params=detail_params).json()

            if not detail.get("items"):
                continue

            v = detail["items"][0]
            views = int(v["statistics"].get("viewCount", 0))

            if views >= MIN_TOTAL_VIEWS:
                send_telegram({
                    "title": v["snippet"]["title"],
                    "videoId": video_id,
                    "views": views,
                    "published_at": v["snippet"]["publishedAt"]
                })

if __name__ == "__main__":
    print("🚀 Agent TEST (50k views) đã khởi động!")
    while True:
        try:
            main()
            print(f"⏳ Ngủ 15 phút... ({datetime.datetime.now().strftime('%H:%M:%S')})")
            time.sleep(900)
        except Exception as e:
            print("Lỗi:", e)
            time.sleep(60)

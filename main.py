import requests
import time
import datetime
import os
import threading
from flask import Flask
from telegram import Bot

# ================== CẤU HÌNH MỚI ==================
YOUTUBE_API_KEY = "AIzaSyD3g1nNRGTbNVqboQBTeL2PATWySGC_4kw"
TELEGRAM_TOKEN = "86600605994:AAFrc6w-WoHgSF4jJwZJC1QDUScUc7jgfZq"
TELEGRAM_CHAT_ID = 486709314

DAYS_AGO = 7

# Ngưỡng mới theo yêu cầu của anh
MIN_VPH = 5000          # 5000 views/giờ
MIN_12H_VIEWS = 50000   # 50k views trong 12 giờ
MIN_24H_VIEWS = 100000  # 100k views trong 24 giờ
MIN_TOTAL_VIEWS = 200000 # 200k views tổng (trong 7 ngày)

KEYWORDS = [
    "bodycam", "police body cam", "police bodycam", "body camera", "code blue cam",
    "real world police", "PoliceActivity", "police arrest", "police interaction",
    "true crime", "crime documentary", "police activity", "body cam footage",
    "law & crime", "DrInsanity", "POLICE INSIDER", "arrest cam"
]

bot = Bot(token=TELEGRAM_TOKEN)

# Dummy Flask server (fix lỗi port)
app = Flask(__name__)
@app.route('/')
def home():
    return "Police Bodycam Agent is running!"
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
threading.Thread(target=run_flask, daemon=True).start()

# ================== HÀM CHÍNH ==================
def get_published_after():
    return (datetime.datetime.utcnow() - datetime.timedelta(days=DAYS_AGO)).isoformat() + "Z"

def calculate_hours(published_at):
    published = datetime.datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    return (datetime.datetime.utcnow() - published).total_seconds() / 3600

def should_send_video(views, hours):
    views = int(views)
    if views >= MIN_TOTAL_VIEWS:
        return True
    if hours > 0 and views / hours >= MIN_VPH:
        return True
    if hours <= 12 and views >= MIN_12H_VIEWS:
        return True
    if hours <= 24 and views >= MIN_24H_VIEWS:
        return True
    return False

def send_telegram(video):
    message = f"""
🚨 **VIDEO BODYCAM / TRUE CRIME NÓNG**

📌 **Tiêu đề**: {video['title']}
🔗 **Link**: https://youtube.com/watch?v={video['videoId']}
👀 **Views**: {video['views']:,} 
⚡ **VPH**: {video['vph']:,}
🕒 **Up**: {video['published_at'][:10]} ({video['hours']:.1f} giờ trước)
    """.strip()
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode="HTML")
    print(f"✅ Đã gửi: {video['title'][:60]}...")

def main():
    published_after = get_published_after()
    print(f"🔍 Đang quét Police Bodycam & True Crime (7 ngày qua)...")

    for keyword in KEYWORDS:
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
            hours = calculate_hours(published_at)
            vph = round(int(views) / hours, 1) if hours > 0 else 0

            if should_send_video(views, hours):
                send_telegram({
                    "title": v["snippet"]["title"],
                    "videoId": video_id,
                    "views": int(views),
                    "vph": vph,
                    "published_at": published_at,
                    "hours": hours
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

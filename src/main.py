import os
import json
from googleapiclient.discovery import build
from google import genai
import tweepy
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
HISTORY_FILE = "data/history.json"

def get_latest_video():
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(part="snippet", channelId=CHANNEL_ID, maxResults=1, order="date", type="video")
    response = request.execute()
    if not response.get("items"): return None
    v = response["items"][0]
    return {"id": v["id"]["videoId"], "title": v["snippet"]["title"], "description": v["snippet"]["description"], "url": f"https://www.youtube.com/watch?v={v['id']['videoId']}"}

def generate_post_content(video_info):
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"YouTube動画「{video_info['title']}」の紹介文をX用に100文字以内で作成して。ハッシュタグ2つ付けて。URLは含めないで。"
    response = client.models.generate_content(model='gemini-2.0-flash-lite', contents=prompt)
    return response.text.strip()

def post_to_x(content):
    client = tweepy.Client(consumer_key=X_API_KEY, consumer_secret=X_API_SECRET, access_token=X_ACCESS_TOKEN, access_token_secret=X_ACCESS_TOKEN_SECRET)
    client.create_tweet(text=content)

def main():
    video = get_latest_video()
    if not video: return
    if not os.path.exists(HISTORY_FILE):
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, 'w') as f: json.dump([], f)
    with open(HISTORY_FILE, 'r') as f: history = json.load(f)
    if video['id'] in history: return

    post_text = generate_post_content(video)
    post_to_x(f"{post_text}\n\n{video['url']}")

    history.append(video['id'])
    with open(HISTORY_FILE, 'w') as f: json.dump(history[-10:], f)

if __name__ == "__main__":
    main()

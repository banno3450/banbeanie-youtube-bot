import os
import json
import sys
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

REQUIRED_ENV_VARS = {
    "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
    "YOUTUBE_CHANNEL_ID": CHANNEL_ID,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "X_API_KEY": X_API_KEY,
    "X_API_SECRET": X_API_SECRET,
    "X_ACCESS_TOKEN": X_ACCESS_TOKEN,
    "X_ACCESS_TOKEN_SECRET": X_ACCESS_TOKEN_SECRET,
}


def validate_env():
    missing = [name for name, value in REQUIRED_ENV_VARS.items() if not value]
    if missing:
        print(f"エラー: 以下の環境変数が設定されていません: {', '.join(missing)}")
        print(".envファイルを確認してください。")
        sys.exit(1)


def get_latest_video():
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(part="snippet", channelId=CHANNEL_ID, maxResults=1, order="date", type="video")
        response = request.execute()
    except Exception as e:
        print(f"YouTube APIエラー: {e}")
        return None
    if not response.get("items"):
        return None
    v = response["items"][0]
    return {
        "id": v["id"]["videoId"],
        "title": v["snippet"]["title"],
        "description": v["snippet"]["description"],
        "url": f"https://www.youtube.com/watch?v={v['id']['videoId']}",
    }


def generate_post_content(video_info):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"YouTube動画「{video_info['title']}」の紹介文をX用に100文字以内で作成して。ハッシュタグ2つ付けて。URLは含めないで。"
        response = client.models.generate_content(model='gemini-1.5-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini APIエラー: {e}")
        return f"新しい動画がアップロードされました！: {video_info['title']}"


def post_to_x(content):
    try:
        client = tweepy.Client(consumer_key=X_API_KEY, consumer_secret=X_API_SECRET, access_token=X_ACCESS_TOKEN, access_token_secret=X_ACCESS_TOKEN_SECRET)
        client.create_tweet(text=content)
        print("Xへの投稿が完了しました。")
    except Exception as e:
        print(f"X投稿エラー: {e}")
        raise


def main():
    validate_env()

    video = get_latest_video()
    if not video:
        print("新しい動画が見つかりませんでした。")
        return

    if not os.path.exists(HISTORY_FILE):
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, 'w') as f:
            json.dump([], f)
    with open(HISTORY_FILE, 'r') as f:
        history = json.load(f)
    if video['id'] in history:
        print("この動画は既に投稿済みです。")
        return

    post_text = generate_post_content(video)
    post_to_x(f"{post_text}\n\n{video['url']}")

    history.append(video['id'])
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history[-10:], f)
    print(f"投稿完了: {video['title']}")


if __name__ == "__main__":
    main()

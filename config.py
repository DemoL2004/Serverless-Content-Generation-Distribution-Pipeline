import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Cloud
BUCKET_NAME = "yt-reddit"

# Paths
FFMPEG_PATH = "ffmpeg"
FFPROBE_PATH = "ffprobe"

CSV_FILE = "/tmp/posts.csv"
ERROR_FILE = "/tmp/errors.csv"
POST_TIMES_FILE = "/tmp/post_times.csv"

LOCAL_MUSIC_DIR = "/tmp/music"
LOCAL_GAMEPLAY_DIR = "/tmp/gameplay"
TOKEN_FILE = "/tmp/Tctoken.pickle"

PREDEFINED_TAGS = ["meme", "funny", "humor", "wholesome"]
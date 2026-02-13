import os
import json
import random
import requests
import unicodedata
import re
import praw
import logging

logger = logging.getLogger(__name__)

from config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    CSV_FILE
)

# Initialize Reddit client once
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)


def fetch_top_post(config_blob_path):
    """
    Fetches a top Reddit post from configured subreddits.
    Avoids duplicates based on logged CSV entries.
    """

    with open(config_blob_path, 'r') as f:
        config = json.load(f)

    subreddits = config.get("subreddits", [])
    time_filters = config.get("time_filters", [])

    tried_subreddits = set()

    while len(tried_subreddits) < len(subreddits):

        subreddit_name = random.choice(
            [s for s in subreddits if s not in tried_subreddits]
        )
        tried_subreddits.add(subreddit_name)

        logger.info("subreddit_selected | name=%s", subreddit_name)

        subreddit = reddit.subreddit(subreddit_name)
        logged_titles = load_logged_titles()

        for time_filter in time_filters:

            logger.info(
                "fetching_posts | subreddit=%s time_filter=%s",
                subreddit_name,
                time_filter or "all_time"
            )

            posts = (
                subreddit.top(time_filter, limit=1000)
                if time_filter
                else subreddit.top(limit=1000)
            )

            for post in posts:

                final_title = format_title(subreddit_name, post.title)
                norm_title = normalize(final_title)

                if norm_title in logged_titles:
                    continue

                if not is_image_or_gif(post.url):
                    continue

                image_name = download_image(post.url)

                if image_name:
                    logger.info(
                        "post_selected | subreddit=%s title=%s",
                        subreddit_name,
                        final_title
                    )
                    return final_title, image_name, subreddit_name

        logger.warning(
            "no_valid_post_found | subreddit=%s",
            subreddit_name
        )

    logger.error("no_posts_available_across_all_subreddits")
    return None, None, None
def load_logged_titles():
    try:
        with open(CSV_FILE, "r") as log_file:
            return {
                normalize(line.split(",", 1)[1])
                for line in log_file
                if "," in line
            }
    except FileNotFoundError:
        return set()


def format_title(subreddit_name, raw_title):
    raw_title = raw_title.replace("_", " ")

    if subreddit_name.lower() == "terriblefacebookmemes":
        return f"Another meme, {raw_title}"

    if subreddit_name.lower() == "programmerhumor":
        return split_camel_if_no_space(raw_title)

    return raw_title


def download_image(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        image_ext = os.path.splitext(url)[-1]
        image_name = f"downloaded_meme{image_ext}"

        with open(image_name, 'wb') as handler:
            handler.write(response.content)

        logger.info("image_downloaded | file=%s", image_name)
        return image_name

    except Exception:
        logger.exception("image_download_failed | url=%s", url)
        return None

def is_image_or_gif(url):
    return any(
        url.lower().endswith(ext)
        for ext in [".jpg", ".jpeg", ".png"]
    )


def normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = text.replace('’', "'").replace('“', '"').replace('”', '"')
    text = re.sub(r"[^\w\s]", "", text)
    return text.strip().lower()


def split_camel_if_no_space(text):
    if " " in text:
        return text
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', text)

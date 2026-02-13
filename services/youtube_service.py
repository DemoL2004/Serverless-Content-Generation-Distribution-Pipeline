import os
import re
import time
import random
import pickle
import gc
import logging

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

from config import PREDEFINED_TAGS, TOKEN_FILE
from utils.logging_utils import log_post, log_post_time, log_error, cleanup_files

logger = logging.getLogger(__name__)

def sanitize_title(title: str) -> str:
    clean = title.replace("<", "").replace(">", "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean

def get_youtube_client():
    try:
        creds = None

        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "rb") as token:
                creds = pickle.load(token)

        if creds and creds.expired and creds.refresh_token:
            logger.info("youtube_token_refresh_started")
            creds.refresh(Request())
            with open(TOKEN_FILE, "wb") as token:
                pickle.dump(creds, token)
            logger.info("youtube_token_refresh_complete")

        if not creds or not creds.valid:
            raise RuntimeError("youtube_auth_invalid_or_missing")

        logger.info("youtube_client_initialized")
        return build("youtube", "v3", credentials=creds)

    except Exception:
        logger.exception("youtube_client_init_failed")
        raise

def upload_video(
    counter,
    subreddit_name,
    video_file,
    title,
    description,
    scheduled_time=None,
    max_retries=3
):
    try:
        tags = PREDEFINED_TAGS

        formatted_title = sanitize_title(title)
        counter = random.randint(100, 1000)

        if len(title) > 100:
            formatted_title = f"Wholesome Meme {counter}"
            description = f"{title}\n{description}"

        hashtag_string = " ".join([f"#{t}" for t in tags])
        description = (
            f"{description}\n"
            f"{hashtag_string}\n"
            "This is just a parody."
        )

        youtube = get_youtube_client()

        body = {
            "snippet": {
                "title": formatted_title,
                "description": description,
                "tags": tags,
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "private" if scheduled_time else "public",
                "selfDeclaredMadeForKids": False
            }
        }

        if scheduled_time:
            iso_time = scheduled_time.isoformat("T") + "Z"
            body["status"]["publishAt"] = iso_time

        media = MediaFileUpload(
            video_file,
            chunksize=1024 * 1024,
            resumable=True
        )

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )

        attempt = 0

        while attempt < max_retries:
            try:
                logger.info(
                    "youtube_upload_attempt | attempt=%d file=%s",
                    attempt + 1,
                    video_file
                )

                response = None

                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(
                            "youtube_upload_progress | progress=%d%%",
                            progress
                        )

                video_id = response["id"]

                logger.info(
                    "youtube_upload_success | video_id=%s",
                    video_id
                )

                log_post(subreddit_name, title)
                log_post_time(subreddit_name, title)

                cleanup_files()
                return video_id

            except Exception as e:
                logger.exception(
                    "youtube_upload_attempt_failed | attempt=%d",
                    attempt + 1
                )

                log_error(subreddit_name, title, str(e))

                attempt += 1
                time.sleep(10)

        logger.error("youtube_upload_failed_max_retries")

        log_post(subreddit_name, title)
        cleanup_files()
        gc.collect()

        raise RuntimeError("youtube_upload_failed_after_retries")

    except Exception:
        logger.exception("youtube_upload_fatal_error")
        raise

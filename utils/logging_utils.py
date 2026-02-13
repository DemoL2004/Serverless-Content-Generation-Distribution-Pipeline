import os
import csv
import logging
from datetime import datetime

from config import ERROR_FILE, POST_TIMES_FILE, CSV_FILE
from services.storage_service import upload_to_gcs

logger = logging.getLogger(__name__)

def log_error(subreddit: str, title: str, error_message: str) -> None:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(ERROR_FILE, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([subreddit, title, error_message, current_time])

        upload_to_gcs(ERROR_FILE, os.path.basename(ERROR_FILE))

        logger.error(
            "error_logged | subreddit=%s title=%s",
            subreddit,
            title
        )

    except Exception:
        logger.exception(
            "error_logging_failed | subreddit=%s title=%s",
            subreddit,
            title
        )
        raise

def log_post_time(subreddit: str, title: str) -> None:
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(POST_TIMES_FILE, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([subreddit, title, current_time])

        upload_to_gcs(POST_TIMES_FILE, os.path.basename(POST_TIMES_FILE))

        logger.info(
            "post_time_logged | subreddit=%s title=%s",
            subreddit,
            title
        )

    except Exception:
        logger.exception(
            "post_time_logging_failed | subreddit=%s title=%s",
            subreddit,
            title
        )
        raise

def log_post(subreddit: str, title: str) -> None:
    normalized_title = normalize(title)

    try:
        with open(CSV_FILE, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([subreddit, normalized_title])

        upload_to_gcs(CSV_FILE, os.path.basename(CSV_FILE))

        logger.info(
            "post_logged | subreddit=%s title=%s",
            subreddit,
            normalized_title
        )

    except Exception:
        logger.exception(
            "post_logging_failed | subreddit=%s title=%s",
            subreddit,
            normalized_title
        )
        raise

def normalize(text: str) -> str:
    return text.strip().lower()

def is_post_logged(subreddit: str, title: str) -> bool:
    if not os.path.exists(CSV_FILE):
        return False

    normalized_title = normalize(title)

    try:
        with open(CSV_FILE, "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row == [subreddit, normalized_title]:
                    return True

    except Exception:
        logger.exception("post_log_read_failed")

    return False

def cleanup_files() -> None:
    files = [
        "compressed_short.mp4",
        "trimmed_tts_output.mp3",
        "downloaded_meme.jpg",
        "final_meme_video.mp4",
        "image_video.mp4",
        "mixed_audio.m4a",
        "trimmed_gameplay.mp4",
        "trimmed_music.mp3",
        "tts_output.mp3",
        "final_output.mp4",
        "merged_video.mp4",
        "OUT.mp4",
        "output_subtitles.srt"
    ]

    for file in files:
        try:
            if os.path.exists(file):
                os.remove(file)
                logger.info("temp_file_removed | file=%s", file)

        except Exception:
            logger.exception("temp_file_removal_failed | file=%s", file)

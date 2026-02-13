import sys
import gc
import logging

from utils.logger import setup_logging
from services.reddit_service import fetch_top_post
from services.tts_service import text_to_speech_with_alignment, save_srt
from services.video_service import create_video_from_image, merge_with_background, burn_srt_subtitles
from services.audio_service import merge_audio_tracks, trim_music_random, get_audio_duration
from services.youtube_service import upload_video
from services.storage_service import (
    get_random_music_file,
    get_next_gameplay_file,
    download_from_gcs
)
from utils.logging_utils import cleanup_files, log_error
from utils.job_control import should_run_job

logger = logging.getLogger(__name__)


CONFIG_PATH = "/tmp/reddit_config.json"


def main():
    setup_logging()

    logger.info("job_started")

    if not should_run_job(10):
        logger.info("job_skipped_threshold_condition")
        sys.exit(0)

    try:
        cleanup_files()

        # 🔴 REQUIRED: download runtime config
        download_from_gcs("reddit_config.json", CONFIG_PATH)

        logger.info("reddit_config_loaded")

        logger.info("fetching_reddit_post")
        title, image_path, subreddit_name = fetch_top_post(CONFIG_PATH)

        if not title:
            logger.warning("no_post_found_exiting")
            return

        logger.info("generating_tts")
        tts_audio, align_data = text_to_speech_with_alignment(
            title,
            config_blob_path=CONFIG_PATH
        )

        save_srt(align_data)

        duration = get_audio_duration(tts_audio) + 4

        logger.info("creating_static_video")
        video_image = create_video_from_image(image_path, duration)

        logger.info("selecting_music")
        music_file = get_random_music_file()
        trimmed_music = trim_music_random(music_file, duration)

        logger.info("merging_audio")
        mixed_audio = merge_audio_tracks(tts_audio, trimmed_music)

        logger.info("selecting_gameplay")
        gameplay_file = get_next_gameplay_file()

        logger.info("merging_video")
        merged_video = merge_with_background(video_image, gameplay_file, duration)

        logger.info("burning_subtitles")
        final_video = burn_srt_subtitles(
            merged_video,
            "output_subtitles.srt",
            "OUT.mp4"
        )

        logger.info("uploading_to_youtube")
        upload_video(
            0,
            subreddit_name,
            final_video,
            title,
            "Enjoy memes daily!"
        )

        gc.collect()
        logger.info("job_completed_successfully")

    except Exception as e:
        logger.exception("job_failed_unhandled_exception")
        log_error("unknown", "unknown", str(e))
        raise  # 🔴 Important: let Cloud Run mark job as FAILED


if __name__ == "__main__":
    main()

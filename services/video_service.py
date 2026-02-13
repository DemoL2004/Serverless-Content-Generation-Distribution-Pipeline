import os
import random
import subprocess
import logging

import cv2
import numpy as np
from PIL import Image

from config import FFMPEG_PATH, FFPROBE_PATH

logger = logging.getLogger(__name__)

def create_video_from_image(image_path, duration, output="image_video.mp4"):
    try:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"{image_path} not found")

        img = Image.open(image_path).convert("RGB")

        img_width, img_height = img.size
        img_array = np.array(img)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        resolution = (img_width, img_height)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        fps = 30
        out = cv2.VideoWriter(output, fourcc, fps, resolution)

        total_frames = int(duration * fps)

        for _ in range(total_frames):
            out.write(img_bgr)

        out.release()

        logger.info(
            "image_video_created | input=%s output=%s duration=%.2f",
            image_path,
            output,
            duration
        )

        return output

    except Exception:
        logger.exception("image_video_creation_failed")
        raise

def merge_with_background(foreground, gameplay_file, duration, output="merged_video.mp4"):
    try:
        logger.info(
            "gameplay_selected | file=%s duration=%.2f",
            gameplay_file,
            duration
        )

        result = subprocess.run(
            [
                FFPROBE_PATH,
                "-i", gameplay_file,
                "-show_entries", "format=duration",
                "-v", "quiet",
                "-of", "csv=p=0"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True
        )

        gameplay_duration = float(result.stdout.decode().strip())

        start_time = random.uniform(
            0,
            max(0, gameplay_duration - duration)
        )

        logger.info(
            "gameplay_trim_start | start_time=%.2f total_duration=%.2f",
            start_time,
            gameplay_duration
        )

        trimmed_gameplay = "trimmed_gameplay.mp4"

        subprocess.run(
            [
                FFMPEG_PATH,
                "-ss", str(start_time),
                "-i", gameplay_file,
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                trimmed_gameplay
            ],
            check=True
        )

        logger.info("gameplay_trim_complete | file=%s", trimmed_gameplay)

        subprocess.run(
            [
                FFMPEG_PATH,
                "-i", trimmed_gameplay,
                "-i", foreground,
                "-filter_complex",
                (
                    "[0:v]scale=1080:1920,setsar=1[bg];"
                    "[1:v]scale=920:-1:flags=lanczos,setsar=1[fg];"
                    "[bg][fg]overlay=(main_w-overlay_w)/2:30[outv]"
                ),
                "-map", "[outv]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "18",
                "-shortest",
                output
            ],
            check=True
        )

        logger.info(
            "video_overlay_complete | output=%s foreground=%s",
            output,
            foreground
        )

        return output

    except Exception:
        logger.exception("video_merge_failed")
        raise

def burn_srt_subtitles(input_video, subtitle_file, output_video):
    try:
        if not os.path.exists(subtitle_file) or os.path.getsize(subtitle_file) == 0:
            logger.warning("subtitle_missing_or_empty | skipping_overlay")
            return input_video

        force_style = (
            "FontName=Montserrat,"
            "FontSize=12,"
            "PrimaryColour=&H00FFFF00,"
            "Bold=1,"
            "Outline=2,"
            "OutlineColour=&H00000000,"
            "Shadow=0,"
            "Alignment=10"
        )

        subprocess.run(
            [
                FFMPEG_PATH,
                "-i", input_video,
                "-vf", f"subtitles='{subtitle_file}':force_style='{force_style}'",
                "-c:a", "copy",
                output_video
            ],
            check=True
        )

        logger.info(
            "subtitle_burn_complete | input=%s output=%s",
            input_video,
            output_video
        )

        return output_video

    except Exception:
        logger.exception("subtitle_burn_failed")
        raise

def compress_short(input_file, output_file="compressed_short.mp4", crf=26):
    try:
        subprocess.run(
            [
                FFMPEG_PATH,
                "-i", input_file,
                "-vf", "scale=720:-2",
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", str(crf),
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                output_file
            ],
            check=True
        )

        logger.info(
            "video_compression_complete | input=%s output=%s crf=%d",
            input_file,
            output_file,
            crf
        )

        return output_file

    except Exception:
        logger.exception("video_compression_failed")
        raise

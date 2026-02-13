import random
import subprocess
import logging

from config import FFMPEG_PATH, FFPROBE_PATH

logger = logging.getLogger(__name__)
# ----------------------------------------
# Audio Duration
# ----------------------------------------

def get_audio_duration(file_path: str) -> float:
    """
    Returns duration (in seconds) of an audio file using ffprobe.
    """
    result = subprocess.run(
        [
            FFPROBE_PATH,
            "-i", file_path,
            "-show_entries", "format=duration",
            "-v", "quiet",
            "-of", "csv=p=0"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    return float(result.stdout.decode().strip())


# ----------------------------------------
# Trim Music
# ----------------------------------------

def trim_music_random(music_file: str, duration: float, output="trimmed_music.mp3") -> str:
    """
    Trims a random segment of music to match required duration.
    """
    music_duration = get_audio_duration(music_file)

    if music_duration > duration + 1:
        start_time = random.uniform(0, music_duration - duration)
    else:
        start_time = 0

    logger.info("Trimming music segment | start_time=%.2f", start_time)

    command = [
        FFMPEG_PATH,
        "-ss", str(start_time),
        "-i", music_file,
        "-t", str(duration),
        "-c", "copy",
        output
    ]

    subprocess.run(command, check=True)

    logger.info("Music trimmed successfully | output=%s", output)
    return output


# ----------------------------------------
# Merge TTS + Music
# ----------------------------------------

def merge_audio_tracks(
    tts_audio: str,
    music_audio: str,
    output="mixed_audio.m4a"
) -> str:
    """
    Mixes TTS and background music with ducking effect.
    """

    tts_duration = get_audio_duration(tts_audio)
    logger.info("TTS duration calculated | duration=%.2f sec", tts_duration)

    tts_delay = 1.0
    duck_start = tts_delay
    duck_end = tts_delay + tts_duration

    command = [
        FFMPEG_PATH,
        "-i", tts_audio,
        "-i", music_audio,
        "-filter_complex",
        (
            f"[0:a]adelay={int(tts_delay * 1000)},volume=10.0[tts];"
            f"[1:a]volume='if(between(t,{duck_start},{duck_end}),0.3,1)'[music_ducked];"
            "[music_ducked][tts]amix=inputs=2:duration=longest:dropout_transition=0"
        ),
        "-c:a", "aac",
        "-shortest",
        output
    ]

    subprocess.run(command, check=True)

    logger.info("Audio tracks merged successfully | output=%s", output)
    return output

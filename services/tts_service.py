import re
import json
from io import BytesIO
from datetime import timedelta

import pydub
from elevenlabs import ElevenLabs

from config import ELEVEN_API_KEY

import logging

logger = logging.getLogger(__name__)

# Initialize ElevenLabs client once
client = ElevenLabs(api_key=ELEVEN_API_KEY)


# ----------------------------
# Text Processing Dictionaries
# ----------------------------

PROFANITY_FILTER = {
    "fuck": "fudge",
    "fucking": "freaking",
    "fucked": "messed up",
    "shit": "shoot",
    "shitty": "crappy",
    "bitch": "witch",
    "ass": "butt",
    "asshole": "jerk",
    "dick": "jerk",
    "piss": "pee",
    "pissed": "annoyed",
    "damn": "dang",
    "goddamn": "gosh dang",
    "hell": "heck",
    "crap": "crud",
    "bastard": "meanie",
    "slut": "player",
    "hoe": "mess",
    "whore": "drama queen",
    "motherfucker": "monster",
    "screw you": "forget you",
    "son of a bitch": "piece of work"
}

ACRONYM_DICT = {
    "fr": "for real",
    "idk": "I don't know",
    "idek": "I don't even know",
    "omg": "oh my gosh",
    "lol": "laughing out loud",
    "brb": "be right back",
    "btw": "by the way",
    "tbh": "to be honest",
    "smh": "shaking my head",
    "lmao": "laughing my butt off",
    "imo": "in my opinion",
    "imho": "in my humble opinion",
    "wtf": "what the fudge",
    "wth": "what the heck",
    "np": "no problem",
    "ftw": "for the win",
    "irl": "in real life",
    "fyi": "for your information",
    "asap": "as soon as possible",
    "bff": "best friend forever",
    "jk": "just kidding"
}


# ----------------------------
# Text Utilities
# ----------------------------

def expand_acronyms(text):
    for acro, full in ACRONYM_DICT.items():
        pattern = re.compile(rf"\b{re.escape(acro)}\b", re.IGNORECASE)
        text = pattern.sub(full, text)
    return text


def clean_profanity(text):
    for bad_word, safe_word in PROFANITY_FILTER.items():
        pattern = re.compile(rf"\b{re.escape(bad_word)}\b", re.IGNORECASE)
        text = pattern.sub(safe_word, text)
    return text


def clean_text_for_subtitles(text):
    return re.sub(r"[^\w\s]", "", text)


# ----------------------------
# TTS + Alignment
# ----------------------------

def text_to_speech_with_alignment(
    original_text,
    config_blob_path,
    output_audio="tts_output.mp3",
    trimmed_audio="trimmed_tts_output.mp3"
):
    """
    Generates TTS audio and performs forced alignment.
    Returns trimmed audio file path and adjusted word timings.
    """

    try:
        logger.info("tts_generation_started")

        preamble = "This meme is titled "
        full_text = preamble + original_text

        full_text = expand_acronyms(full_text)
        clean_text = clean_profanity(full_text)

        with open(config_blob_path, 'r') as f:
            config = json.load(f)

        voice_id = config.get("voice", {}).get("voice_id")
        voice_settings = config.get("voice", {}).get("settings", {})

        stream = client.text_to_speech.convert(
            text=clean_text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            voice_settings=voice_settings
        )

        with open(output_audio, "wb") as f:
            for chunk in stream:
                f.write(chunk)

        logger.info("tts_audio_generated | file=%s", output_audio)

        # Forced alignment
        with open(output_audio, "rb") as f:
            audio_data = BytesIO(f.read())

        transcription = client.forced_alignment.create(
            file=audio_data,
            text=clean_text
        )

        raw_word_timings = [
            {
                "text": word.text,
                "start": float(word.start),
                "end": float(word.end)
            }
            for word in transcription.words
        ]

        logger.info("forced_alignment_complete | word_count=%d", len(raw_word_timings))

        titled_end_time = None

        for idx, word in enumerate(raw_word_timings):
            if word["text"].lower() == "titled":
                titled_end_time = word["end"]
                following_words = raw_word_timings[idx + 1:]
                break
        else:
            logger.warning("preamble_trim_failed | returning_full_audio")
            return output_audio, raw_word_timings

        adjusted_timings = [
            {
                "text": w["text"],
                "start": round(w["start"] - titled_end_time, 3),
                "end": round(w["end"] - titled_end_time, 3)
            }
            for w in following_words
        ]

        trim_start_ms = int(titled_end_time * 1000)
        audio = pydub.AudioSegment.from_mp3(output_audio)
        trimmed_segment = audio[trim_start_ms:]
        trimmed_segment.export(trimmed_audio, format="mp3")

        logger.info(
            "tts_trim_complete | trimmed_file=%s adjusted_word_count=%d",
            trimmed_audio,
            len(adjusted_timings)
        )

        return trimmed_audio, adjusted_timings

    except Exception:
        logger.exception("tts_pipeline_failed")
        raise

# ----------------------------
# Subtitle Utilities
# ----------------------------

def sec_to_timestamp(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    millis = int(round((seconds - total_seconds) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def save_srt(word_timings, output_srt="output_subtitles.srt", offset_seconds=1.0):
    try:
        with open(output_srt, 'w', encoding='utf-8') as f:
            count = 1

            for word in word_timings:
                text = clean_text_for_subtitles(word["text"].strip().upper())

                if not text:
                    continue

                start = sec_to_timestamp(word["start"] + offset_seconds)
                end = sec_to_timestamp(word["end"] + offset_seconds)

                f.write(f"{count}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")

                count += 1

        logger.info("subtitles_written | file=%s lines=%d", output_srt, count - 1)

    except Exception:
        logger.exception("subtitle_generation_failed")
        raise

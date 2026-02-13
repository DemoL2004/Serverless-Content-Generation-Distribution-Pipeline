
# Serverless Content Generation & Distribution Pipeline

## Overview

A cloud-native automation pipeline that programmatically generates short-form video content by integrating multiple third-party APIs, performing dynamic media processing, and distributing scheduled uploads to YouTube.

This system demonstrates API orchestration, serverless file handling, multimedia processing, error recovery logic, and automated publishing workflows.

Designed for deployment in a serverless environment such as Google Cloud Run.

---

## Core Capabilities

- Reddit API integration (PRAW)
- Automated content selection with deduplication
- Text normalization and profanity filtering
- ElevenLabs Text-to-Speech generation
- Forced word-level alignment for subtitle timing
- Automated SRT subtitle generation
- Image-to-video rendering using OpenCV
- Background gameplay overlay rendering
- MP3 background music integration
- Dynamic audio mixing and ducking (FFmpeg)
- Google Cloud Storage integration
- Scheduled YouTube uploads via YouTube Data API
- CSV-based logging and retry protection
- Error threshold control to prevent repeated failures

---

## High-Level Architecture

Reddit API  
↓  
Content Selection & Filtering  
↓  
Text Processing  
↓  
TTS Generation (ElevenLabs)  
↓  
Forced Alignment → Subtitle Generation  
↓  
Image → Video Rendering (OpenCV)  
↓  
Audio Mixing (FFmpeg)  
↓  
Background Gameplay Overlay  
↓  
Video Compression  
↓  
YouTube Scheduled Upload  
↓  
Logging to Google Cloud Storage  

---

## Media Pipeline Components

### 1. Static Meme Rendering
- Converts downloaded image into a time-based MP4 video
- Frame generation via OpenCV

### 2. Background Gameplay Integration
- Random gameplay clip pulled from GCS
- Trimmed dynamically to match narration duration
- Meme overlaid using FFmpeg filter graph

### 3. Audio Processing
- TTS narration generation
- Background MP3 trimming
- Audio ducking during narration
- Mixed using FFmpeg filter_complex

### 4. Subtitle System
- Word-level forced alignment
- SRT file generation
- Burned directly into final video

---

## Technologies Used

- Python 3.x
- Google Cloud Run (Job-based execution)
- Google Cloud Storage (GCS)
- PRAW (Reddit API)
- ElevenLabs API
- YouTube Data API v3
- FFmpeg / FFprobe
- OpenCV
- Pillow
- pydub
- dotenv

---

## Cloud-Native Design

- Uses `/tmp` for ephemeral storage (Cloud Run compatible)
- No persistent disk reliance
- All media assets stored in GCS:
  - gameplay/
  - music/
  - logs
  - configuration JSON
- Structured logging via Python logging module
- Retry protection for upload failures
- Error threshold control before job execution

---

## Security Practices

- No hardcoded secrets
- Environment variable-based configuration
- OAuth token stored securely (not committed)
- Title sanitization before upload
- Profanity normalization before TTS
- GitHub secret scanning compliance

---

## Example Workflow

1. Fetch top Reddit post from configured subreddits
2. Validate and deduplicate content
3. Generate TTS narration
4. Align words and generate subtitles
5. Create static image video
6. Trim background music
7. Mix narration + music with ducking
8. Trim gameplay clip
9. Overlay meme onto gameplay
10. Burn subtitles
11. Upload to YouTube
12. Log results to Cloud Storage

---

## Project Structure

services/  
    reddit_service.py  
    tts_service.py  
    video_service.py  
    audio_service.py  
    youtube_service.py  
    storage_service.py  
    
utils/  
    logging_utils.py  
    job_control.py  
    logger.py   

config.py  
main.py   
Dockerfile   
requirements.txt  


---

## Deployment

Designed for:

- Google Cloud Run Jobs
- Containerized Python environment
- Linux-based serverless runtime

### Requirements

- FFmpeg installed in container
- Google Cloud credentials configured
- Environment variables set
- GCS bucket configured
- OAuth token generated locally

---

## Future Enhancements

- Observability metrics (Cloud Monitoring)
- Structured JSON logging export
- Parallel content generation
- Queue-based scaling
- YAML configuration support
- CI/CD pipeline integration

---

## License

Educational and automation demonstration project.

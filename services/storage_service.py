import os
import random
import logging
from google.cloud import storage
from config import BUCKET_NAME, LOCAL_MUSIC_DIR, LOCAL_GAMEPLAY_DIR

logger = logging.getLogger(__name__)

# Initialize GCS client once
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)


def download_from_gcs(blob_name, local_path=None):
    """
    Downloads a blob from GCS to local file.
    Defaults to /tmp/<blob_name> for Cloud Run compatibility.
    """
    if local_path is None:
        local_path = f"/tmp/{blob_name}"

    try:
        blob = bucket.blob(blob_name)
        blob.download_to_filename(local_path)

        logger.info(
            "gcs_download_success | bucket=%s blob=%s local_path=%s",
            BUCKET_NAME,
            blob_name,
            local_path
        )

        return local_path

    except Exception:
        logger.exception(
            "gcs_download_failed | bucket=%s blob=%s",
            BUCKET_NAME,
            blob_name
        )
        raise


def upload_to_gcs(local_path: str, blob_name: str):
    """
    Uploads a local file to GCS, overwriting existing object.
    """
    try:
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(local_path)

        logger.info(
            "gcs_upload_success | bucket=%s blob=%s local_path=%s",
            BUCKET_NAME,
            blob_name,
            local_path
        )

    except Exception:
        logger.exception(
            "gcs_upload_failed | bucket=%s blob=%s",
            BUCKET_NAME,
            blob_name
        )
        raise


def get_random_music_file():
    """
    Downloads a random .mp3 file from GCS music/ folder.
    """
    blobs = list(bucket.list_blobs(prefix="music/"))
    music_blobs = [blob for blob in blobs if blob.name.endswith(".mp3")]

    if not music_blobs:
        logger.error("no_music_files_found_in_gcs")
        raise FileNotFoundError("No music files found in GCS.")

    selected_blob = random.choice(music_blobs)

    os.makedirs(LOCAL_MUSIC_DIR, exist_ok=True)
    local_path = os.path.join(
        LOCAL_MUSIC_DIR,
        os.path.basename(selected_blob.name)
    )

    selected_blob.download_to_filename(local_path)

    logger.info(
        "music_selected | blob=%s local_path=%s",
        selected_blob.name,
        local_path
    )

    return local_path


def get_next_gameplay_file():
    """
    Downloads a random gameplay .mp4 file from GCS gameplay/ folder.
    """
    blobs = list(bucket.list_blobs(prefix="gameplay/"))
    gameplay_blobs = [blob for blob in blobs if blob.name.endswith(".mp4")]

    if not gameplay_blobs:
        logger.error("no_gameplay_files_found_in_gcs")
        raise FileNotFoundError("No gameplay files found in GCS.")

    selected_blob = random.choice(gameplay_blobs)

    os.makedirs(LOCAL_GAMEPLAY_DIR, exist_ok=True)
    local_path = os.path.join(
        LOCAL_GAMEPLAY_DIR,
        os.path.basename(selected_blob.name)
    )

    selected_blob.download_to_filename(local_path)

    logger.info(
        "gameplay_selected | blob=%s local_path=%s",
        selected_blob.name,
        local_path
    )

    return local_path

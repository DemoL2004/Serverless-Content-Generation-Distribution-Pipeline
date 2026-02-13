import os
import csv
import logging
from datetime import datetime, timedelta

from services.storage_service import download_from_gcs
from config import ERROR_FILE

logger = logging.getLogger(__name__)


def should_run_job(threshold_hours: int = 10) -> bool:
    """
    Determines whether the Cloud Run Job should execute
    based on the timestamp of the last logged error.
    """

    try:
        download_from_gcs("errors.csv", local_path=ERROR_FILE)
        logger.info("job_control | errors_csv_downloaded")

    except Exception:
        logger.warning(
            "job_control | errors_csv_download_failed → allowing_execution"
        )
        return True

    if not os.path.exists(ERROR_FILE):
        logger.info(
            "job_control | errors_csv_missing → allowing_execution"
        )
        return True

    last_row = None

    try:
        with open(ERROR_FILE, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    last_row = row
    except Exception:
        logger.exception(
            "job_control | errors_csv_read_failed → allowing_execution"
        )
        return True

    if not last_row:
        logger.info(
            "job_control | errors_csv_empty → allowing_execution"
        )
        return True

    try:
        timestamp_str = last_row[3]
        last_dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

    except Exception:
        logger.warning(
            "job_control | invalid_timestamp_format → allowing_execution"
        )
        return True

    now = datetime.now()
    age = now - last_dt

    logger.info(
        "job_control | last_error_age_hours=%.2f threshold=%d",
        age.total_seconds() / 3600,
        threshold_hours
    )

    if age > timedelta(hours=threshold_hours):
        logger.info("job_control | threshold_passed → running_job")
        return True

    logger.info("job_control | threshold_not_met → skipping_job")
    return False

# videobot/tasks.py
from pathlib import Path
from celery_app import celery
from videobot.engine import make_videos

@celery.task(bind=True)
def run_video_job(self, cfg: dict) -> str:
    """
    Celery wrapper. Returns the output folder path as a string.
    """
    folder: Path = make_videos(cfg)
    return str(folder)

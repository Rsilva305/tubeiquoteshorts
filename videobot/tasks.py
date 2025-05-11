# ── videobot/tasks.py ───────────────────────────────────────
from pathlib import Path
from celery import Celery
from videobot import engine      # your heavy video maker

from celery_app import celery    # import the Celery() object

@celery.task(bind=True)
def run_video_job(self, cfg: dict):
    """
    Celery entry-point.  Returns a dict:
      { "folder": "/app/customers/acme_inc",
        "files":  ["0-foo.mp4", "1-bar.mp4"] }
    """
    output_path: Path = engine.make_videos(cfg)

    # gather every .mp4 the engine produced
    files = [p.name for p in Path(output_path).glob("*.mp4")]

    # task result saved in Redis → web service can read it
    return {"folder": str(output_path), "files": files}

# ── webapp.py ────────────────────────────────────────────────
"""
FastAPI front-end for Quote-Video-Maker
--------------------------------------
• POST  /generate          -> queue a new video job, return job_id
• GET   /status/{job_id}   -> check progress / get output folder
This file assumes you already have:
    celery_app.py          (defines Celery() instance)
    videobot/tasks.py      (run_video_job Celery task)
    videobot/engine.py     (make_videos(cfg) heavy function)
"""
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Celery imports
from celery.result import AsyncResult
from videobot.tasks import run_video_job       # our Celery wrapper

# ─────────────────────────────────────────────────────────────
app = FastAPI(title="Quote-Video-Maker API", version="0.3.0")

# Helpers for absolute paths ---------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent    # project root

def rel(*bits: str) -> str:
    """Return an *absolute* Windows-friendly path inside the project."""
    return str(BASE_DIR.joinpath(*bits))

# Request body model -----------------------------------------------------------
class JobRequest(BaseModel):
    customer_name: str = Field(..., examples=["acme_inc"])
    number_of_videos: int = Field(1, ge=1, le=20)

# Build the cfg dict expected by videobot.engine -------------------------------
def build_cfg(job: JobRequest) -> dict:
    return {
        "video_folder":     rel("videos"),
        "audio_folder":     rel("audio"),
        "json_file":        rel("sources", "verses_data", "motivation_data.json"),
        "fonts_dir":        rel("sources", "fonts"),
        "output_folder":    rel("customers"),
        "text_source_font": rel("sources", "MouldyCheeseRegular-WyMWG.ttf"),
        "image_file":       rel("sources", "logo.png"),

        "customer_name":    job.customer_name,
        "number_of_videos": job.number_of_videos,

        # lists copied from your original main.py
        "fonts_paths": [
            rel("sources", "fonts", "CoffeeJellyUmai.ttf"),
            rel("sources", "fonts", "CourierprimecodeRegular.ttf"),
            rel("sources", "fonts", "PineappleDays.ttf"),
            rel("sources", "fonts", "GreenTeaJelly.ttf"),
            rel("sources", "fonts", "HeyMarch.ttf"),
            rel("sources", "fonts", "LetsCoffee.ttf"),
            rel("sources", "fonts", "LikeSlim.ttf"),
            rel("sources", "fonts", "SunnySpellsBasicRegular.ttf"),
            rel("sources", "fonts", "TakeCoffee.ttf"),
            rel("sources", "fonts", "WantCoffee.ttf"),
        ],
        "fonts_sizes":        [95, 70, 65, 85, 75, 50, 75, 87, 50, 65],
        "fonts_maxcharsline": [34, 25, 30, 45, 33, 34, 35, 32, 35, 35],
    }

# POST /generate ----------------------------------------------------------------
@app.post("/generate")
async def generate(job: JobRequest):
    cfg  = build_cfg(job)
    task = run_video_job.apply_async(args=[cfg])     # enqueue
    return {"job_id": task.id, "status": "queued"}

# GET /status/{job_id} ----------------------------------------------------------
@app.get("/status/{job_id}")
async def status(job_id: str):
    res = AsyncResult(job_id, app=run_video_job.app)  # connect to Redis backend

    if res.state == "PENDING":
        return {"status": "queued"}
    if res.state == "STARTED":
        return {"status": "working"}
    if res.state == "SUCCESS":
        return {"status": "done", "folder": res.result}
    if res.state == "FAILURE":
        return {"status": "error", "detail": str(res.result)}

    raise HTTPException(status_code=500, detail=f"unknown state {res.state}")

# ─────────────────────────────────────────────────────────────

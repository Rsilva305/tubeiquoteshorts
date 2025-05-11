# ── webapp.py ────────────────────────────────────────────────
"""
FastAPI front-end for Quote-Video-Maker
--------------------------------------
• POST  /generate              → queue a new video job, return job_id
• GET   /status/{job_id}       → check progress / get output folder
• GET   /download/{path:path}  → stream any file in /app/customers/…
"""
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Celery
from celery.result import AsyncResult
from videobot.tasks import run_video_job       # our Celery task wrapper

# ─────────────────────────────────────────────────────────────
app = FastAPI(title="Quote-Video-Maker API", version="0.4.0")

BASE_DIR: Path = Path(__file__).resolve().parent
CUSTOMERS_DIR = Path("/app/customers")          # <-- worker writes here

def rel(*bits: str) -> str:
    return str(BASE_DIR.joinpath(*bits))

# ─────── request model ───────────────────────────────────────
class JobRequest(BaseModel):
    customer_name: str = Field(..., examples=["acme_inc"])
    number_of_videos: int = Field(1, ge=1, le=20)

# ─────── helper to build cfg dict ────────────────────────────
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

# ─────── routes ──────────────────────────────────────────────
@app.post("/generate")
async def generate(job: JobRequest):
    task = run_video_job.apply_async(args=[build_cfg(job)])
    return {"job_id": task.id, "status": "queued"}

@app.get("/status/{job_id}")
async def status(job_id: str):
    res = AsyncResult(job_id, app=run_video_job.app)
    if res.state == "PENDING":
        return {"status": "queued"}
    if res.state == "STARTED":
        return {"status": "working"}
    if res.state == "SUCCESS":
        return {"status": "done", "folder": res.result}
    if res.state == "FAILURE":
        return {"status": "error", "detail": str(res.result)}
    raise HTTPException(500, f"unknown state {res.state}")

# NEW ───── download any file written to /app/customers ───────
@app.get("/download/{path:path}")
def download(path: str):
    fp = CUSTOMERS_DIR / path
    if not fp.exists():
        raise HTTPException(404, "file not found")
    return FileResponse(fp)

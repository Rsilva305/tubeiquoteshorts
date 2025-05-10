# webapp.py
from uuid import uuid4
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from videobot.engine import make_videos        # we wrote this in Step 1

app = FastAPI(title="Quote-Video-Maker API", version="0.1.0")

# ----  Data the customer sends in the request  -----------------
class JobRequest(BaseModel):
    customer_name: str                       = Field(..., examples=["acme_inc"])
    number_of_videos: int                    = Field(1, ge=1, le=20)
    # add more optional knobs later (font, logo, etc.)

# ----  Simple in-memory “database” just for today  --------------
JOBS: dict[str, dict] = {}     # job_id → {"status": "...", "folder": Path|None}

# ----  Endpoint the browser/JS will call  -----------------------
@app.post("/generate")
async def generate(job: JobRequest, tasks: BackgroundTasks):
    job_id = uuid4().hex
    cfg = {
        # hard-code your own folders for now
        "video_folder": "videos",
        "audio_folder": "audio",
        "json_file": "sources/verses_data/motivation_data.json",
        "fonts_dir": "sources/fonts",
        "output_folder": "customers",
        "text_source_font": "sources/MouldyCheeseRegular-WyMWG.ttf",
        "image_file": "sources/logo.png",
        "customer_name": job.customer_name,
        "number_of_videos": job.number_of_videos,
        # these three lists are copied from main.py  :contentReference[oaicite:0]{index=0}:contentReference[oaicite:1]{index=1}
        "fonts_paths": [                     # ← paste your 10 font paths
            "sources/fonts/CoffeeJellyUmai.ttf",
            "sources/fonts/CourierprimecodeRegular.ttf",
            # …
        ],
        "fonts_sizes": [95, 70, 65, 85, 75, 50, 75, 87, 50, 65],
        "fonts_maxcharsline": [34, 25, 30, 45, 33, 34, 35, 32, 35, 35],
    }

    # record that the job is queued
    JOBS[job_id] = {"status": "queued", "folder": None}

    # run the heavy function **after** the HTTP response goes out
    tasks.add_task(run_job, job_id, cfg)
    return {"job_id": job_id, "status": "queued"}

async def run_job(job_id: str, cfg: dict):
    try:
        JOBS[job_id]["status"] = "working"
        out_folder = make_videos(cfg)        # calls ffmpeg.create_videos under the hood :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}
        JOBS[job_id] = {"status": "done", "folder": str(out_folder)}
    except Exception as e:
        JOBS[job_id] = {"status": f"error: {e}", "folder": None}

@app.get("/status/{job_id}")
async def status(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="job_id not found")
    return JOBS[job_id]

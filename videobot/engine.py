# videobot/engine.py
import os
from pathlib import Path
from uuid import uuid4
import ffmpeg  # your existing module
from Fonts import Fonts         # your existing helper
import json_handler             # existing
import verse_handler            # existing

def make_videos(cfg: dict) -> Path:
    """
    cfg keys (all strings unless noted):
        video_folder, audio_folder, json_file, fonts_dir,
        output_folder, text_source_font, image_file,
        customer_name, number_of_videos (int)
    Returns: Path to the output directory that now contains the videos.
    """
    fonts = Fonts(cfg["fonts_paths"],
                  cfg["fonts_sizes"],
                  cfg["fonts_maxcharsline"])

    ffmpeg.create_videos(
        video_folder=cfg["video_folder"],
        audio_folder=cfg["audio_folder"],
        json_file=cfg["json_file"],
        fonts_dir=cfg["fonts_dir"],
        output_folder=cfg["output_folder"],
        text_source_font=cfg["text_source_font"],
        image_file=cfg["image_file"],
        customer_name=cfg["customer_name"],
        number_of_videos=cfg["number_of_videos"],
        fonts=fonts,
    )
    return Path(cfg["output_folder"]) / cfg["customer_name"]

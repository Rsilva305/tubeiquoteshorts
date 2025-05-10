# ── ffmpeg.py (full file) ─────────────────────────────────────────
import os
import pickle
import random
import subprocess
import shlex          # ← NEW
import re
import sys
import time
import json_handler
import verse_handler
import Fonts
import cv2


def create_dirs(output_folder, customer_name, posts=True):
    output_path = f"{output_folder}/{customer_name}"
    os.makedirs(f"{output_path}/verse_images", exist_ok=True)
    if posts:
        os.makedirs(f"{output_path}/post_images", exist_ok=True)
    return output_path


def create_videos(video_folder, audio_folder, json_file, fonts_dir, output_folder,
                  text_source_font, image_file, customer_name, number_of_videos,
                  fonts: Fonts, posts=False):

    verses, refs = json_handler.get_data(json_file)
    if number_of_videos == -1:
        number_of_videos = len(verses) - 1

    start_time_total = time.time()
    videos_num, audios_num, fonts_num = [], [], []

    video_files = [f"{video_folder}/{f}" for f in os.listdir(video_folder) if f.endswith(".mp4")]
    audio_files = [f"{audio_folder}/{f}" for f in os.listdir(audio_folder) if f.endswith(".mp3")]

    random_for_video = random.randint(0, len(video_files) - 1)
    random_for_audio = random.randint(0, len(audio_files) - 1)
    random_for_font  = random.randint(0, len(fonts.fonts_path) - 1)

    for i in range(number_of_videos):
        videos_num.append((random_for_video + i) % len(video_files))
        audios_num.append((random_for_audio + i) % len(audio_files))
        fonts_num.append((random_for_font  + i) % len(fonts.fonts_path))

    random.shuffle(videos_num)
    random.shuffle(audios_num)
    random.shuffle(fonts_num)

    output_path = create_dirs(output_folder, customer_name, posts)

    col1 = col2 = col3 = []
    avg_runtime = get_avg_runtime("runtime.pk")
    if avg_runtime != -1:
        est = round(avg_runtime * number_of_videos, 2)
        print("\033[0;32mEstimated run time:", est, "seconds\033[0m")

    for i in range(number_of_videos):
        t0 = time.time()
        print(f"Creating Video #{i}")

        video_file = video_files[videos_num.pop()]
        audio_file = audio_files[audios_num.pop()]

        rnd_font = fonts_num.pop()
        font_file, font_size, font_chars = (
            fonts.fonts_path[rnd_font],
            fonts.fonts_size[rnd_font],
            fonts.fonts_chars_limit[rnd_font],
        )

        text_verse, text_source = verses[i], refs[i]
        src_img  = text_source.replace(":", "").rstrip()
        src_name = src_img.replace(" ", "")
        file_name = f"/{i}-{src_name}_{os.path.basename(video_file).split('.')[0]}.mp4"

        create_video(
            text_verse, text_source, text_source_font, src_img,
            video_file, audio_file, image_file,
            font_file, font_size, font_chars,
            output_path, file_name, posts
        )

        col1.append(file_name.strip("/"))
        col2.append(text_source)
        col3.append(text_verse)

        print(f"\033[0;34m DONE #{i}, Run time:", round(time.time()-t0,2),"s\033[0m", output_path)

    verse_handler.add_sheets(col1, output_path, customer_name, col2, col3)

    if number_of_videos > 1:
        new_avg = (avg_runtime + (time.time()-start_time_total)/number_of_videos)/2
        update_avg_runtime(new_avg, "runtime.pk")


def create_video(text_verse, text_source, text_source_font, src_img,
                 video_file, audio_file, image_file,
                 font_file, font_size, font_chars,
                 output_path, file_name, posts=True):

    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=width,height",
         "-of", "csv=p=0:s=x", video_file],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    w, h = map(int, re.findall(r"\d+", result.stdout.decode())[:2])

    vid_dur = float(subprocess.check_output(
        shlex.split(f'ffprobe -i "{video_file}" -show_entries format=duration -v quiet -of csv="p=0"')
    ).decode().strip())

    verse_img, verse_h = verse_handler.create_image(
        text_verse, font_file, font_size, font_chars,
        (w, h//2), output_path, src_img, text_color=(255,255,255,255))

    img_y, ref_y, txt_y = 0, 800, 800 + verse_h + 75
    if txt_y > 1200:
        diff = txt_y - 1200
        txt_y, ref_y = 1200, ref_y - diff

    text_source = text_source.replace(":", "\\:")
    out_path = f"{output_path}{file_name}"

    ffmpeg_cmd = (
        f'ffmpeg -loglevel error -stats -y -loop 1 -i "{image_file}" -i "{audio_file}" '
        f'-i "{video_file}" -i "{verse_img}" -r 24 -filter_complex '
        f'"[2:v][0:v]overlay=(W-w)/2:{img_y}[v1]; '
        f'[v1]drawtext=fontfile=\'{text_source_font}\':text=\'{text_source}\':'
        f'x=(w-text_w)/2:y={txt_y}:fontsize=42:fontcolor=white:enable=\'between(t,1,{vid_dur})\'[v2]; '
        f'[v2][3:v]overlay=(W-w)/2:{ref_y}:enable=\'between(t,1,{vid_dur})\'[v3]" '
        f'-t {vid_dur} -map "[v3]" -map 1 -c:v libx264 -preset veryfast -crf 18 "{out_path}"'
    )

    subprocess.check_call(shlex.split(ffmpeg_cmd))   # ← FIXED

    if posts:
        verse_handler.create_post_images(out_path, f"{output_path}/post_images")


def get_avg_runtime(filename):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except (EOFError, FileNotFoundError):
        return -1


def update_avg_runtime(val, filename):
    with open(filename, "wb") as f:
        pickle.dump(val, f)

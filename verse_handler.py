# ── verse_handler.py  (FULL FILE) ─────────────────────────────────
import csv
import textwrap
from pathlib import Path
from string import ascii_letters
from PIL import Image, ImageDraw, ImageFont

# ---------- CONFIG ------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
FALLBACK_FONT = BASE_DIR.joinpath(
    "..", "sources", "fonts", "PermanentMarker-Regular.ttf"  # <-- make sure this file exists
).resolve()

# ---------- SAFE FONT LOADER -------------------------------------
def load_font_safe(path: str | Path, size: int) -> ImageFont.FreeTypeFont:
    """Try chosen font → fallback font → built-in default (never crash)."""
    print("DEBUG – trying font:", path, flush=True)
    try:
        return ImageFont.truetype(str(path), size=size)
    except OSError:
        print("WARNING – font unusable, falling back to:", FALLBACK_FONT, flush=True)
        try:
            return ImageFont.truetype(str(FALLBACK_FONT), size=size)
        except OSError:
            print("ERROR – fallback font missing; using built-in default", flush=True)
            return ImageFont.load_default()

# ---------- IMAGE CREATION (USED BY FFMPEG) -----------------------
def create_image(
    text: str,
    font_path: str,
    font_size: int,
    max_char_count: int,
    image_size: tuple[int, int],
    save_path: str,
    text_source: str,
    text_color=(255, 255, 255, 255),
):
    save_path = Path(save_path) / "verse_images"
    save_path.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", image_size, color=(190, 190, 190, 0))
    font = load_font_safe(font_path, font_size)

    avg_char_w = sum(font.getbbox(ch)[2] for ch in ascii_letters) / len(ascii_letters)
    max_char_count = max(int(img.size[0] * 0.718 / avg_char_w), max_char_count)
    wrapped = textwrap.fill(text, width=max_char_count)

    shadow = Image.new("RGBA", img.size, (255, 255, 255, 0))
    ImageDraw.Draw(shadow).text(
        (img.size[0] / 2 - 1, img.size[1] / 2 + 4),
        wrapped, font=font, fill=(0, 0, 0, 80),
        anchor="mm", align="center"
    )
    draw = ImageDraw.Draw(img)
    draw.text(
        (img.size[0] / 2, img.size[1] / 2),
        wrapped, font=font, fill=text_color,
        anchor="mm", align="center"
    )

    final = Image.alpha_composite(shadow, img).crop(img.getbbox())
    rendered_h = final.height

    fname = (text_source or "verse").replace(":", "")
    out = save_path / f"{fname}.png"
    i = 1
    while out.exists():
        out = save_path / f"{fname}-{i}.png"; i += 1
    final.save(out)
    return str(out), rendered_h

# ---------- HELPERS NEEDED BY ffmpeg.py ---------------------------
def add_sheets(video_names, output_path, customer_name, refs, verses):
    """Create a simple CSV with (video, reference, verse) rows."""
    csv_path = Path(output_path) / f"{customer_name}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["File Name", "Reference", "Verse"])
        for v, r, t in zip(video_names, refs, verses):
            w.writerow([v, r, t])

def rename_videos(video_folder, csv_file):
    """Stub.  Implement if you need smarter renaming later."""
    pass

def get_new_file_name(reference: str) -> str:
    """Return a safe filename for a Bible reference (or any reference)."""
    return reference.replace(":", "_").strip("(ESV)").strip()[:100] + ".mp4"

def fix_fonts(text: str, font_path: str):
    text = text.replace("—", "-")
    if "FlowersSunday" in font_path:
        return text.replace("'", "")
    return text

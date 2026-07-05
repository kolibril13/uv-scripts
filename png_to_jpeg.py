# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow",
# ]
# ///

print("Converting PNG images in Downloads to JPEG format...")
from pathlib import Path
from PIL import Image

downloads = Path.home() / "Downloads"

# Use the same cache folder as convert_mov_to_mp4.py
cache = downloads / "cache"
cache.mkdir(exist_ok=True)


def move_to_cache(path: Path) -> Path:
    """Move a file into cache/ without overwriting an existing file."""
    dest = cache / path.name
    counter = 2
    while dest.exists():
        dest = cache / f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    path.rename(dest)
    return dest


for png in downloads.glob("*.png"):
    jpeg = png.with_suffix(".jpeg")

    # Flatten any transparency (incl. palette-mode PNGs) onto a white background
    img = Image.open(png).convert("RGBA")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.getchannel("A"))

    bg.save(jpeg, "JPEG", quality=70)

    # Move original PNG using the cache folder
    move_to_cache(png)

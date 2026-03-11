# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow",
# ]
# ///

print("Converting PNG images in Downloads to WebP format...")
from pathlib import Path
from PIL import Image

downloads = Path.home() / "Downloads"

# Use the same cache folder as convert_mov_to_mp4.py
cache = downloads / "cache"
cache.mkdir(exist_ok=True)

for png in downloads.glob("*.png"):
    webp = png.with_suffix(".webp")
    img = Image.open(png)

    # Handle alpha transparencies - WebP supports alpha, but for smaller size convert to RGB
    if img.mode in ("RGBA", "LA", "PA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        img = bg
    else:
        img = img.convert("RGB")

    img.save(webp, "WEBP", quality=70, method=6)

    # Move original PNG using the cache folder
    png.rename(cache / png.name)
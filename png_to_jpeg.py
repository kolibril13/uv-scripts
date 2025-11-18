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
archive = downloads / "old_original_images"
archive.mkdir(exist_ok=True)

for png in downloads.glob("*.png"):
    jpeg = png.with_suffix(".jpeg")
    img = Image.open(png)

    # Handle alpha transparencies
    if img.mode in ("RGBA", "LA", "PA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        img = bg
    else:
        img = img.convert("RGB")

    img.save(jpeg, "JPEG", quality=70)

    # Move original PNG using pathlib
    png.rename(archive / png.name)
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow",
# ]
# ///

from pathlib import Path
from PIL import Image

# Define paths
desktop_path = Path.home() / "Downloads"

# Scan for PNG files and convert to JPEG
for png_file in desktop_path.glob("*.png"):
    jpeg_file = png_file.with_suffix(".jpeg")
    img = Image.open(png_file).convert("RGB")
    img.save(jpeg_file, "JPEG", quality=70)

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ffmpeg-python",
# ]
# ///

# header generated with
# uv add --script script.py ffmpeg-python

from pathlib import Path
import ffmpeg
import shutil

source_path = Path.home() / "Desktop"
downloads_path = Path.home() / "Downloads"

cache_path = downloads_path / "cache"
cache_path.mkdir(exist_ok=True)

for file_path in source_path.glob("*.mov"):
    output_file = downloads_path / file_path.with_suffix(".mp4").name

    try:
        # Convert the video to .mp4 format
        ffmpeg.input(str(file_path)).output(str(output_file), vcodec='libx264', acodec='aac').run()
        print(f"Converted: {file_path} -> {output_file}")

        # Move the old .mov file into cache folder
        shutil.move(str(file_path), cache_path / file_path.name)
        print(f"Moved original .mov to: {cache_path / file_path.name}")

    except ffmpeg.Error as e:
        print(f"Error converting {file_path}: {e}")

print("Conversion complete.")
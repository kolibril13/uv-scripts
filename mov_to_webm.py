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
    output_file = downloads_path / file_path.with_suffix(".webm").name

    try:
        # Convert the video to .webm format
        ffmpeg.input(str(file_path)).output(
            str(output_file),
            vcodec='libvpx-vp9',
            crf=32,
            **{'b:v': 0},
            pix_fmt='yuv420p',
            acodec='libopus',
        ).overwrite_output().run(capture_stdout=True, capture_stderr=True)
        print(f"Converted: {file_path} -> {output_file}")

        # Move the old .mov file into cache folder
        shutil.move(str(file_path), cache_path / file_path.name)
        print(f"Moved original .mov to: {cache_path / file_path.name}")

    except ffmpeg.Error as e:
        err = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
        print(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")

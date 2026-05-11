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

downloads_path = Path.home() / "Downloads"
cache_path = downloads_path / "cache"
cache_path.mkdir(exist_ok=True)

for file_path in downloads_path.glob("*.mp4"):
    # Skip outputs of previous runs.
    if file_path.stem.endswith("_web"):
        continue

    output_file = file_path.with_name(file_path.stem + "_web.mp4")

    try:
        stream = ffmpeg.input(str(file_path))

        ffmpeg.output(
            stream.video,
            str(output_file),
            vcodec='libx264',
            preset='medium',
            crf=23,
            pix_fmt='yuv420p',
            movflags='+faststart',
            an=None,
        ).overwrite_output().run(capture_stdout=True, capture_stderr=True)
        print(f"Converted: {file_path} -> {output_file}")

        shutil.move(str(file_path), cache_path / file_path.name)
        print(f"Moved original .mp4 to: {cache_path / file_path.name}")

    except ffmpeg.Error as e:
        err = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
        print(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")

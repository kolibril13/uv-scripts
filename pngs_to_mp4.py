# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# Requires the ffmpeg CLI (e.g. `brew install ffmpeg`)

from pathlib import Path
import subprocess

from settings import END_HOLD_SECONDS

# Find the latest created folder IN THE CACHE FOLDER in Downloads
downloads_path = Path.home() / "Downloads"
cache_path = downloads_path / "cache"
cache_path.mkdir(exist_ok=True)

# Find all subfolders in the cache folder
dirs = [d for d in cache_path.iterdir() if d.is_dir()]
if not dirs:
    raise RuntimeError("No folders found in cache.")
latest_folder = max(dirs, key=lambda d: d.stat().st_ctime)

# Output video filename (in Downloads), named after the source folder so
# consecutive runs don't overwrite each other
output_video = downloads_path / f"{latest_folder.name}.mp4"

try:
    png_files = sorted(latest_folder.glob("*.png"))
    if not png_files:
        raise ValueError("No PNG files found in the latest cache folder.")

    # libx264 + yuv420p requires even dimensions
    video_filters = "scale=ceil(iw/2)*2:ceil(ih/2)*2"
    if END_HOLD_SECONDS > 0:
        # hold the last frame as a still for the configured duration
        video_filters += f",tpad=stop_mode=clone:stop_duration={END_HOLD_SECONDS}"

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-pattern_type", "glob",
            "-framerate", "24",
            "-i", str(latest_folder / "*.png"),
            "-vf", video_filters,
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            str(output_video),
        ],
        check=True,
        capture_output=True,
    )

    print(f"Video created successfully: {output_video}")

except subprocess.CalledProcessError as e:
    err = e.stderr.decode("utf-8", errors="replace")
    print(f"An error occurred during conversion:\n{err}")
except Exception as e:
    print(f"An error occurred: {e}")

print("Process complete.")

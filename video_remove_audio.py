# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# Requires the ffmpeg CLI (e.g. `brew install ffmpeg`)

from pathlib import Path
import shutil
import subprocess

downloads_path = Path.home() / "Downloads"
cache_path = downloads_path / "cache"
cache_path.mkdir(exist_ok=True)

video_suffixes = {".mp4", ".mov", ".mkv", ".webm", ".m4v"}


def move_to_cache(path: Path) -> Path:
    """Move a file into cache/ without overwriting an existing file."""
    dest = cache_path / path.name
    counter = 2
    while dest.exists():
        dest = cache_path / f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    shutil.move(str(path), dest)
    return dest


for file_path in downloads_path.iterdir():
    if not file_path.is_file() or file_path.suffix.lower() not in video_suffixes:
        continue

    # Skip outputs of previous runs.
    if file_path.stem.endswith("_noaudio"):
        continue

    output_file = file_path.with_name(file_path.stem + "_noaudio" + file_path.suffix)

    try:
        # Drop the audio track, keep the video stream untouched.
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-an",
                "-c:v", "copy",
                "-movflags", "+faststart",
                str(output_file),
            ],
            check=True,
            capture_output=True,
        )
        print(f"Removed audio: {file_path} -> {output_file}")

        cached = move_to_cache(file_path)
        print(f"Moved original to: {cached}")

    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace")
        print(f"Error processing {file_path}:\n{err}")

print("Done.")

# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# Requires the ffmpeg CLI (e.g. `brew install ffmpeg`)

from pathlib import Path
import shutil
import subprocess

source_path = Path.home() / "Desktop"
downloads_path = Path.home() / "Downloads"

cache_path = downloads_path / "cache"
cache_path.mkdir(exist_ok=True)


def move_to_cache(path: Path) -> Path:
    """Move a file into cache/ without overwriting an existing file."""
    dest = cache_path / path.name
    counter = 2
    while dest.exists():
        dest = cache_path / f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    shutil.move(str(path), dest)
    return dest


for file_path in source_path.glob("*.mov"):
    output_file = downloads_path / file_path.with_suffix(".mp4").name

    try:
        # Convert the video to .mp4 format
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-vcodec", "libx264",
                "-acodec", "aac",
                "-preset", "medium",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_file),
            ],
            check=True,
            capture_output=True,
        )
        print(f"Converted: {file_path} -> {output_file}")

        # Move the old .mov file into cache folder
        cached = move_to_cache(file_path)
        print(f"Moved original .mov to: {cached}")

    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace")
        print(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")

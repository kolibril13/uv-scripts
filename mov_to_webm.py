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
    output_file = downloads_path / file_path.with_suffix(".webm").name

    try:
        # Convert the video to .webm format
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-vcodec", "libvpx-vp9",
                "-crf", "32",
                "-b:v", "0",
                "-pix_fmt", "yuv420p",
                "-acodec", "libopus",
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

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


def move_to_cache(path: Path) -> Path:
    """Move a file into cache/ without overwriting an existing file."""
    dest = cache_path / path.name
    counter = 2
    while dest.exists():
        dest = cache_path / f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    shutil.move(str(path), dest)
    return dest


for file_path in downloads_path.glob("*.mp4"):
    # Skip outputs of previous runs.
    if file_path.stem.endswith("_web"):
        continue

    output_file = file_path.with_name(file_path.stem + "_web.mp4")

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-an",
                "-vcodec", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_file),
            ],
            check=True,
            capture_output=True,
        )
        print(f"Converted: {file_path} -> {output_file}")

        cached = move_to_cache(file_path)
        print(f"Moved original .mp4 to: {cached}")

    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace")
        print(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")

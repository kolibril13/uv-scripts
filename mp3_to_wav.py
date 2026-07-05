# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# Requires the ffmpeg CLI (e.g. `brew install ffmpeg`)

from pathlib import Path
import shutil
import subprocess

folder_path = Path.home() / "Downloads"
cache_path = folder_path / "cache"
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


# Convert MP3 files to WAV
for file_path in folder_path.glob("*.mp3"):
    output_file = file_path.with_suffix(".wav")

    try:
        # Convert to WAV (PCM 16-bit), keep original channels and sample rate
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-acodec", "pcm_s16le",
                str(output_file),
            ],
            check=True,
            capture_output=True,
        )
        print(f"Converted: {file_path} -> {output_file}")

        cached = move_to_cache(file_path)
        print(f"Moved original to: {cached}")

    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace")
        print(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")

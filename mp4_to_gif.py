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


FPS = 10
SCALE_W = 480 * 2

for file_path in source_path.glob("*.mp4"):
    out_gif = downloads_path / file_path.with_suffix(".gif").name
    palette_png = file_path.with_name(file_path.stem + "_palette.png")

    try:
        # 1) Generate palette (single PNG!)
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-vf", f"fps={FPS},scale={SCALE_W}:-1:flags=lanczos,palettegen=stats_mode=diff",
                "-frames:v", "1",
                "-update", "1",
                str(palette_png),
            ],
            check=True,
            capture_output=True,
        )

        # 2) Use palette to create GIF
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-i", str(palette_png),
                "-filter_complex",
                f"[0:v]fps={FPS},scale={SCALE_W}:-1:flags=lanczos[v];"
                "[v][1:v]paletteuse=dither=bayer:bayer_scale=5",
                "-loop", "0",
                str(out_gif),
            ],
            check=True,
            capture_output=True,
        )

        print(f"Converted: {file_path} -> {out_gif}")

        # Move original .mp4 into cache
        cached = move_to_cache(file_path)
        print(f"Moved original .mp4 to: {cached}")

    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace")
        print(f"Error converting {file_path}:\n{err}")
    finally:
        # Clean up the palette even when conversion fails
        palette_png.unlink(missing_ok=True)

print("Conversion complete.")

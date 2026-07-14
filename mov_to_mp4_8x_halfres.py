# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# Requires the ffmpeg CLI (e.g. `brew install ffmpeg`)

from pathlib import Path
import json
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
        # macOS screen recordings are variable frame rate (VFR). The robust
        # recipe is:
        #   1. Probe avg_frame_rate (NOT r_frame_rate, which is usually the
        #      timebase like 600/1 and will blow up the fps filter).
        #   2. Normalize VFR -> CFR first by resampling at the real fps.
        #   3. Then apply setpts=0.125*PTS on the clean CFR stream.
        # Output frame rate is implicitly 8 * src_fps, which keeps every
        # frame and avoids stalls/duplicated frames during "quiet" regions.
        probe = json.loads(
            subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=avg_frame_rate,r_frame_rate",
                    "-of", "json",
                    str(file_path),
                ],
                check=True,
                capture_output=True,
            ).stdout
        )
        video_stream = probe["streams"][0]
        rate_str = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "60/1"
        num, den = rate_str.split("/")
        num, den = float(num), float(den)
        src_fps = num / den if den and num else 60.0
        # Clamp to a sane range in case probing returns something weird.
        src_fps = max(15.0, min(src_fps, 120.0))

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                # VFR -> CFR, then half resolution (even dims required by
                # yuv420p), then 8x speed.
                "-vf", f"fps={src_fps},scale=trunc(iw/4)*2:trunc(ih/4)*2,setpts=0.125*PTS",
                "-an",
                "-vcodec", "libx264",
                "-preset", "medium",
                "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                str(output_file),
            ],
            check=True,
            capture_output=True,
        )
        print(f"Converted: {file_path} -> {output_file} (src {src_fps:.2f} fps, half res, 8x speed)")

        # Move the old .mov file into cache folder
        cached = move_to_cache(file_path)
        print(f"Moved original .mov to: {cached}")

    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace")
        print(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")

# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# Requires the ffmpeg CLI (e.g. `brew install ffmpeg`)
#
# Speed up a single .mov by 2x and place the result (still a .mov) in Downloads.
#
# Usage:
#   uv run mov_2x_single_mov.py recording.mov      # a file on the Desktop
#   uv run mov_2x_single_mov.py ~/Movies/clip.mov  # or any path

from pathlib import Path
import json
import shutil
import subprocess
import sys

desktop_path = Path.home() / "Desktop"
downloads_path = Path.home() / "Downloads"

cache_path = downloads_path / "cache"
cache_path.mkdir(exist_ok=True)


def resolve_source(arg: str) -> Path:
    """Resolve the argument to a .mov, looking on the Desktop for bare names."""
    candidate = Path(arg).expanduser()
    if not candidate.is_absolute() and not candidate.exists():
        candidate = desktop_path / arg
    return candidate


def move_to_cache(path: Path) -> Path:
    """Move a file into cache/ without overwriting an existing file."""
    dest = cache_path / path.name
    counter = 2
    while dest.exists():
        dest = cache_path / f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    shutil.move(str(path), dest)
    return dest


if len(sys.argv) != 2:
    sys.exit("Usage: uv run mov_2x_single_mov.py <file.mov>")

file_path = resolve_source(sys.argv[1])
if not file_path.exists():
    sys.exit(f"File not found: {file_path}")
if file_path.suffix.lower() != ".mov":
    sys.exit(f"Not a .mov file: {file_path}")

# Output keeps the .mov container. Suffix with _2x so it doesn't clash with the
# original name when both briefly live under the same tree.
output_file = downloads_path / f"{file_path.stem}_2x.mov"

try:
    # macOS screen recordings are variable frame rate (VFR): they peak at the
    # capture rate (r_frame_rate, e.g. 60) but drop frames during static
    # regions, so avg_frame_rate comes out lower (e.g. 44). The old recipe
    # resampled to a CFR *before* the speed-up, which silently discarded real
    # frames during busy regions (fps=avg drops them; even fps=peak followed by
    # default CFR muxing re-decimates back down) -> the jerky "dropped frames"
    # look.
    #
    # The fix: don't resample at all. setpts=0.5*PTS just halves every frame's
    # timestamp (2x speed), and -fps_mode passthrough hands each source frame
    # to the encoder untouched -- no dropping, no duplicating. The result is a
    # VFR .mov that keeps 100% of the original frames, played back twice as
    # fast. (ffprobe still reports r_frame_rate as the peak, e.g. 60, but the
    # true frame count is preserved.)
    probe = json.loads(
        subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=avg_frame_rate,r_frame_rate,nb_read_frames",
                "-count_frames",
                "-of", "json",
                str(file_path),
            ],
            check=True,
            capture_output=True,
        ).stdout
    )
    video_stream = probe["streams"][0]
    src_frames = video_stream.get("nb_read_frames", "?")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(file_path),
            "-vf", "setpts=0.5*PTS",   # 2x speed: halve every timestamp
            "-fps_mode", "passthrough",  # keep every source frame, no re-timing
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
    print(f"Converted: {file_path} -> {output_file} ({src_frames} frames preserved, 2x speed)")

    # Move the old .mov file into cache folder
    cached = move_to_cache(file_path)
    print(f"Moved original .mov to: {cached}")

except subprocess.CalledProcessError as e:
    err = e.stderr.decode("utf-8", errors="replace")
    sys.exit(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")

# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

# Requires the ffmpeg CLI (e.g. `brew install ffmpeg`)

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def resolve_input_video(downloads: Path, filename: str | None) -> Path:
    if filename:
        video_path = downloads / filename
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        if video_path.suffix.lower() != ".mp4":
            raise ValueError(f"Expected an .mp4 file, got: {video_path.name}")
        return video_path

    mp4_files = sorted(downloads.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not mp4_files:
        raise FileNotFoundError("No .mp4 files found in Downloads.")
    return mp4_files[0]


def create_output_dir(downloads: Path, video_path: Path) -> Path:
    base_name = f"{video_path.stem}_frames"
    out_dir = downloads / base_name

    if not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=False)
        return out_dir

    idx = 2
    while True:
        candidate = downloads / f"{base_name}_{idx}"
        if not candidate.exists():
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate
        idx += 1


def extract_frames(video_path: Path, out_dir: Path) -> None:
    pattern = str(out_dir / "frame_%06d.png")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-start_number", "1", pattern],
        check=True,
        capture_output=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract frames from an MP4 in Downloads into a subfolder."
    )
    parser.add_argument(
        "filename",
        nargs="?",
        help="MP4 filename in Downloads (example: clip.mp4). Defaults to newest .mp4.",
    )
    args = parser.parse_args()

    downloads = Path.home() / "Downloads"
    if not downloads.exists():
        raise FileNotFoundError(f"Downloads folder not found: {downloads}")

    try:
        video_path = resolve_input_video(downloads, args.filename)
        out_dir = create_output_dir(downloads, video_path)
        extract_frames(video_path, out_dir)
        print(f"Extracted frames from {video_path.name} -> {out_dir}")
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.decode("utf-8", errors="replace")
        print(f"ffmpeg error while processing video:\n{details}")
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()

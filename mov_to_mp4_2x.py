# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ffmpeg-python",
# ]
# ///

# header generated with
# uv add --script script.py ffmpeg-python

from pathlib import Path
import ffmpeg
import shutil

source_path = Path.home() / "Desktop"
downloads_path = Path.home() / "Downloads"

cache_path = downloads_path / "cache"
cache_path.mkdir(exist_ok=True)

for file_path in source_path.glob("*.mov"):
    output_file = downloads_path / file_path.with_suffix(".mp4").name

    try:
        # macOS screen recordings are variable frame rate (VFR). The robust
        # recipe is:
        #   1. Probe avg_frame_rate (NOT r_frame_rate, which is usually the
        #      timebase like 600/1 and will blow up the fps filter).
        #   2. Normalize VFR -> CFR first by resampling at the real fps.
        #   3. Then apply setpts=0.5*PTS on the clean CFR stream.
        # Output frame rate is implicitly 2 * src_fps, which keeps every
        # frame and avoids stalls/duplicated frames during "quiet" regions.
        probe = ffmpeg.probe(str(file_path))
        video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        rate_str = video_stream.get('avg_frame_rate') or video_stream.get('r_frame_rate') or '60/1'
        num, den = rate_str.split('/')
        num, den = float(num), float(den)
        src_fps = num / den if den and num else 60.0
        # Clamp to a sane range in case probing returns something weird.
        src_fps = max(15.0, min(src_fps, 120.0))

        stream = ffmpeg.input(str(file_path))
        video = (
            stream.video
            .filter('fps', fps=src_fps)          # VFR -> CFR
            .filter('setpts', '0.5*PTS')         # 2x speed
        )

        ffmpeg.output(
            video,
            str(output_file),
            vcodec='libx264',
            preset='medium',
            crf=20,
            pix_fmt='yuv420p',
            movflags='+faststart',
            an=None,
        ).overwrite_output().run()
        print(f"Converted: {file_path} -> {output_file} (src {src_fps:.2f} fps)")

        # Move the old .mov file into cache folder
        shutil.move(str(file_path), cache_path / file_path.name)
        print(f"Moved original .mov to: {cache_path / file_path.name}")

    except ffmpeg.Error as e:
        print(f"Error converting {file_path}: {e}")

print("Conversion complete.")
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ffmpeg-python",
# ]
# ///

from pathlib import Path
import ffmpeg
import shutil

folder_path = Path.home() / "Downloads"
cache_path = folder_path / "cache"
cache_path.mkdir(exist_ok=True)

# .m4a and .mp4a are typical extensions for AAC in MP4
for ext in ("*.m4a", "*.mp4a"):
    for file_path in folder_path.glob(ext):
        output_file = file_path.with_suffix(".wav")

        try:
            # Convert to WAV (PCM 16-bit), keep original channels and sample rate
            ffmpeg.input(str(file_path)).output(
                str(output_file),
                acodec="pcm_s16le",
            ).overwrite_output().run()
            print(f"Converted: {file_path} -> {output_file}")

            shutil.move(str(file_path), cache_path / file_path.name)
            print(f"Moved original to: {cache_path / file_path.name}")

        except ffmpeg.Error as e:
            err = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
            print(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")

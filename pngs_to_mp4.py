# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ffmpeg-python",
# ]
# ///

# header generated with
# uv add --script script.py ffmpeg-python

from pathlib import Path
import shutil
import ffmpeg

# Find the latest created folder IN THE CACHE FOLDER in Downloads
downloads_path = Path.home() / "Downloads"
cache_path = downloads_path / "cache"
cache_path.mkdir(exist_ok=True)

# Find all subfolders in the cache folder
dirs = [d for d in cache_path.iterdir() if d.is_dir()]
if not dirs:
    raise RuntimeError("No folders found in cache.")
latest_folder = max(dirs, key=lambda d: d.stat().st_ctime)

# Output video filename (in Downloads)
output_video = downloads_path / "output_video.mp4"

try:
    # List all PNG files in the latest folder inside cache and get the last frame
    png_files = sorted(latest_folder.glob("*.png"))
    if not png_files:
        raise ValueError("No PNG files found in the latest cache folder.")

    last_frame = png_files[-1]

    # Create temporary copies of the last frame to extend its duration
    temp_frames_folder = latest_folder / "temp_frames"
    temp_frames_folder.mkdir(exist_ok=True)

    for frame in png_files:
        shutil.copy(frame, temp_frames_folder / frame.name)  # Copy all original frames to temp

    for i in range(48):  # Add 48 copies of the last frame
        temp_frame_name = f"last_frame_copy_{i:02d}.png"
        shutil.copy(last_frame, temp_frames_folder / temp_frame_name)

    # Create the video using the temp folder
    input_pattern = str(temp_frames_folder / "*.png")
    ffmpeg.input(input_pattern, pattern_type="glob", framerate=24) \
        .output(str(output_video), c="libx264", pix_fmt="yuv420p") \
        .overwrite_output() \
        .run(capture_stdout=True, capture_stderr=True)

    print(f"Video created successfully: {output_video}")

    # Clean up temporary frames
    shutil.rmtree(temp_frames_folder)

    # Move original PNG images to the main cache folder (not strictly necessary, but follows original pattern)
    # for frame in png_files:
    #     shutil.move(str(frame), cache_path / frame.name)

    # print(f"All original PNG images moved to: {cache_path}")

except ffmpeg.Error as e:
    print(f"An error occurred during conversion: {e.stderr.decode()}")
except Exception as e:
    print(f"An error occurred: {e}")

print("Process complete.")
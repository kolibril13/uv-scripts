# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "ffmpeg-python",
# ]
# ///

from pathlib import Path
import shutil
import ffmpeg

# Specify the folder containing the PNG images
folder_path = Path.home() / "Downloads"  # Adjust path if necessary
old_raw_path = folder_path / "old_raw"
old_raw_path.mkdir(exist_ok=True)

# Output video filename
output_video = folder_path / "output_video.mp4"

try:
    # List all PNG files in the folder and get the last frame
    png_files = sorted(folder_path.glob("*.png"))
    if not png_files:
        raise ValueError("No PNG files found in the folder.")

    last_frame = png_files[-1]

    # Create temporary copies of the last frame to extend its duration
    temp_frames_folder = folder_path / "temp_frames"
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

    # Move original PNG images to old_raw folder
    for frame in png_files:
        shutil.move(str(frame), old_raw_path / frame.name)

    print(f"All original PNG images moved to: {old_raw_path}")

except ffmpeg.Error as e:
    print(f"An error occurred during conversion: {e.stderr.decode()}")
except Exception as e:
    print(f"An error occurred: {e}")

print("Process complete.")
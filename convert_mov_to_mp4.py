# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ffmpeg-python",
# ]
# ///

# header generated with
# uv add --script convert_mov_to_mp4.py ffmpeg-python
from pathlib import Path
import ffmpeg

# Specify the folder containing the videos
folder_path = Path.home() / "Desktop"  # Adjust path if necessary

# Loop through all .mov files in the folder
for file_path in folder_path.glob("*.mov"):
    output_file = file_path.with_suffix(".mp4")  # Change the file extension to .mp4

    try:
        # Convert the video to .mp4 format
        ffmpeg.input(str(file_path)).output(str(output_file), vcodec='libx264', acodec='aac').run()
        print(f"Converted: {file_path} -> {output_file}")
    except ffmpeg.Error as e:
        print(f"Error converting {file_path}: {e}")

print("Conversion complete.")
# /// script
# requires-python = ">=3.11"
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
        # Load the input file
        stream = ffmpeg.input(str(file_path))
        # Apply the video filter to speed up the video (setpts=0.5*PTS doubles the playback speed)
        video = stream.video.filter('setpts', '0.5*PTS')
        
        # Convert to .mp4 with the specified video codec; disable audio with `an=None`
        ffmpeg.output(video, str(output_file), vcodec='libx264', an=None).run()
        print(f"Converted: {file_path} -> {output_file}")
    except ffmpeg.Error as e:
        print(f"Error converting {file_path}: {e}")

print("Conversion complete.")
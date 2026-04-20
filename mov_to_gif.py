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

FPS = 10
SCALE_W = 480*2

for file_path in source_path.glob("*.mov"):
    out_gif = downloads_path / file_path.with_suffix(".gif").name
    palette_png = file_path.with_name(file_path.stem + "_palette.png")

    try:
        # 1) Generate palette (single PNG!)
        inp = ffmpeg.input(str(file_path))
        pal_stream = (
            inp.video
            .filter("fps", fps=FPS)
            .filter("scale", SCALE_W, -1, flags="lanczos")
            .filter("palettegen", stats_mode="diff")
        )

        (
            ffmpeg
            .output(pal_stream, str(palette_png), vframes=1, update=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        # 2) Use palette to create GIF
        inp2 = ffmpeg.input(str(file_path))
        pal_in = ffmpeg.input(str(palette_png))

        vid = (
            inp2.video
            .filter("fps", fps=FPS)
            .filter("scale", SCALE_W, -1, flags="lanczos")
        )

        gif = ffmpeg.filter([vid, pal_in], "paletteuse", dither="bayer", bayer_scale=5)

        (
            ffmpeg
            .output(gif, str(out_gif), loop=0)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        print(f"Converted: {file_path} -> {out_gif}")

        # Move original .mov into cache
        shutil.move(str(file_path), cache_path / file_path.name)
        print(f"Moved original .mov to: {cache_path / file_path.name}")

        # Optional: keep or delete the palette
        palette_png.unlink(missing_ok=True)

    except ffmpeg.Error as e:
        err = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
        print(f"Error converting {file_path}:\n{err}")

print("Conversion complete.")
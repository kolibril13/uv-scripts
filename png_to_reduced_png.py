# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow",
# ]
# ///

print("Reducing PNG images in Downloads to under 2 MB...")
from pathlib import Path
from PIL import Image

downloads = Path.home() / "Downloads"

# Use the same cache folder as other scripts
cache = downloads / "cache"
cache.mkdir(exist_ok=True)

TARGET_SIZE = 2 * 1024 * 1024  # 2 MB in bytes


def move_to_cache(path: Path) -> Path:
    """Move a file into cache/ without overwriting an existing file."""
    dest = cache / path.name
    counter = 2
    while dest.exists():
        dest = cache / f"{path.stem}_{counter}{path.suffix}"
        counter += 1
    path.rename(dest)
    return dest


for png in downloads.glob("*.png"):
    # Skip outputs of previous runs.
    if png.stem.endswith("_reduced"):
        continue

    reduced = png.with_stem(png.stem + "_reduced")
    original_size = png.stat().st_size

    # Skip if already under target size
    if original_size < TARGET_SIZE:
        print(f"  {png.name} is already {original_size / 1024 / 1024:.2f} MB - skipping")
        continue

    print(f"  {png.name}: {original_size / 1024 / 1024:.2f} MB → reducing...")

    img = Image.open(png).convert("RGBA")
    width, height = img.size
    temp_path = png.parent / ".temp_png"

    # Quantizing to a 256-color palette shrinks PNGs far more than downscaling
    # alone; downscale on top of that only if still over the target.
    while True:
        temp_img = img if (width, height) == img.size else img.resize(
            (width, height), Image.Resampling.LANCZOS
        )
        temp_img.quantize(256, method=Image.Quantize.FASTOCTREE).save(
            temp_path, "PNG", optimize=True
        )

        file_size = temp_path.stat().st_size

        if file_size < TARGET_SIZE:
            # Found a good size, save to final location
            temp_path.rename(reduced)
            print(f"    ✓ Reduced to {file_size / 1024 / 1024:.2f} MB")
            break

        # Clean up temp file
        temp_path.unlink()

        # Reduce dimensions (scale down by 10%)
        width = int(width * 0.9)
        height = int(height * 0.9)

        # If we've scaled too much, stop
        if width < 100 or height < 100:
            print("    ! Could not reduce below 2 MB (minimum dimensions reached)")
            break

    # Move original PNG to cache
    move_to_cache(png)

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

for png in downloads.glob("*.png"):
    reduced = png.with_stem(png.stem + "_reduced")
    img = Image.open(png)
    original_size = png.stat().st_size

    # Skip if already under target size
    if original_size < TARGET_SIZE:
        print(f"  {png.name} is already {original_size / 1024 / 1024:.2f} MB - skipping")
        continue

    print(f"  {png.name}: {original_size / 1024 / 1024:.2f} MB → reducing...")

    # Start with original dimensions and quality
    width, height = img.size
    quality = 95

    # Iteratively reduce resolution and quality until under target size
    while True:
        # Create a temporary file to check size
        temp_img = img.resize((width, height), Image.Resampling.LANCZOS)

        # Save with current quality to temp location to check size
        temp_path = png.parent / ".temp_png"
        temp_img.save(temp_path, "PNG", optimize=True)

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
            print(f"    ! Could not reduce below 2 MB (minimum dimensions reached)")
            break

    # Move original PNG to cache
    png.rename(cache / png.name)

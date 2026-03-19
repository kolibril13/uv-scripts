#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow",
#     "pyobjc-framework-Cocoa",
# ]
# ///

"""Read an image from the macOS clipboard; save WebP + JPEG under ./tmp/ (same stem).

WebP keeps alpha (no white matte) and uses high quality; optional lossless:
``CLIPBOARD_WEBP_LOSSLESS=1``.

Output directory is ``Path.cwd() / "tmp"``. Run from the project root so temps land in that repo.
"""

import os
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

if sys.platform != "darwin":
    print("clipboard_to_webp.py only runs on macOS.", file=sys.stderr)
    sys.exit(1)

from AppKit import NSPasteboard  # noqa: E402
from PIL import Image  # noqa: E402

# Preferred order: try WebP/JPEG first, then other raster types.
_CLIPBOARD_IMAGE_UTIS = (
    "public.webp",
    "public.jpeg",
    "public.png",
    "public.tiff",
    "com.compuserve.gif",
)

# WebP: higher quality + full alpha quality reduce "washed out" lossy color.
# Set CLIPBOARD_WEBP_LOSSLESS=1 for mathematically lossless WebP (larger files).
_WEBP_QUALITY = 95
_WEBP_METHOD = 6
_WEBP_ALPHA_QUALITY = 100

# JPEG: tools that read images (e.g. IDE preview); slightly higher quality for text/UI.
_JPEG_QUALITY = 90


def _clipboard_image_bytes() -> tuple[bytes, str]:
    pb = NSPasteboard.generalPasteboard()
    if pb is None:
        print("Could not access the macOS pasteboard.", file=sys.stderr)
        sys.exit(1)
    for uti in _CLIPBOARD_IMAGE_UTIS:
        data = pb.dataForType_(uti)
        if data is not None and len(data) > 0:
            return bytes(data), uti
    return b"", ""


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode in ("RGBA", "LA", "PA"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.getchannel("A"))
        return bg
    return img.convert("RGB")


def _prepare_for_webp(img: Image.Image) -> Image.Image:
    """Keep alpha for WebP (no white matte); JPEG path still uses _to_rgb."""
    if img.mode in ("RGBA", "LA", "PA"):
        return img.convert("RGBA")
    if img.mode == "P":
        if "transparency" in img.info:
            return img.convert("RGBA")
        return img.convert("RGB")
    if img.mode in ("RGB", "L"):
        return img.convert("RGB")
    return img.convert("RGB")


def main() -> None:
    raw, uti = _clipboard_image_bytes()
    if not raw:
        print(
            "No image found on the clipboard (copy an image first).",
            file=sys.stderr,
        )
        sys.exit(1)

    out_dir = Path.cwd() / "tmp"
    out_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%H:%M:%S")
    out_webp = out_dir / f"{stamp}.webp"
    out_jpeg = out_dir / f"{stamp}.jpg"

    img = Image.open(BytesIO(raw))
    webp_img = _prepare_for_webp(img)
    jpeg_img = _to_rgb(img)

    webp_kwargs: dict = {
        "method": _WEBP_METHOD,
    }
    if os.environ.get("CLIPBOARD_WEBP_LOSSLESS", "").strip() in ("1", "true", "yes"):
        webp_kwargs["lossless"] = True
    else:
        webp_kwargs["quality"] = _WEBP_QUALITY
        if webp_img.mode == "RGBA":
            webp_kwargs["alpha_quality"] = _WEBP_ALPHA_QUALITY

    icc = img.info.get("icc_profile")
    if icc:
        webp_kwargs["icc_profile"] = icc

    webp_img.save(out_webp, "WEBP", **webp_kwargs)
    jpeg_img.save(out_jpeg, "JPEG", quality=_JPEG_QUALITY, optimize=True)

    print(f"Saved clipboard image ({uti}) to:")
    print(f"  WebP: {out_webp}")
    print(f"  JPEG: {out_jpeg}")
    print(f"SAVED_PATH_WEBP={out_webp}")
    print(f"SAVED_PATH_JPEG={out_jpeg}")
    # Alias for flows that expect a single "asset" path (the WebP).
    print(f"SAVED_PATH={out_webp}")


if __name__ == "__main__":
    main()

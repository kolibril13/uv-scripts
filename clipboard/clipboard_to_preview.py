#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pillow",
#     "pyobjc-framework-Cocoa",
# ]
# ///

"""Read an image from the macOS clipboard, save it to ~/Downloads, and reveal it in Finder.

Dragging from Preview.app or Quick Look only passes image data, which some apps
(e.g. DaVinci Resolve) won't accept as media. A Finder window drags the actual
file, so revealing it there is the reliable way to drag-and-drop into Resolve.
"""

import subprocess
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

if sys.platform != "darwin":
    print("clipboard_to_preview.py only runs on macOS.", file=sys.stderr)
    sys.exit(1)

from AppKit import NSPasteboard  # noqa: E402
from PIL import Image  # noqa: E402

_CLIPBOARD_IMAGE_UTIS = (
    "public.png",
    "public.jpeg",
    "public.tiff",
    "public.webp",
    "com.compuserve.gif",
)


def _clipboard_image_bytes() -> tuple[bytes, str]:
    pasteboard = NSPasteboard.generalPasteboard()
    if pasteboard is None:
        print("Could not access the macOS pasteboard.", file=sys.stderr)
        sys.exit(1)

    for uti in _CLIPBOARD_IMAGE_UTIS:
        data = pasteboard.dataForType_(uti)
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


def main() -> None:
    raw, uti = _clipboard_image_bytes()
    if not raw:
        print("No image found on the clipboard (copy an image first).", file=sys.stderr)
        sys.exit(1)

    downloads = Path.home() / "Downloads"
    downloads.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    out_path = downloads / f"clipboard-{stamp}.png"

    img = Image.open(BytesIO(raw))
    if img.mode in ("RGBA", "LA", "PA"):
        img = img.convert("RGBA")
    elif img.mode in ("RGB", "L"):
        img = img.convert("RGB")
    else:
        img = _to_rgb(img)

    img.save(out_path, "PNG")

    print(f"Saved clipboard image ({uti}) to: {out_path}")
    print(f"SAVED_PATH={out_path}")

    subprocess.run(["open", "-R", str(out_path)], check=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "numpy",
#     "pillow",
#     "pyobjc-framework-Cocoa",
#     "scipy",
# ]
# ///

"""Read an image from the macOS clipboard, remove its background, copy it back as RGBA PNG.

The background colour is estimated from the image border, then removed with a
matting pass rather than a flat colour key:

1. Sample a border band, take the median colour, refine it with the pixels close
   to that median. Perceptual distance is CIE76 in Lab, so near-white on white or
   subtle gradients behave sensibly.
2. Derive soft alpha by ratio matting - each pixel's distance from the background
   is measured against the strongest foreground next to it - so anti-aliased type
   and hairlines keep their partial coverage instead of turning into a hard cut.
3. Only clear background regions that are connected to the border, so same-coloured
   areas *inside* the subject (a white eye, a hole in a logo) survive.
4. Un-mix the background out of the semi-transparent edge pixels, which removes the
   colour halo a plain colour key leaves behind.

Tunables (all optional env vars):
  CLIPBOARD_BG_TOLERANCE   deltaE fully-background threshold (default 8)
  CLIPBOARD_BG_SOFTNESS    deltaE at which a pixel counts as foreground (default 26)
  CLIPBOARD_BG_COLOR       force the background colour, e.g. "#ffffff"
  CLIPBOARD_BG_EVERYWHERE  1 to also clear background-coloured areas the subject encloses
  CLIPBOARD_BG_TRIM        1 to crop the result to the remaining content
"""

import os
import sys
from io import BytesIO

import numpy as np

if sys.platform != "darwin":
    print("clipboard_to_transparent.py only runs on macOS.", file=sys.stderr)
    sys.exit(1)

from AppKit import NSData, NSPasteboard  # noqa: E402
from PIL import Image  # noqa: E402
from scipy import ndimage  # noqa: E402

_CLIPBOARD_IMAGE_UTIS = (
    "public.png",
    "public.tiff",
    "public.jpeg",
    "public.webp",
    "com.compuserve.gif",
)

# deltaE below _TOLERANCE is pure background. _SOFTNESS is the smallest contrast
# treated as real foreground, and the floor for the matting reference, so a subject
# barely distinct from the background does not dissolve. Suits screenshots and flat art.
_TOLERANCE = 8.0
_SOFTNESS = 26.0

# deltaE window used when refining the border median into the background colour.
_BORDER_REFINE = 10.0

# Pixel radius of the edge band that gets partial alpha instead of a hard cut.
_MATTE_RADIUS = 2


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print(f"Ignoring {name}={raw!r} (not a number).", file=sys.stderr)
        return default


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


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


def _write_clipboard_png(png: bytes) -> None:
    pasteboard = NSPasteboard.generalPasteboard()
    pasteboard.declareTypes_owner_(["public.png"], None)
    data = NSData.dataWithBytes_length_(png, len(png))
    if not pasteboard.setData_forType_(data, "public.png"):
        print("Could not write the image back to the pasteboard.", file=sys.stderr)
        sys.exit(1)


# sRGB (D65) -> XYZ, and the D65 white point.
_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ],
    dtype=np.float32,
)
_D65 = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)


def _to_lab(rgb: np.ndarray) -> np.ndarray:
    """sRGB (float 0-255) -> CIE L*a*b*: L 0-100, a/b roughly -128..127.

    Done by hand rather than via ``Image.convert("LAB")``: Pillow packs a/b into
    signed bytes that wrap, so two near-identical colours straddling a=0 come out
    255 apart.
    """
    srgb = np.clip(rgb, 0.0, 255.0) / 255.0
    linear = np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)
    xyz = linear @ _RGB_TO_XYZ.T / _D65

    eps = 216.0 / 24389.0
    kappa = 24389.0 / 27.0
    f = np.where(xyz > eps, np.cbrt(xyz), (kappa * xyz + 16.0) / 116.0)

    return np.stack(
        [
            116.0 * f[..., 1] - 16.0,
            500.0 * (f[..., 0] - f[..., 1]),
            200.0 * (f[..., 1] - f[..., 2]),
        ],
        axis=-1,
    ).astype(np.float32)


def _delta_e(lab: np.ndarray, ref: np.ndarray) -> np.ndarray:
    return np.sqrt(np.sum((lab - ref) ** 2, axis=-1))


def _parse_color(raw: str) -> tuple[int, int, int] | None:
    text = raw.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(c * 2 for c in text)
    if len(text) != 6:
        return None
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError:
        return None


def _estimate_background(
    rgb: np.ndarray, lab: np.ndarray, opaque: np.ndarray
) -> tuple[np.ndarray, float]:
    """Return the border background colour (RGB float) and how uniform the border is."""
    height, width = opaque.shape
    band = max(2, min(height, width) // 60)

    border = np.zeros((height, width), dtype=bool)
    border[:band, :] = True
    border[-band:, :] = True
    border[:, :band] = True
    border[:, -band:] = True
    border &= opaque

    if not border.any():
        # Fully transparent border: fall back to the whole image.
        border = opaque.copy()
    if not border.any():
        return np.array([255.0, 255.0, 255.0], dtype=np.float32), 0.0

    lab_border = lab[border]
    median = np.median(lab_border, axis=0)
    close = _delta_e(lab_border, median) < _BORDER_REFINE
    uniformity = float(close.mean())
    if not close.any():
        close = np.ones(len(lab_border), dtype=bool)

    # float64 accumulator: a float32 mean over a million border pixels drifts by a
    # whole level, which then biases the distance map and the edge un-mixing.
    return (
        rgb[border][close].mean(axis=0, dtype=np.float64).astype(np.float32),
        uniformity,
    )


def main() -> None:
    raw, uti = _clipboard_image_bytes()
    if not raw:
        print("No image found on the clipboard (copy an image first).", file=sys.stderr)
        sys.exit(1)

    tolerance = _env_float("CLIPBOARD_BG_TOLERANCE", _TOLERANCE)
    softness = max(_env_float("CLIPBOARD_BG_SOFTNESS", _SOFTNESS), tolerance + 0.5)

    img = Image.open(BytesIO(raw)).convert("RGBA")
    rgba = np.asarray(img, dtype=np.float32)
    rgb = rgba[..., :3]
    alpha_in = rgba[..., 3] / 255.0
    lab = _to_lab(rgb)
    opaque = alpha_in > 0.5

    forced = os.environ.get("CLIPBOARD_BG_COLOR", "").strip()
    if forced:
        parsed = _parse_color(forced)
        if parsed is None:
            print(f"Could not parse CLIPBOARD_BG_COLOR={forced!r}.", file=sys.stderr)
            sys.exit(1)
        bg_rgb = np.array(parsed, dtype=np.float32)
        uniformity = 1.0
    else:
        bg_rgb, uniformity = _estimate_background(rgb, lab, opaque)

    bg_lab = _to_lab(bg_rgb.reshape(1, 1, 3))[0, 0]
    distance = _delta_e(lab, bg_lab)

    # Candidate background: close enough in colour, or already transparent.
    candidate = (distance < softness) | ~opaque

    if _env_flag("CLIPBOARD_BG_EVERYWHERE"):
        background = candidate
    else:
        # Keep only the candidate blobs touching the border; interior look-alikes stay.
        labels, count = ndimage.label(candidate, structure=np.ones((3, 3), dtype=int))
        if count:
            edge_labels = np.unique(
                np.concatenate(
                    [labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]]
                )
            )
            edge_labels = edge_labels[edge_labels != 0]
            background = np.isin(labels, edge_labels)
        else:
            background = np.zeros_like(candidate)

    # Ratio matting: measure each pixel against the strongest foreground nearby
    # instead of a fixed distance, so an edge pixel that is half background gets
    # roughly half alpha whatever the subject's contrast against the background is.
    reference = np.maximum(
        ndimage.maximum_filter(distance, size=2 * _MATTE_RADIUS + 1), softness
    )
    ramp = np.clip(
        (distance - tolerance) / np.maximum(reference - tolerance, 1e-3), 0.0, 1.0
    )

    # Anti-aliased pixels sit just outside the connected background, too far in
    # colour to be candidates. Grow the region by the matting radius so the ramp
    # reaches them; confident foreground already ramps to 1, so this is safe.
    soft = ndimage.binary_dilation(
        background, structure=np.ones((3, 3), dtype=bool), iterations=_MATTE_RADIUS
    )
    alpha = alpha_in * np.where(soft, ramp, 1.0)

    # Un-mix the background out of the edge pixels so no colour halo is left.
    partial = soft & (alpha > 0.003) & (alpha < 0.997)
    out_rgb = rgb.copy()
    if partial.any():
        a = alpha[partial][:, None]
        out_rgb[partial] = np.clip((rgb[partial] - (1.0 - a) * bg_rgb) / a, 0.0, 255.0)

    out = np.dstack([out_rgb, alpha * 255.0]).round().astype(np.uint8)
    result = Image.fromarray(out, "RGBA")

    if _env_flag("CLIPBOARD_BG_TRIM"):
        bbox = result.getbbox()
        if bbox:
            result = result.crop(bbox)

    buf = BytesIO()
    result.save(buf, "PNG")
    _write_clipboard_png(buf.getvalue())

    removed = float((alpha < 0.5).mean()) - float((alpha_in < 0.5).mean())
    hex_color = "#%02x%02x%02x" % tuple(int(round(c)) for c in bg_rgb)
    print(f"Clipboard image: {img.width}x{img.height} ({uti})")
    print(f"Background colour: {hex_color} (border uniformity {uniformity:.0%})")
    print(
        f"Removed {removed:.1%} of the pixels; {result.width}x{result.height} copied back."
    )

    if uniformity < 0.6:
        print(
            "Border is not a flat colour, so the result may be rough. "
            "Try CLIPBOARD_BG_COLOR=#rrggbb or a larger CLIPBOARD_BG_SOFTNESS.",
            file=sys.stderr,
        )
    if removed > 0.97:
        print(
            "Nearly everything was removed - the subject probably matches the "
            "background. Try a smaller CLIPBOARD_BG_TOLERANCE.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()

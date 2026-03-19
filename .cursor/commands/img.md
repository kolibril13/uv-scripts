# /img

Save the **macOS clipboard** image as **WebP + JPEG** in **`<workspace-root>/tmp/`** (same timestamp stem), then **read the JPEG** for context, pick a **short descriptive filename**, and **copy the WebP** to the root of that same workspace.

**Speed / ordering:** Do not read workspace files, plan, or use the clipboard for anything else until clipboard capture is done. The clipboard can change at any moment—the capture command must be the **first** action.

**This repo (`uv-scripts`) is the tooling root** for all projects. Scripts are in `clipboard/`. **Part 1 and Part 2 both use `cd "<workspace-root>"`** so `./tmp/` and the final `.webp` are in the **open project**.

## Part 1 — save from clipboard

1. **Immediately**, before anything else:
   ```bash
   cd "<workspace-root>" && uv run "$HOME/projects/uv-scripts/clipboard/clipboard_to_webp.py"
   ```
   The **open project’s root** replaces `"<workspace-root>"`. (If the open workspace **is** uv-scripts and cwd is the repo root, `uv run ./clipboard/clipboard_to_webp.py` is equivalent after `cd`.)
2. If this fails, stop and report the error.

3. Parse paths from the output (under **`tmp/`**):
   - **WebP (for repo / embed):** `SAVED_PATH_WEBP=...` (or `SAVED_PATH=...`, same value).
   - **JPEG (for reading / analysis):** `SAVED_PATH_JPEG=...`.

## Part 2 — understand, name, copy project WebP

4. **Open/read the JPEG** at `SAVED_PATH_JPEG` (image-capable read) and briefly note what is visible (UI, text, subject).
5. Choose a **new base name** (stem only, no extension):
   - Lowercase **kebab-case**, ASCII `a-z`, `0-9`, hyphens only.
   - **3–6 words** worth of meaning, e.g. `blender-geometry-nodes-graph`.
   - Avoid generic names like `screenshot` or `image` unless nothing else fits.
6. Copy the WebP from **`tmp/`** into the **project root** (still with cwd at workspace root):
   ```bash
   cd "<workspace-root>" && uv run "$HOME/projects/uv-scripts/clipboard/image_to_workspace.py" "<absolute-path-from-SAVED_PATH_WEBP>" "<descriptive-stem>"
   ```
   Quote paths with spaces.
7. Report:
   - One-line summary of what the image shows.
   - Final file path under that project root (from `Copied to:`).

## Notes

- **macOS only** for clipboard capture (`clipboard_to_webp.py`: Pillow + PyObjC).
- **WebP:** quality **84**, method **6** (embed). **JPEG:** quality **90**, `optimize=True` (preview/read).
- **`tmp/`** is gitignored in `uv-scripts`; add `tmp/` to **`.gitignore`** in other projects if you don’t want clipboard temps committed.
- Pairs in **`~/.cursor/commands/img.md`** should match this file so `/img` works from **any** workspace.

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# brew install asmvik/formulae/skhd
# skhd --start-service
# python3 /Users/jan-hendrik/projects/uv-scripts/clipboard/setup_shortcut_skhd.py


"""Install/update a skhd hotkey for saving clipboard images to Downloads."""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_PATH = Path("/Users/jan-hendrik/projects/uv-scripts/clipboard/clipboard_to_downloads.py")
DEFAULT_UV_BIN = Path("/opt/homebrew/bin/uv")
BEGIN_MARKER = "# >>> uv-scripts clipboard_to_downloads >>>"
END_MARKER = "# <<< uv-scripts clipboard_to_downloads <<<"


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def validate_requirements(uv_bin: Path) -> None:
    if not SCRIPT_PATH.is_file():
        fail(f"Script not found: {SCRIPT_PATH}")

    if not uv_bin.is_file() or not os.access(uv_bin, os.X_OK):
        fail(
            f"uv binary not found or not executable: {uv_bin}\n"
            "Set UV_BIN to your uv path and run again."
        )

    if not shutil.which("skhd"):
        fail("skhd is not installed or not on PATH.\nInstall with: brew install asmvik/formulae/skhd")


def rewrite_config(skhd_config: Path, uv_bin: Path) -> Path:
    skhd_config.parent.mkdir(parents=True, exist_ok=True)
    skhd_config.touch(exist_ok=True)

    backup = skhd_config.with_name(f"{skhd_config.name}.bak.{datetime.now():%Y%m%d-%H%M%S}")
    shutil.copy2(skhd_config, backup)

    out: list[str] = []
    skip = False
    for line in skhd_config.read_text(encoding="utf-8").splitlines():
        if line == BEGIN_MARKER:
            skip = True
            continue
        if line == END_MARKER:
            skip = False
            continue
        if not skip:
            out.append(line)

    cleaned = "\n".join(out).rstrip()
    block = "\n".join(
        [
            BEGIN_MARKER,
            '# Cmd+Shift+2 -> save clipboard image to ~/Downloads (" on many layouts)',
            f"cmd + shift - 2 : /bin/bash -lc '{uv_bin} run {SCRIPT_PATH}'",
            END_MARKER,
        ]
    )
    skhd_config.write_text(f"{cleaned}\n\n{block}\n" if cleaned else f"{block}\n", encoding="utf-8")
    return backup


def reload_skhd() -> None:
    is_running = subprocess.run(
        ["pgrep", "-x", "skhd"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0

    if is_running:
        reload_result = subprocess.run(["skhd", "--reload"], check=False)
        if reload_result.returncode != 0:
            subprocess.run(["skhd", "--restart-service"], check=False)
        return

    subprocess.run(["skhd", "--start-service"], check=False)


def main() -> None:
    skhd_config = Path(os.environ.get("SKHD_CONFIG", str(Path.home() / ".skhdrc"))).expanduser().resolve()
    uv_bin = Path(os.environ.get("UV_BIN", str(DEFAULT_UV_BIN))).expanduser().resolve()

    validate_requirements(uv_bin)
    backup = rewrite_config(skhd_config, uv_bin)
    reload_skhd()

    print("Updated skhd config:")
    print(f"  {skhd_config}")
    print("Backup created:")
    print(f"  {backup}")
    print()
    print("Hotkey installed:")
    print('  Cmd+Shift+2 -> run clipboard_to_downloads.py')
    print()
    print("If this is your first skhd setup:")
    print("  1) Grant Accessibility permission to skhd in System Settings")
    print("  2) Disable Secure Keyboard Entry in your terminal app")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///

# brew install asmvik/formulae/skhd
# skhd --start-service
# python3 /Users/jan-hendrik/projects/uv-scripts/shortcuts/setup_shortcut_skhd.py


"""Install/update skhd hotkeys for uv-scripts."""

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path("/Users/jan-hendrik/projects/uv-scripts")
DEFAULT_UV_BIN = Path("/opt/homebrew/bin/uv")
BEGIN_MARKER = "# >>> uv-scripts shortcuts >>>"
END_MARKER = "# <<< uv-scripts shortcuts <<<"


@dataclass(frozen=True)
class Binding:
    # skhd hotkey syntax, e.g. "cmd + shift - 2"
    hotkey: str
    # human-readable label, e.g. "Cmd+Shift+2"
    label: str
    # path to the target script
    script: Path
    # one-line comment describing the binding
    description: str


BINDINGS: list[Binding] = [
    Binding(
        hotkey="cmd + shift - 2",
        label="Cmd+Shift+2",
        script=REPO_ROOT / "clipboard" / "clipboard_to_downloads.py",
        description='save clipboard image to ~/Downloads (" on many layouts)',
    ),
    Binding(
        hotkey="cmd + shift - 1",
        label="Cmd+Shift+1",
        script=REPO_ROOT / "shortcuts" / "hello_world.py",
        description="print hello world",
    ),
]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def validate_requirements(uv_bin: Path) -> None:
    for b in BINDINGS:
        if not b.script.is_file():
            fail(f"Script not found: {b.script}")

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

    # Strip any previous managed block, plus the legacy marker names.
    legacy_markers = [
        ("# >>> uv-scripts clipboard_to_downloads >>>", "# <<< uv-scripts clipboard_to_downloads <<<"),
        (BEGIN_MARKER, END_MARKER),
    ]

    out: list[str] = []
    skip = False
    for line in skhd_config.read_text(encoding="utf-8").splitlines():
        if any(line == begin for begin, _ in legacy_markers):
            skip = True
            continue
        if any(line == end for _, end in legacy_markers):
            skip = False
            continue
        if not skip:
            out.append(line)

    cleaned = "\n".join(out).rstrip()

    block_lines: list[str] = [BEGIN_MARKER]
    for b in BINDINGS:
        block_lines.append(f"# {b.label} -> {b.description}")
        block_lines.append(f"{b.hotkey} : /bin/bash -lc '{uv_bin} run {b.script}'")
    block_lines.append(END_MARKER)
    block = "\n".join(block_lines)

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
    print("Hotkeys installed:")
    for b in BINDINGS:
        print(f"  {b.label} -> {b.script.name} ({b.description})")
    print()
    print("If this is your first skhd setup:")
    print("  1) Grant Accessibility permission to skhd in System Settings")
    print("  2) Disable Secure Keyboard Entry in your terminal app")


if __name__ == "__main__":
    main()

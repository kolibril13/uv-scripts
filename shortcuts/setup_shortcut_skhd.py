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
    # one-line comment describing the binding
    description: str
    # path to a uv-run script; mutually exclusive with `command`
    script: Path | None = None
    # raw shell command to run; mutually exclusive with `script`
    command: str | None = None

    def __post_init__(self) -> None:
        if (self.script is None) == (self.command is None):
            raise ValueError(
                f"Binding {self.label!r} must set exactly one of `script` or `command`."
            )

    def shell_command(self, uv_bin: Path) -> str:
        if self.script is not None:
            return f"{uv_bin} run {self.script}"
        assert self.command is not None
        return self.command

    def target_label(self) -> str:
        return self.script.name if self.script is not None else (self.command or "")


BINDINGS: list[Binding] = [
    Binding(
        hotkey="cmd + shift - 2",
        label="Cmd+Shift+2",
        script=REPO_ROOT / "clipboard" / "clipboard_to_preview.py",
        description='open clipboard image in Preview (" on many layouts)',
    ),
    Binding(
        hotkey="cmd + shift - 1",
        label="Cmd+Shift+1",
        command=(
            "open '/Users/jan-hendrik/projects/tauri-tldraw-annotate"
            "/src-tauri/target/release/bundle/macos/curate-draw.app'"
        ),
        description="launch (or focus) the curate-draw screenshot annotator",
    ),
]


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def validate_requirements(uv_bin: Path) -> None:
    needs_uv = False
    for b in BINDINGS:
        if b.script is not None:
            if not b.script.is_file():
                fail(f"Script not found: {b.script}")
            needs_uv = True

    if needs_uv and (not uv_bin.is_file() or not os.access(uv_bin, os.X_OK)):
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
        # Single-quote the command so spaces/flags are preserved; any embedded
        # single quotes are escaped using the standard '"'"' idiom.
        escaped = b.shell_command(uv_bin).replace("'", "'\"'\"'")
        block_lines.append(f"{b.hotkey} : /bin/bash -lc '{escaped}'")
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
    uv_bin = Path(os.environ.get("UV_BIN", str(DEFAULT_UV_BIN))).expanduser()

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
        print(f"  {b.label} -> {b.target_label()} ({b.description})")
    print()
    print("If this is your first skhd setup:")
    print("  1) Grant Accessibility permission to skhd in System Settings")
    print("  2) Disable Secure Keyboard Entry in your terminal app")


if __name__ == "__main__":
    main()

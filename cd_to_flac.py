# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "musicbrainzngs",
# ]
# ///

# Imports the audio CD currently in the drive as tagged FLAC files
# (lossless) into the music library, organized as Artist Name/Album Name/.
#
# macOS mounts an audio CD under /Volumes as AIFF track files plus a hidden
# .TOC.plist with the disc's table of contents. From that TOC we compute the
# MusicBrainz disc ID and look up artist, album and track titles, then convert
# each AIFF to FLAC with ffmpeg.
#
# Requires the ffmpeg CLI (e.g. `brew install ffmpeg`)

import base64
import hashlib
import plistlib
import re
import socket
import subprocess
from pathlib import Path

import musicbrainzngs

# Without this, a stalled connection to MusicBrainz/Cover Art Archive hangs forever.
socket.setdefaulttimeout(15)

library_path = (
    Path.home()
    / "Library/Mobile Documents/com~apple~CloudDocs/00_personal/Balfolk Musik"
)


def sanitize(name: str) -> str:
    """Make a string safe to use as a file or folder name."""
    return re.sub(r"[/:]", "-", name).strip().rstrip(".")


# --- Find the mounted audio CD ---
cd_volumes = [p for p in Path("/Volumes").iterdir() if (p / ".TOC.plist").exists()]
if not cd_volumes:
    raise SystemExit("No audio CD found in /Volumes. Insert a CD and wait for it to mount.")
cd_volume = cd_volumes[0]

track_files = sorted(
    (f for f in cd_volume.iterdir() if f.suffix.lower() in (".aiff", ".aif", ".aifc")),
    key=lambda f: int(re.match(r"\d+", f.name).group()),
)
print(f"Found audio CD at {cd_volume} with {len(track_files)} tracks")

# --- Compute the MusicBrainz disc ID from the TOC ---
# https://musicbrainz.org/doc/Disc_ID_Calculation
toc = plistlib.loads((cd_volume / ".TOC.plist").read_bytes())
sessions = toc["Sessions"]
audio_tracks = [t for t in sessions[0]["Track Array"] if not t.get("Data")]
offsets = {t["Point"]: t["Start Block"] + 150 for t in audio_tracks}

if len(sessions) > 1:
    # Enhanced CD: MusicBrainz defines the lead-out as the start of the
    # data session minus 11400 sectors.
    leadout = sessions[1]["Track Array"][0]["Start Block"] - 11400 + 150
else:
    leadout = sessions[0]["Leadout Block"] + 150

first_track = audio_tracks[0]["Point"]
last_track = audio_tracks[-1]["Point"]

sha = hashlib.sha1()
sha.update(f"{first_track:02X}".encode())
sha.update(f"{last_track:02X}".encode())
sha.update(f"{leadout:08X}".encode())
for point in range(1, 100):
    sha.update(f"{offsets.get(point, 0):08X}".encode())
disc_id = base64.b64encode(sha.digest(), altchars=b"._").decode().replace("=", "-")

# TOC string allows MusicBrainz to fuzzy-match if the exact disc ID is unknown
toc_string = f"{first_track} {last_track} {leadout} " + " ".join(
    str(offsets[t["Point"]]) for t in audio_tracks
)
print(f"MusicBrainz disc ID: {disc_id}")

# --- Look up the release on MusicBrainz ---
musicbrainzngs.set_useragent("uv-cd-import", "0.1", "jan-hendrik.mueller@gmx.net")
try:
    result = musicbrainzngs.get_releases_by_discid(
        disc_id, toc=toc_string, includes=["artists", "recordings"]
    )
except musicbrainzngs.ResponseError:
    result = {}

releases = result.get("disc", {}).get("release-list") or result.get("release-list") or []

release = None
disc_position = 1
disc_total = 1

if releases:
    if len(releases) > 1:
        print("Multiple matching releases found:")
        for i, r in enumerate(releases, 1):
            details = ", ".join(
                filter(None, [r.get("date"), r.get("country"), r.get("disambiguation")])
            )
            print(f"  {i}. {r['artist-credit-phrase']} - {r['title']} ({details})")
        choice = input(f"Which release? [1-{len(releases)}, default 1]: ").strip()
        release = releases[int(choice) - 1 if choice else 0]
    else:
        release = releases[0]

    artist = release["artist-credit-phrase"]
    album = release["title"]
    date = release.get("date", "")

    # Pick the medium (disc) of this release that matches our disc
    media = release["medium-list"]
    medium = next(
        (m for m in media if any(d.get("id") == disc_id for d in m.get("disc-list", []))),
        None,
    ) or next(
        (m for m in media if len(m["track-list"]) == len(track_files)), media[0]
    )
    disc_position = int(medium.get("position", 1))
    disc_total = len(media)

    tracks = sorted(medium["track-list"], key=lambda t: int(t["position"]))
    titles = [t.get("title") or t["recording"]["title"] for t in tracks]
else:
    print("Disc not found on MusicBrainz - falling back to manual entry.")
    artist = input("Artist name: ").strip()
    album = input("Album name: ").strip()
    date = input("Year (optional): ").strip()
    titles = [f"Track {i:02d}" for i in range(1, len(track_files) + 1)]

print(f"\nImporting: {artist} - {album}" + (f" ({date})" if date else ""))

album_dir = library_path / sanitize(artist) / sanitize(album)
album_dir.mkdir(parents=True, exist_ok=True)

# --- Rip each track to FLAC ---
for file_path in track_files:
    number = int(re.match(r"\d+", file_path.name).group())
    title = titles[number - 1] if number <= len(titles) else f"Track {number:02d}"

    file_name = f"{number:02d} {sanitize(title)}.flac"
    if disc_total > 1:
        file_name = f"{disc_position}-{file_name}"
    output_file = album_dir / file_name

    if output_file.exists():
        print(f"  Skipping (already exists): {output_file.name}")
        continue

    print(f"  Ripping track {number}: {title} ...")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(file_path),
                "-map", "0:a",
                "-c:a", "flac",
                "-compression_level", "8",
                "-metadata", f"title={title}",
                "-metadata", f"artist={artist}",
                "-metadata", f"album_artist={artist}",
                "-metadata", f"album={album}",
                "-metadata", f"track={number}/{len(titles)}",
                "-metadata", f"disc={disc_position}/{disc_total}",
                *(["-metadata", f"date={date}"] if date else []),
                str(output_file),
            ],
            check=True,
            capture_output=True,
        )
        print(f"    -> {output_file}")
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode("utf-8", errors="replace")
        print(f"Error ripping {file_path}:\n{err}")

# --- Cover art (best effort) ---
if release is not None and not (album_dir / "cover.jpg").exists():
    try:
        image = musicbrainzngs.get_image_front(release["id"], size="1200")
        (album_dir / "cover.jpg").write_bytes(image)
        print("Saved cover.jpg")
    except Exception:
        print("No cover art found on the Cover Art Archive.")

subprocess.run(["drutil", "eject"], check=False)
print(f"\nDone. Album imported to: {album_dir}")

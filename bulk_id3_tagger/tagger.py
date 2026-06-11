"""Read a tagging template JSON and write ID3 tags + artwork to each file."""

import json
import os
import re

from mutagen.id3 import ID3, ID3NoHeaderError, APIC, TIT2, TPE1, TALB, TCON, TDRC, TRCK
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

_ARTWORK_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

_FOUR_DIGIT_YEAR = re.compile(r"^\d{4}$")


class TaggerError(Exception):
    pass


def _load_id3(path):
    """Load (or create) an ID3 tag block for an MP3 or WAV file."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".mp3":
        audio = MP3(path)
    elif ext == ".wav":
        audio = WAVE(path)
    else:
        raise TaggerError(f"Unsupported file type: {path}")

    if audio.tags is None:
        audio.add_tags()
    return audio


def _resolve(track, defaults, field):
    return track.get(field) or defaults.get(field) or ""


def _resolve_artwork(track, defaults, base_dir, track_label):
    """Resolve the artwork path for a track, raising loudly if it is missing."""
    raw = track.get("artwork") or defaults.get("artwork") or ""
    if not raw:
        return ""
    path = raw if os.path.isabs(raw) else os.path.join(base_dir, raw)
    if not os.path.isfile(path):
        raise TaggerError(
            f"Artwork file not found for track '{track_label}': {path}"
        )
    return path


def _embed_artwork(tags, artwork_path):
    if not artwork_path:
        return
    if not os.path.isfile(artwork_path):
        raise TaggerError(f"Artwork file not found: {artwork_path}")

    ext = os.path.splitext(artwork_path)[1].lower()
    mime = _ARTWORK_MIME.get(ext)
    if mime is None:
        raise TaggerError(f"Unsupported artwork format: {artwork_path}")

    with open(artwork_path, "rb") as f:
        image_data = f.read()

    tags.delall("APIC")
    tags.add(APIC(
        encoding=3,       # UTF-8
        mime=mime,
        type=3,           # front cover
        desc="Cover",
        data=image_data,
    ))


def tag_file(path, title="", artist="", album="", genre="", year="",
             track_number=None, artwork=""):
    """Write the given metadata + artwork into an audio file's ID3 tags."""
    audio = _load_id3(path)
    tags = audio.tags

    if title:
        tags.delall("TIT2")
        tags.add(TIT2(encoding=3, text=title))
    if artist:
        tags.delall("TPE1")
        tags.add(TPE1(encoding=3, text=artist))
    if album:
        tags.delall("TALB")
        tags.add(TALB(encoding=3, text=album))
    if genre:
        tags.delall("TCON")
        tags.add(TCON(encoding=3, text=genre))
    if year:
        tags.delall("TDRC")
        tags.add(TDRC(encoding=3, text=str(year)))
    if track_number:
        tags.delall("TRCK")
        tags.add(TRCK(encoding=3, text=str(track_number)))

    _embed_artwork(tags, artwork)

    audio.save()


def validate_template(template, base_dir):
    """Validate the entire template before tagging begins.

    Checks every track (and the defaults block) for:
    - track_number: must be numeric or empty/null
    - year: must be a 4-digit number or empty/null
    - artwork: if specified, the resolved path must exist on disk

    Returns a list of human-readable error strings.  An empty list means the
    template is valid.
    """
    defaults = template.get("defaults", {})
    tracks = template.get("tracks", [])
    errors = []

    # Validate defaults-level year
    default_year = defaults.get("year") or ""
    if default_year and not _FOUR_DIGIT_YEAR.match(str(default_year)):
        errors.append(f"defaults.year '{default_year}' is not a 4-digit number")

    # Validate defaults-level artwork
    default_artwork = defaults.get("artwork") or ""
    if default_artwork:
        artwork_path = (
            default_artwork
            if os.path.isabs(default_artwork)
            else os.path.join(base_dir, default_artwork)
        )
        if not os.path.isfile(artwork_path):
            errors.append(
                f"defaults.artwork path does not exist: {artwork_path}"
            )

    for idx, track in enumerate(tracks):
        label = track.get("file") or f"track[{idx}]"

        # track_number
        tn = track.get("track_number")
        if tn is not None and tn != "":
            try:
                int(tn)
            except (TypeError, ValueError):
                errors.append(
                    f"{label}: track_number '{tn}' is not numeric"
                )

        # year (per-track override)
        year = track.get("year") or ""
        if year and not _FOUR_DIGIT_YEAR.match(str(year)):
            errors.append(
                f"{label}: year '{year}' is not a 4-digit number"
            )

        # artwork (per-track override only; defaults already checked above)
        artwork_raw = track.get("artwork") or ""
        if artwork_raw:
            artwork_path = (
                artwork_raw
                if os.path.isabs(artwork_raw)
                else os.path.join(base_dir, artwork_raw)
            )
            if not os.path.isfile(artwork_path):
                errors.append(
                    f"{label}: artwork path does not exist: {artwork_path}"
                )

    return errors


def apply_template(json_path, base_dir=None, dry_run=False):
    """Tag every file listed in a template JSON. Returns (tagged, errors).

    When dry_run=True, prints what would be written for each track without
    actually modifying any files.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    defaults = template.get("defaults", {})
    tracks = template.get("tracks", [])
    base_dir = base_dir or os.path.dirname(os.path.abspath(json_path))

    # --- Pre-run validation ---
    validation_errors = validate_template(template, base_dir)
    if validation_errors:
        msg_lines = ["Validation failed — fix these errors before tagging:"]
        for err in validation_errors:
            msg_lines.append(f"  - {err}")
        raise TaggerError("\n".join(msg_lines))

    total = len(tracks)
    tagged = []
    errors = []

    for idx, track in enumerate(tracks, start=1):
        filename = track.get("file")
        if not filename:
            errors.append((track, "Track entry has no \"file\" field"))
            continue

        path = os.path.join(base_dir, filename)
        if not os.path.isfile(path):
            errors.append((filename, f"File not found: {path}"))
            continue

        # Resolve artwork loudly — will raise TaggerError on bad path
        try:
            artwork = _resolve_artwork(track, defaults, base_dir, filename)
        except TaggerError as exc:
            errors.append((filename, str(exc)))
            continue

        title = _resolve(track, defaults, "title")
        artist = _resolve(track, defaults, "artist")
        album = _resolve(track, defaults, "album")
        genre = _resolve(track, defaults, "genre")
        year = _resolve(track, defaults, "year")
        track_number = track.get("track_number")

        if dry_run:
            print(f"[{idx}/{total}] Would tag: {filename}")
            print(f"         title:        {title or '(not set)'}")
            print(f"         artist:       {artist or '(not set)'}")
            print(f"         album:        {album or '(not set)'}")
            print(f"         year:         {year or '(not set)'}")
            print(f"         track_number: {track_number if track_number is not None else '(not set)'}")
            print(f"         artwork:      {artwork or '(not set)'}")
            tagged.append(filename)
            continue

        print(f"[{idx}/{total}] Tagging: {filename}")

        try:
            tag_file(
                path,
                title=title,
                artist=artist,
                album=album,
                genre=genre,
                year=year,
                track_number=track_number,
                artwork=artwork,
            )
            tagged.append(filename)
        except (TaggerError, ID3NoHeaderError, OSError) as exc:
            errors.append((filename, str(exc)))

    return tagged, errors

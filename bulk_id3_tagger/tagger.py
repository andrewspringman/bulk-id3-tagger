"""Read a tagging template JSON and write ID3 tags + artwork to each file."""

import json
import os

from mutagen.id3 import ID3, ID3NoHeaderError, APIC, TIT2, TPE1, TALB, TCON, TDRC, TRCK
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

_ARTWORK_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


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


def apply_template(json_path, base_dir=None):
    """Tag every file listed in a template JSON. Returns (tagged, errors)."""
    with open(json_path, "r", encoding="utf-8") as f:
        template = json.load(f)

    defaults = template.get("defaults", {})
    tracks = template.get("tracks", [])
    base_dir = base_dir or os.path.dirname(os.path.abspath(json_path))

    tagged = []
    errors = []

    for track in tracks:
        filename = track.get("file")
        if not filename:
            errors.append((track, "Track entry has no \"file\" field"))
            continue

        path = os.path.join(base_dir, filename)
        if not os.path.isfile(path):
            errors.append((filename, f"File not found: {path}"))
            continue

        artwork = _resolve(track, defaults, "artwork")
        if artwork and not os.path.isabs(artwork):
            artwork = os.path.join(base_dir, artwork)

        try:
            tag_file(
                path,
                title=_resolve(track, defaults, "title"),
                artist=_resolve(track, defaults, "artist"),
                album=_resolve(track, defaults, "album"),
                genre=_resolve(track, defaults, "genre"),
                year=_resolve(track, defaults, "year"),
                track_number=track.get("track_number"),
                artwork=artwork,
            )
            tagged.append(filename)
        except (TaggerError, ID3NoHeaderError, OSError) as exc:
            errors.append((filename, str(exc)))

    return tagged, errors

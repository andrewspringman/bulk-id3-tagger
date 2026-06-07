"""Scan a folder of audio files and produce a JSON tagging template."""

import json
import os
import re

AUDIO_EXTENSIONS = (".mp3", ".wav")

# suno-download names files "{title}_{song_id}.mp3" — strip the trailing
# "_<id>" so the guessed title matches what the artist actually called the song.
_SUNO_ID_SUFFIX = re.compile(r"_[A-Za-z0-9-]+$")


def _guess_title(filename):
    name = os.path.splitext(filename)[0]
    stripped = _SUNO_ID_SUFFIX.sub("", name)
    return stripped if stripped else name


def scan_folder(folder, album="", artist="", genre="", year="", artwork=""):
    """Build a tagging template dict for every audio file in `folder`.

    Top-level "defaults" apply to every track; each track entry can override
    any of them by editing the JSON before running the tagger.
    """
    files = sorted(
        f for f in os.listdir(folder)
        if f.lower().endswith(AUDIO_EXTENSIONS)
    )

    tracks = []
    for index, filename in enumerate(files, start=1):
        tracks.append({
            "file": filename,
            "title": _guess_title(filename),
            "track_number": index,
        })

    return {
        "defaults": {
            "artist": artist,
            "album": album,
            "genre": genre,
            "year": year,
            "artwork": artwork,
        },
        "tracks": tracks,
    }


def write_template(folder, output_path, **defaults):
    template = scan_folder(folder, **defaults)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    return template

# bulk-id3-tagger

Two small steps to get a folder of MP3/WAV files release-ready:

1. **`scan`** — walks a folder of audio files and writes a `tags_template.json`
   with a guessed title and track number for each file (plus a `defaults`
   block for things like artist, album, genre, year, and artwork).
2. **`tag`** — reads that JSON (after you've reviewed/edited it) and writes
   the title, artist, album, genre, year, track number, and cover artwork
   into each file's ID3 tags.

Built to prep batches of [Suno](https://suno.com) songs (downloaded with
[suno-download](https://github.com/andrewspringman/suno-download)) for
distribution through services like CD Baby and streaming platforms.

## Install

```bash
git clone https://github.com/andrewspringman/bulk-id3-tagger.git
cd bulk-id3-tagger
python3 -m venv venv && source venv/bin/activate
pip install -e .
```

## Usage

### 1. Generate a template

```bash
bulk-id3-tagger scan ~/Music/my-release \
  --artist "Your Name" \
  --album "Release Name" \
  --genre "Jazz" \
  --year "2026" \
  --artwork "cover.jpg"
```

This writes `~/Music/my-release/tags_template.json`:

```json
{
  "defaults": {
    "artist": "Your Name",
    "album": "Release Name",
    "genre": "Jazz",
    "year": "2026",
    "artwork": "cover.jpg"
  },
  "tracks": [
    {
      "file": "Some Song_abc123.mp3",
      "title": "Some Song",
      "track_number": 1
    }
  ]
}
```

Open the JSON and fix anything the scan guessed wrong — titles, track order,
or per-track overrides (any field in `defaults` can also be set on an
individual track to override it just for that file). `artwork` paths are
resolved relative to the folder the JSON lives in unless given as an
absolute path.

### 2. Apply the tags

```bash
bulk-id3-tagger tag ~/Music/my-release/tags_template.json
```

This writes ID3 tags (and embeds the cover art) directly into each audio
file listed in the template, and prints a summary of what succeeded and
what failed.

## Notes

- Supports `.mp3` and `.wav` files (ID3 tags via [mutagen](https://mutagen.readthedocs.io/)).
- Artwork must be `.jpg`/`.jpeg` or `.png`.
- Re-running `tag` is safe — it overwrites the relevant tag frames rather
  than duplicating them.

## License

MIT License — see [LICENSE](LICENSE).

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A two-step Python CLI for prepping batches of audio files (MP3/WAV) for
release: scan a folder to produce an editable JSON tagging template, then
apply that template to write ID3 tags and embedded cover artwork.

Built to unblock two music releases (French Gypsy Jazz, Lofi Hip-Hop) that
need ID3 tags + artwork before going to CD Baby. Source files come from
[suno-download](https://github.com/andrewspringman/suno-download), but the
source folder is intentionally configurable (`scan <folder>`) rather than
hardcoded — releases haven't been gathered into separate folders yet.

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -e .

# Step 1: scan a folder, write tags_template.json
bulk-id3-tagger scan <folder> [--artist ... --album ... --genre ... --year ... --artwork ...]

# Step 2: apply that template (after reviewing/editing it)
bulk-id3-tagger tag <folder>/tags_template.json
```

Equivalent without installing: `python -m bulk_id3_tagger scan ...` / `tag ...`

There is no test suite, linter, or build step configured.

## Architecture

Three modules wired together by a thin argparse CLI in `__main__.py`:

1. **`scanner.py`** — `scan_folder()` / `write_template()`. Lists `.mp3`/`.wav`
   files in a folder, guesses each track's title by stripping the trailing
   `_<suno-id>` suffix that suno-download appends to filenames, assigns
   sequential track numbers, and assembles a `{"defaults": {...}, "tracks": [...]}`
   dict that gets written out as JSON.
2. **`tagger.py`** — `apply_template()` reads that JSON, resolves each track's
   final field values (`track value or defaults value`), and calls `tag_file()`
   per track. `tag_file()` loads (or creates) the file's ID3 block via mutagen
   (`MP3` for `.mp3`, `WAVE` for `.wav`), replaces the relevant frames
   (`TIT2`/`TPE1`/`TALB`/`TCON`/`TDRC`/`TRCK`), and embeds cover art as an
   `APIC` frame (front-cover type, JPEG/PNG only). Returns `(tagged, errors)`
   so the CLI can report a clean summary without aborting on the first bad file.
3. **`__main__.py`** — `scan` and `tag` subcommands; `scan` accepts
   `--artist/--album/--genre/--year/--artwork` to pre-fill the `defaults` block.

### Template JSON shape

```json
{
  "defaults": {"artist": "", "album": "", "genre": "", "year": "", "artwork": ""},
  "tracks": [{"file": "Song_abc123.mp3", "title": "Song", "track_number": 1}]
}
```

Any field present on a track entry overrides the corresponding `defaults`
value for that track only (see `tagger._resolve()`). Artwork paths are
resolved relative to the template's own directory unless absolute.

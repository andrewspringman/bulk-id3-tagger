"""CLI for bulk-id3-tagger.

Two subcommands, matching the two-script plan:

  scan   <folder> [-o template.json]   — generate a JSON tagging template
  tag    <template.json>               — write ID3 tags + artwork from that JSON
"""

import argparse
import os
import sys

from . import scanner, tagger


def _cmd_scan(args):
    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print(f"Not a folder: {folder}", file=sys.stderr)
        return 1

    output = args.output or os.path.join(folder, "tags_template.json")
    template = scanner.write_template(
        folder,
        output,
        artist=args.artist,
        album=args.album,
        genre=args.genre,
        year=args.year,
        artwork=args.artwork,
    )

    track_count = len(template["tracks"])
    print(f"Found {track_count} audio file(s) in {folder}")
    print(f"Wrote template to {output}")
    print()
    print("Edit that file to fill in / correct titles, defaults, and the")
    print("artwork path, then run:")
    print(f"  bulk-id3-tagger tag {output}")
    return 0


def _cmd_tag(args):
    json_path = os.path.abspath(args.template)
    if not os.path.isfile(json_path):
        print(f"Not a file: {json_path}", file=sys.stderr)
        return 1

    base_dir = os.path.abspath(args.base_dir) if args.base_dir else None

    try:
        tagged, errors = tagger.apply_template(
            json_path, base_dir=base_dir, dry_run=args.dry_run
        )
    except tagger.TaggerError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"\nDry run complete — {len(tagged)} track(s) would be tagged.")
        if errors:
            print(f"{len(errors)} error(s) found:")
            for name, message in errors:
                print(f"  ✗ {name}: {message}")
            return 1
        return 0

    print(f"\nTagged {len(tagged)} file(s).")

    if errors:
        print(f"\n{len(errors)} error(s):")
        for name, message in errors:
            print(f"  ✗ {name}: {message}")
        return 1

    return 0


def build_parser():
    parser = argparse.ArgumentParser(prog="bulk-id3-tagger")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="generate a JSON tagging template from a folder")
    scan.add_argument("folder", help="folder containing .mp3/.wav files")
    scan.add_argument("-o", "--output", help="path to write the template JSON (default: <folder>/tags_template.json)")
    scan.add_argument("--artist", default="", help="default artist for every track")
    scan.add_argument("--album", default="", help="default album/release name for every track")
    scan.add_argument("--genre", default="", help="default genre for every track")
    scan.add_argument("--year", default="", help="default release year for every track")
    scan.add_argument("--artwork", default="", help="default artwork image path (.jpg/.png) for every track")
    scan.set_defaults(func=_cmd_scan)

    tag = subparsers.add_parser("tag", help="write ID3 tags + artwork from a template JSON")
    tag.add_argument("template", help="path to a tags_template.json produced by `scan`")
    tag.add_argument("--base-dir", help="folder the audio/artwork files live in (default: the template's own folder)")
    tag.add_argument("--dry-run", action="store_true",
                     help="print what would be tagged for each track without writing any files")
    tag.set_defaults(func=_cmd_tag)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

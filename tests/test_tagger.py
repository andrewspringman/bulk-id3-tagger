"""Tests for the tagger module."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from bulk_id3_tagger import tagger


class TestTaggerError(unittest.TestCase):
    """Test error handling in the tagger module."""

    def test_missing_artwork_file_error(self):
        """Error raised when artwork file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy MP3 file
            mp3_path = Path(tmpdir, "test.mp3")
            mp3_path.write_bytes(b"")

            # Try to embed non-existent artwork
            with self.assertRaises(tagger.TaggerError) as ctx:
                tagger._embed_artwork({}, "/nonexistent/image.jpg")

            self.assertIn("not found", str(ctx.exception).lower())

    def test_unsupported_artwork_format_error(self):
        """Error raised for unsupported artwork format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            artwork_path = Path(tmpdir, "image.bmp")
            artwork_path.write_bytes(b"")

            with self.assertRaises(tagger.TaggerError) as ctx:
                tagger._embed_artwork({}, str(artwork_path))

            self.assertIn("unsupported", str(ctx.exception).lower())


class TestApplyTemplate(unittest.TestCase):
    """Test template application functionality."""

    def test_apply_template_missing_file_error(self):
        """Error raised when template file doesn't exist."""
        with self.assertRaises(tagger.TaggerError) as ctx:
            tagger.apply_template("/nonexistent/template.json")

        self.assertIn("not found", str(ctx.exception).lower())

    def test_apply_template_invalid_json_error(self):
        """Error raised for invalid JSON template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir, "invalid.json")
            template_path.write_text("{invalid json")

            with self.assertRaises(tagger.TaggerError) as ctx:
                tagger.apply_template(str(template_path))

            self.assertIn("invalid", str(ctx.exception).lower())

    def test_apply_template_missing_audio_file(self):
        """Error reported for missing audio file in template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir, "template.json")
            template = {
                "defaults": {},
                "tracks": [
                    {"file": "nonexistent.mp3", "title": "Song"}
                ]
            }
            template_path.write_text(json.dumps(template))

            tagged, errors = tagger.apply_template(str(template_path))

            self.assertEqual(len(tagged), 0)
            self.assertEqual(len(errors), 1)
            self.assertIn("not found", errors[0][1].lower())

    def test_apply_template_missing_artwork_file(self):
        """Error reported for missing artwork file in template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy MP3 file
            mp3_path = Path(tmpdir, "song.mp3")
            mp3_path.write_bytes(b"")

            template_path = Path(tmpdir, "template.json")
            template = {
                "defaults": {"artwork": "/nonexistent/cover.jpg"},
                "tracks": [
                    {"file": "song.mp3", "title": "Song"}
                ]
            }
            template_path.write_text(json.dumps(template))

            tagged, errors = tagger.apply_template(str(template_path))

            self.assertEqual(len(tagged), 0)
            self.assertEqual(len(errors), 1)
            self.assertIn("artwork", errors[0][1].lower())

    def test_apply_template_dry_run_no_write(self):
        """Dry-run mode validates but doesn't write tags."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy MP3 file
            mp3_path = Path(tmpdir, "song.mp3")
            mp3_path.write_bytes(b"")

            template_path = Path(tmpdir, "template.json")
            template = {
                "defaults": {"artist": "Artist", "album": "Album"},
                "tracks": [
                    {"file": "song.mp3", "title": "Song"}
                ]
            }
            template_path.write_text(json.dumps(template))

            # Apply template in dry-run mode
            tagged, errors = tagger.apply_template(
                str(template_path),
                dry_run=True
            )

            # Should succeed without errors
            self.assertEqual(len(tagged), 1)
            self.assertEqual(len(errors), 0)

    def test_apply_template_track_missing_file_field(self):
        """Error reported when track entry lacks 'file' field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = Path(tmpdir, "template.json")
            template = {
                "defaults": {},
                "tracks": [
                    {"title": "Song"}  # Missing 'file' field
                ]
            }
            template_path.write_text(json.dumps(template))

            tagged, errors = tagger.apply_template(str(template_path))

            self.assertEqual(len(tagged), 0)
            self.assertEqual(len(errors), 1)
            self.assertIn("file", errors[0][1].lower())


class TestResolveField(unittest.TestCase):
    """Test field resolution from track and defaults."""

    def test_resolve_track_override(self):
        """Track field overrides default."""
        track = {"title": "Track Title"}
        defaults = {"title": "Default Title"}

        result = tagger._resolve(track, defaults, "title")

        self.assertEqual(result, "Track Title")

    def test_resolve_default_value(self):
        """Default used when track field missing."""
        track = {}
        defaults = {"title": "Default Title"}

        result = tagger._resolve(track, defaults, "title")

        self.assertEqual(result, "Default Title")

    def test_resolve_empty_string(self):
        """Empty string returned when both missing."""
        track = {}
        defaults = {}

        result = tagger._resolve(track, defaults, "title")

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()

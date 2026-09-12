"""Tests for the scanner module."""

import os
import tempfile
import unittest
from pathlib import Path

from bulk_id3_tagger import scanner


class TestGuessTitle(unittest.TestCase):
    """Test title guessing from filenames."""

    def test_guess_title_without_suno_suffix(self):
        """Guess title from filename without suno ID suffix."""
        self.assertEqual(scanner._guess_title("My Song.mp3"), "My Song")

    def test_guess_title_with_suno_suffix(self):
        """Strip suno ID suffix from filename."""
        self.assertEqual(
            scanner._guess_title("My Song_abc123.mp3"),
            "My Song"
        )

    def test_guess_title_with_uuid_suffix(self):
        """Strip UUID-style suno suffix."""
        self.assertEqual(
            scanner._guess_title("Beautiful Day_550e8400-e29b-41d4-a716-446655440000.mp3"),
            "Beautiful Day"
        )

    def test_guess_title_preserves_hyphens_in_title(self):
        """Keep hyphens within the actual title."""
        self.assertEqual(
            scanner._guess_title("My-Song_abc123.mp3"),
            "My-Song"
        )

    def test_guess_title_empty_after_strip(self):
        """When only suno suffix remains, return what's left after removing extension."""
        self.assertEqual(
            scanner._guess_title("_abc123.mp3"),
            "_abc123"
        )


class TestScanFolder(unittest.TestCase):
    """Test folder scanning functionality."""

    def test_scan_empty_folder(self):
        """Scanning empty folder produces empty track list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template = scanner.scan_folder(tmpdir)
            self.assertEqual(template["tracks"], [])

    def test_scan_folder_with_audio_files(self):
        """Folder with audio files produces correct tracks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy audio files
            Path(tmpdir, "Song_1.mp3").touch()
            Path(tmpdir, "Song_2.wav").touch()

            template = scanner.scan_folder(tmpdir)

            self.assertEqual(len(template["tracks"]), 2)
            self.assertEqual(template["tracks"][0]["file"], "Song_1.mp3")
            self.assertEqual(template["tracks"][0]["track_number"], 1)
            self.assertEqual(template["tracks"][1]["file"], "Song_2.wav")
            self.assertEqual(template["tracks"][1]["track_number"], 2)

    def test_scan_folder_ignores_non_audio_files(self):
        """Non-audio files are ignored during scan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "song.mp3").touch()
            Path(tmpdir, "image.jpg").touch()
            Path(tmpdir, "notes.txt").touch()

            template = scanner.scan_folder(tmpdir)

            self.assertEqual(len(template["tracks"]), 1)
            self.assertEqual(template["tracks"][0]["file"], "song.mp3")

    def test_scan_folder_default_metadata(self):
        """Default metadata is included in template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "song.mp3").touch()

            template = scanner.scan_folder(
                tmpdir,
                artist="Artist Name",
                album="Album Name",
                genre="Jazz",
                year="2026"
            )

            self.assertEqual(template["defaults"]["artist"], "Artist Name")
            self.assertEqual(template["defaults"]["album"], "Album Name")
            self.assertEqual(template["defaults"]["genre"], "Jazz")
            self.assertEqual(template["defaults"]["year"], "2026")


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from native.lichtspiel.model import (
    empty_project,
    load_project,
    preflight,
    queued_media,
    save_project,
)
from native.lichtspiel.player import display_args, test_pattern_path
from native.lichtspiel.window import MainWindow


class NativeModelTests(unittest.TestCase):
    def test_project_roundtrip_keeps_duplicate_cues_and_real_file_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            filename = directory / "short.mp4"
            filename.write_bytes(b"sample")
            project = empty_project()
            project["library"].append(
                {
                    "id": "film",
                    "name": "Short",
                    "path": str(filename),
                    "duration": 90,
                    "category": "Film",
                    "size": 6,
                }
            )
            project["queue"] = ["film", "film"]
            save_project(project, directory)
            restored = load_project(directory)
            self.assertEqual(restored["queue"], ["film", "film"])
            self.assertEqual(len(queued_media(restored)), 2)
            self.assertEqual(len(preflight(restored)), 2)
            filename.unlink()
            with self.assertRaisesRegex(ValueError, "fehlt"):
                preflight(restored)

    def test_preflight_rejects_invalid_duration_and_dangling_queue(self):
        with tempfile.TemporaryDirectory() as temporary:
            filename = Path(temporary) / "clip.mp4"
            filename.write_bytes(b"sample")
            project = empty_project()
            project["library"] = [
                {"id": "clip", "path": str(filename), "duration": float("nan")}
            ]
            project["queue"] = ["clip"]
            with self.assertRaisesRegex(ValueError, "Laufzeit"):
                preflight(project)
            project["queue"] = ["missing"]
            with self.assertRaisesRegex(ValueError, "fehlende Medieneinträge"):
                preflight(project)

    def test_projection_card_is_bundled_and_display_arguments_are_shared(self):
        self.assertTrue(Path(test_pattern_path()).is_file())
        self.assertEqual(display_args(2), ["--screen=2", "--fs-screen=2"])
        with self.assertRaisesRegex(ValueError, "Ausgabebildschirm"):
            display_args(-1)


class NativeWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_four_qt_pages_open_without_web_renderer(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            self.assertEqual(window.pages.count(), 4)
            self.assertEqual(window.pages.currentIndex(), 2)
            window.close()


if __name__ == "__main__":
    unittest.main()

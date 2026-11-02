import os
import tempfile
import unittest
from concurrent.futures import Future
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
from native.lichtspiel.widgets import ElidedLabel
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

    def test_live_controls_show_clip_and_show_progress(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.player.items = [
                {"name": "Trailer", "category": "Trailer", "duration": 30},
                {"name": "Hauptfilm", "category": "Film", "duration": 90},
            ]
            window._player_state(
                {"status": "playing", "index": 1, "position": 45, "duration": 90}
            )
            self.assertEqual(window.clip_progress.value(), 500)
            self.assertEqual(window.show_progress.value(), 625)
            self.assertIn("Hauptfilm", window.current_cue.text())
            self.assertIn("Noch 00:45", window.clip_remaining.text())
            window.player.state["status"] = "idle"
            window.close()

    def test_next_cue_stays_inside_live_card_at_minimum_width(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.resize(900, 640)
            window.show()
            window._set_page(0)
            self.app.processEvents()
            card = window.next_cue.parentWidget()
            self.assertLessEqual(
                window.next_cue.geometry().right(), card.contentsRect().right()
            )
            window.close()

    def test_light_network_error_does_not_open_modal_over_show_controls(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            with mock.patch("native.lichtspiel.window.QMessageBox.warning") as warning:
                failed = Future()
                failed.set_exception(RuntimeError("Verbindung unterbrochen"))
                window._queue_light_job(failed, lambda _result: None)
                window._poll_jobs()
                warning.assert_not_called()
            self.assertIn("Verbindung unterbrochen", window.status.text())
            window.close()

    def test_unsaved_light_target_is_not_used_for_read_only_connection_test(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.light_entity.setText("light.neue_lampe")
            with mock.patch.object(window.lighting.executor, "submit") as submit:
                window._test_lighting_connection()
                submit.assert_not_called()
            self.assertIn("zuerst", window.light_feedback.text())
            window.close()

    def test_long_media_title_stays_on_one_line(self):
        full = "Ein sehr langer Filmname mit vielen weiteren Wörtern"
        title = ElidedLabel(full)
        title.resize(110, 25)
        title.show()
        self.app.processEvents()
        self.assertTrue(title.text().endswith("…"))
        self.assertEqual(title.toolTip(), full)
        title.close()


if __name__ == "__main__":
    unittest.main()

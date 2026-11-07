import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from native.lichtspiel.journal import append_event, format_events, read_events
from native.lichtspiel.model import empty_project
from native.lichtspiel.window import MainWindow


class JournalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_log_keeps_order_and_ignores_broken_lines(self):
        with tempfile.TemporaryDirectory() as temporary:
            filename = Path(temporary) / "show-journal.jsonl"
            append_event(
                filename,
                {
                    "run": "one",
                    "kind": "start",
                    "text": "Vorstellung gestartet",
                    "path": "/private/movie.mp4",
                },
            )
            with filename.open("ab") as target:
                target.write(b"not-json\n")
            append_event(
                filename, {"run": "one", "kind": "end", "text": "Vorstellung beendet"}
            )
            entries = read_events(filename)
            self.assertEqual([entry["kind"] for entry in entries], ["start", "end"])
            self.assertNotIn("/private/movie.mp4", filename.read_text())
            self.assertIn("Vorstellung beendet", format_events(entries))

    def test_player_transitions_are_logged_once_and_visible_in_regie(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            project = empty_project()
            project["library"] = [
                {
                    "id": "a",
                    "name": "Werbung",
                    "path": "/private/spot.mp4",
                    "category": "Werbung",
                    "duration": 20,
                },
                {
                    "id": "b",
                    "name": "Film",
                    "path": "/private/film.mp4",
                    "category": "Film",
                    "duration": 90,
                },
            ]
            project["queue"] = ["a", "b"]
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project", return_value=project
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory", return_value=directory
                ),
                mock.patch.object(MainWindow, "_detect_mpv"),
            ):
                window = MainWindow()
                window.player.items = project["library"]
                for status, index, position in (
                    ("starting", 0, 0),
                    ("playing", 0, 0),
                    ("playing", 0, 4),
                    ("paused", 0, 4),
                    ("playing", 0, 4),
                    ("playing", 1, 0),
                    ("finished", 1, 90),
                ):
                    state = {
                        "status": status,
                        "index": index,
                        "position": position,
                        "duration": project["library"][index]["duration"],
                    }
                    window.player.state = state
                    window.player.state_changed.emit(state)
                window.recovery_executor.submit(lambda: None).result(timeout=2)
                entries = read_events(window.journal_path)
                self.assertEqual(
                    [entry["kind"] for entry in entries],
                    ["start", "cue", "state", "state", "state", "cue", "end"],
                )
                self.assertNotIn("/private/", window.journal_path.read_text())
                window._open_journal()
                window.recovery_executor.submit(lambda: None).result(timeout=2)
                window._poll_jobs()
                self.assertIn("Vorstellung beendet", window.journal_text.toPlainText())
                window.close()

    def test_terminal_updates_do_not_create_false_stop_or_empty_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            project = empty_project()
            project["library"] = [
                {"id": "a", "name": "Clip", "path": "/tmp/clip.mp4", "duration": 30}
            ]
            project["queue"] = ["a"]
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project", return_value=project
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory", return_value=directory
                ),
                mock.patch.object(MainWindow, "_detect_mpv"),
            ):
                window = MainWindow()
                window.player.items = project["library"]

                def emit(status, message=""):
                    state = {
                        "status": status,
                        "index": 0,
                        "position": 0,
                        "duration": 30,
                        "message": message,
                    }
                    window.player.state = state
                    window.player.state_changed.emit(state)

                emit("starting")
                emit("playing")
                emit("idle")  # mpv's final-clip path emits idle then finished.
                emit("finished")
                self.app.processEvents()
                emit("starting")
                emit("playing")
                emit("error")  # mpv sends the useful error text in the next update.
                emit("error", "Player antwortet nicht.")
                self.app.processEvents()
                window.recovery_executor.submit(lambda: None).result(timeout=2)
                text = format_events(read_events(window.journal_path))
                self.assertEqual(text.count("Vorstellung beendet."), 1)
                self.assertNotIn("Vorstellung gestoppt.", text)
                self.assertEqual(text.count("Playerfehler:"), 1)
                self.assertIn("Player antwortet nicht.", text)
                window.close()


if __name__ == "__main__":
    unittest.main()

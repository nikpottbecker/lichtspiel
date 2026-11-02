import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication

from native.lichtspiel.player import MpvPlayer

FAKE_MPV = """#!/usr/bin/env python3
import json
import socket
import sys

endpoint = next(a.split("=", 1)[1] for a in sys.argv if a.startswith("--input-ipc-server="))
server = socket.socket(socket.AF_UNIX)
server.bind(endpoint)
server.listen(1)
client, _ = server.accept()
with client, client.makefile("rb") as source:
    for line in source:
        message = json.loads(line)
        command = message["command"]
        if command[0] == "loadfile":
            client.sendall(b'{"event":"property-change","name":"duration","data":60}\\n')
            client.sendall(b'{"event":"file-loaded"}\\n')
        if command[0] == "screenshot-to-file":
            with open(command[1], "wb") as target:
                target.write(b'frame')
            response = {"request_id": message["request_id"], "error": "success"}
            client.sendall((json.dumps(response) + "\\n").encode())
        if command[0] == "quit":
            break
server.close()
"""


@unittest.skipIf(sys.platform == "win32", "Unix socket test fixture")
class MpvIpcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_until(self, condition, timeout=3):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if condition():
                return
            time.sleep(0.01)
        self.fail("Timed out waiting for the player state")

    def test_process_and_ipc_keep_controls_responsive(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary) / "fake-mpv"
            binary.write_text(FAKE_MPV, encoding="utf-8")
            binary.chmod(0o755)
            player = MpvPlayer()
            items = [
                {"path": "/tmp/first.mp4", "duration": 30},
                {"path": "/tmp/second.mp4", "duration": 40},
            ]
            player.start(str(binary), items, 0)
            self.wait_until(lambda: player.state["status"] == "playing")
            player.pause()
            self.assertEqual(player.state["status"], "paused")
            player.blackout()
            self.assertEqual(player.state["status"], "blackout")
            player.resume()
            self.assertEqual(player.state["status"], "playing")
            player.next()
            self.assertEqual(player.state["index"], 1)
            player.stop()
            self.wait_until(lambda: player.process.state() == QProcess.NotRunning)
            self.assertEqual(player.state["status"], "idle")

    def test_watchdog_reports_unresponsive_player(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary) / "fake-mpv"
            binary.write_text(FAKE_MPV, encoding="utf-8")
            binary.chmod(0o755)
            player = MpvPlayer()
            player.start(str(binary), [{"path": "/tmp/first.mp4", "duration": 30}], 0)
            self.wait_until(lambda: player.state["status"] == "playing")
            player.last_reply = time.monotonic() - 13
            player._watchdog_tick()
            self.assertEqual(player.state["status"], "error")
            self.assertIn("antwortet", player.state["message"])
            self.wait_until(lambda: player.process.state() == QProcess.NotRunning)

    def test_resume_loads_saved_clip_with_file_local_start(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary) / "fake-mpv"
            binary.write_text(FAKE_MPV, encoding="utf-8")
            binary.chmod(0o755)
            player = MpvPlayer()
            items = [
                {"path": "/tmp/spot.mp4", "duration": 30},
                {"path": "/tmp/film.mp4", "duration": 90},
            ]
            with mock.patch.object(
                player, "_command", wraps=player._command
            ) as command:
                player.start(str(binary), items, 0, start_index=1, start_position=12.5)
                self.wait_until(lambda: player.state["status"] == "playing")
                self.assertEqual(player.state["index"], 1)
                command.assert_any_call(
                    ["loadfile", "/tmp/film.mp4", "replace", -1, "start=12.500"]
                )
            player.stop()
            self.wait_until(lambda: player.process.state() == QProcess.NotRunning)

    def test_preview_uses_current_player_without_second_decoder(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary) / "fake-mpv"
            binary.write_text(FAKE_MPV, encoding="utf-8")
            binary.chmod(0o755)
            player = MpvPlayer()
            frames = []
            player.frame_ready.connect(frames.append)
            player.start(str(binary), [{"path": "/tmp/film.mp4", "duration": 90}], 0)
            self.wait_until(lambda: player.state["status"] == "playing")
            self.wait_until(lambda: player.state["duration"] == 60)
            self.wait_until(lambda: player.file_ready)
            self.assertTrue(player.request_preview())
            self.assertFalse(player.request_preview())
            self.wait_until(lambda: len(frames) == 1)
            self.assertEqual(Path(frames[0]).read_bytes(), b"frame")
            player.blackout()
            self.assertFalse(player.request_preview())
            player.stop()
            self.wait_until(lambda: player.process.state() == QProcess.NotRunning)
            self.assertFalse(Path(frames[0]).exists())

    def test_late_preview_from_previous_clip_is_discarded(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary) / "fake-mpv"
            binary.write_text(FAKE_MPV, encoding="utf-8")
            binary.chmod(0o755)
            player = MpvPlayer()
            frames = []
            player.frame_ready.connect(frames.append)
            items = [
                {"path": "/tmp/first.mp4", "duration": 30},
                {"path": "/tmp/second.mp4", "duration": 60},
            ]
            player.start(str(binary), items, 0)
            self.wait_until(lambda: player.state["status"] == "playing")
            self.wait_until(lambda: player.file_ready)
            self.assertTrue(player.request_preview())
            player.next()
            self.wait_until(lambda: player.preview_request is None)
            self.assertEqual(frames, [])
            self.assertTrue(player.preview_supported)
            player.stop()
            self.wait_until(lambda: player.process.state() == QProcess.NotRunning)


if __name__ == "__main__":
    unittest.main()

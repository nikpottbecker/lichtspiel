import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

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
        command = json.loads(line)["command"]
        if command[0] == "loadfile":
            client.sendall(b'{"event":"property-change","name":"duration","data":60}\\n')
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


if __name__ == "__main__":
    unittest.main()

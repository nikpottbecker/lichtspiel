"""Nonblocking mpv process control. Qt remains responsive while video plays."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QTimer, Signal
from PySide6.QtNetwork import QLocalSocket


def find_mpv(preferred: str = "") -> str:
    candidates = [preferred, shutil.which("mpv") or ""]
    if sys.platform == "darwin":
        candidates.extend(
            [
                "/opt/homebrew/bin/mpv",
                "/usr/local/bin/mpv",
                "/Applications/mpv.app/Contents/MacOS/mpv",
            ]
        )
    elif sys.platform == "win32":
        candidates.extend(
            [
                str(
                    Path(os.environ.get("LOCALAPPDATA", ""))
                    / "Programs"
                    / "mpv"
                    / "mpv.exe"
                ),
                r"C:\mpv\mpv.exe",
            ]
        )
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        try:
            result = subprocess.run(
                [candidate, "--version"],
                capture_output=True,
                text=True,
                timeout=4,
                check=True,
            )
            if re.search(r"\bmpv\s+v?\d", result.stdout, re.IGNORECASE):
                return candidate
        except (OSError, subprocess.SubprocessError):
            continue
    return ""


def probe_duration(binary: str, filename: str) -> float:
    result = subprocess.run(
        [
            binary,
            "--no-config",
            "--vo=null",
            "--ao=null",
            "--frames=1",
            "--term-status-msg=",
            "--term-playing-msg=LICHTSPIEL_DURATION=${=duration}",
            "--",
            filename,
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    match = re.search(r"LICHTSPIEL_DURATION=([\d.]+)", result.stdout + result.stderr)
    if not match:
        raise ValueError(
            f"Die Laufzeit von „{Path(filename).name}“ konnte nicht gelesen werden."
        )
    value = float(match.group(1))
    if value <= 0:
        raise ValueError(f"Ungültige Laufzeit: {Path(filename).name}")
    return value


def audio_devices(binary: str) -> list[tuple[str, str]]:
    if not binary:
        return [("auto", "Systemstandard")]
    try:
        result = subprocess.run(
            [binary, "--no-config", "--audio-device=help"],
            capture_output=True,
            text=True,
            timeout=8,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return [("auto", "Systemstandard")]
    devices = re.findall(
        r"^\s*'([^']+)'\s+\((.+)\)\s*$", result.stdout + result.stderr, re.MULTILINE
    )
    return devices or [("auto", "Systemstandard")]


def display_args(index: int) -> list[str]:
    if index < 0:
        raise ValueError("Ungültiger Ausgabebildschirm.")
    return [f"--screen={index}", f"--fs-screen={index}"]


def test_pattern_path() -> str:
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / "lichtspiel" / "assets" / "projection-test.png")
    return str(
        Path(__file__).resolve().parents[2]
        / "electron"
        / "assets"
        / "projection-test.png"
    )


class MpvPlayer(QObject):
    state_changed = Signal(dict)
    frame_ready = Signal(str)
    preview_unavailable = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.SeparateChannels)
        self.process.errorOccurred.connect(self._process_error)
        self.process.finished.connect(self._finished)
        self.process.readyReadStandardError.connect(self._drain_stderr)
        self.process.readyReadStandardOutput.connect(self._drain_stdout)
        self.socket = QLocalSocket(self)
        self.socket.readyRead.connect(self._read_socket)
        self.socket.errorOccurred.connect(self._socket_error)
        self.connect_timer = QTimer(self)
        self.connect_timer.setInterval(100)
        self.connect_timer.timeout.connect(self._try_connect)
        self.watchdog = QTimer(self)
        self.watchdog.setInterval(3000)
        self.watchdog.timeout.connect(self._watchdog_tick)
        self.connect_attempts = 0
        self.last_reply = 0.0
        self.heartbeat_serial = 1000
        self.preview_request = None
        self.preview_filename = ""
        self.preview_request_index = -1
        self.preview_requested_at = 0.0
        self.preview_supported = True
        self.preview_directory = None
        self.file_ready = False
        self.stderr_tail = b""
        self.buffer = b""
        self.items: list[dict] = []
        self.endpoint = ""
        self.intentional_stop = False
        self.state = {"status": "idle", "index": 0, "position": 0.0, "duration": 0.0}

    def _update(self, **patch):
        self.state = {**self.state, **patch}
        self.state_changed.emit(self.state.copy())

    def active(self) -> bool:
        return self.state["status"] in ("starting", "playing", "paused", "blackout")

    def _command(self, command: list, request_id: int | None = None) -> None:
        if self.socket.state() != QLocalSocket.ConnectedState:
            raise RuntimeError("Player ist nicht verbunden.")
        message = {"command": command}
        if request_id is not None:
            message["request_id"] = request_id
        self.socket.write((json.dumps(message) + "\n").encode())

    def start(
        self,
        binary: str,
        items: list[dict],
        screen_index: int,
        audio_device: str = "auto",
        start_index: int = 0,
        start_position: float = 0.0,
    ):
        if self.active() or self.process.state() != QProcess.NotRunning:
            raise RuntimeError("Eine Vorstellung läuft bereits.")
        if not binary:
            raise RuntimeError("mpv fehlt. Wähle den Player in der Einrichtung aus.")
        if not items:
            raise RuntimeError("Der Ablauf ist leer.")
        if (
            not 0 <= start_index < len(items)
            or not 0 <= start_position < items[start_index]["duration"]
        ):
            raise ValueError("Ungültiger Wiederaufnahmepunkt.")
        self.items = [dict(item) for item in items]
        if self.preview_directory is not None:
            self.preview_directory.cleanup()
        self.preview_directory = tempfile.TemporaryDirectory(
            prefix="lichtspiel-preview-", ignore_cleanup_errors=True
        )
        self.preview_request = None
        self.preview_filename = ""
        self.preview_request_index = -1
        self.preview_supported = True
        self.file_ready = False
        self.start_position = start_position
        self.intentional_stop = False
        self.buffer = b""
        self.stderr_tail = b""
        self.endpoint = (
            rf"\\.\pipe\lichtspiel-{uuid.uuid4()}"
            if sys.platform == "win32"
            else str(Path(tempfile.gettempdir()) / f"lichtspiel-{uuid.uuid4()}.sock")
        )
        self.process.setProgram(binary)
        self.process.setArguments(
            [
                "--no-config",
                "--idle=yes",
                "--force-window=yes",
                "--keep-open=no",
                "--fullscreen=yes",
                *display_args(screen_index),
                "--no-osc",
                "--osd-level=0",
                "--input-default-bindings=no",
                "--input-vo-keyboard=no",
                "--cursor-autohide=always",
                "--no-input-terminal",
                "--screenshot-jpeg-quality=65",
                "--title=Lichtspiel – Leinwand",
                f"--audio-device={audio_device}",
                f"--input-ipc-server={self.endpoint}",
            ]
        )
        self._update(
            status="starting",
            index=start_index,
            position=start_position,
            duration=items[start_index]["duration"],
            message="",
        )
        self.process.start()
        self.connect_attempts = 0
        self.connect_timer.start()

    def _try_connect(self):
        if self.socket.state() == QLocalSocket.ConnectedState:
            self.connect_timer.stop()
            self._command(["observe_property", 1, "time-pos"])
            self._command(["observe_property", 2, "duration"])
            media = self.items[self.state["index"]]
            command = ["loadfile", media["path"], "replace"]
            if self.start_position:
                # mpv's fourth loadfile argument applies only to this file.
                command.extend([-1, f"start={self.start_position:.3f}"])
            self._command(command)
            self.last_reply = time.monotonic()
            self.watchdog.start()
            self._update(status="playing")
            return
        if self.process.state() == QProcess.NotRunning and self.connect_attempts > 1:
            self.fail(
                "mpv konnte nicht gestartet werden. Prüfe Player und Ausgabegerät."
            )
            return
        self.connect_attempts += 1
        if self.connect_attempts > 70:
            self.fail("Keine Verbindung zum Player. Bitte mpv neu auswählen.")
            return
        if self.socket.state() == QLocalSocket.UnconnectedState:
            self.socket.connectToServer(self.endpoint)

    def _read_socket(self):
        self.buffer += bytes(self.socket.readAll())
        if len(self.buffer) > 2 * 1024 * 1024:
            self.fail("Ungültige Player-Antwort.")
            return
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                message = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if (
                isinstance(message.get("request_id"), int)
                and message["request_id"] >= 1000
            ):
                self.last_reply = time.monotonic()
            if (
                self.preview_request is not None
                and message.get("request_id") == self.preview_request
            ):
                self.preview_request = None
                filename = Path(self.preview_filename)
                if self.preview_request_index != self.state["index"]:
                    filename.unlink(missing_ok=True)
                elif message.get("error") == "success" and self.preview_directory:
                    if filename.is_file():
                        self.frame_ready.emit(str(filename))
                    else:
                        self._disable_preview("Kein Vorschaubild empfangen.")
                else:
                    self._disable_preview("mpv unterstützt die Bildvorschau nicht.")
            if message.get("event") == "property-change" and isinstance(
                message.get("data"), (int, float)
            ):
                if message.get("name") == "time-pos":
                    self._update(position=message["data"])
                elif message.get("name") == "duration":
                    self._update(duration=message["data"])
            elif message.get("event") == "file-loaded":
                self.file_ready = True
            elif message.get("event") == "end-file":
                self.file_ready = False
                if message.get("reason") == "eof":
                    self.next()
                elif message.get("reason") == "error":
                    self.fail(
                        "Das Medium konnte nicht abgespielt werden. Bitte Datei und Codec prüfen."
                    )

    def _process_error(self, _error):
        if not self.intentional_stop and self.active():
            self.fail(
                "mpv konnte nicht gestartet werden. Prüfe Player und Ausgabegerät."
            )

    def _socket_error(self, _error):
        # Connection refusals are expected while mpv creates its IPC endpoint.
        if (
            self.state["status"] != "starting"
            and not self.intentional_stop
            and self.active()
        ):
            self.fail("Die Verbindung zum Player ist abgebrochen.")

    def _finished(self, _code, _status):
        self._cleanup_preview()
        if not self.intentional_stop and self.active():
            self.fail("Der Player wurde beendet. Prüfe mpv und die Ausgabe.")

    def _cleanup_preview(self):
        if self.preview_directory is not None:
            self.preview_directory.cleanup()
            self.preview_directory = None

    def _drain_stderr(self):
        self.stderr_tail = (
            self.stderr_tail + bytes(self.process.readAllStandardError())
        )[-4096:]

    def _drain_stdout(self):
        self.process.readAllStandardOutput()

    def _watchdog_tick(self):
        if not self.active() or self.state["status"] == "starting":
            return
        if time.monotonic() - self.last_reply > 12:
            self.fail(
                "Der Player antwortet seit 12 Sekunden nicht. Prüfe mpv und die Ausgabedatei."
            )
            return
        self.heartbeat_serial += 1
        try:
            self._command(["get_property", "time-pos"], self.heartbeat_serial)
        except RuntimeError:
            self.fail("Der Player ist nicht mehr verbunden.")

    def request_preview(self) -> bool:
        if (
            not self.preview_supported
            or not self.file_ready
            or self.state["status"]
            not in (
                "playing",
                "paused",
            )
        ):
            return False
        if self.preview_request is not None:
            if time.monotonic() - self.preview_requested_at > 6:
                self._disable_preview("Bildvorschau antwortet nicht.")
            return False
        if self.socket.state() != QLocalSocket.ConnectedState:
            return False
        self.heartbeat_serial += 1
        self.preview_request = self.heartbeat_serial
        self.preview_request_index = self.state["index"]
        self.preview_requested_at = time.monotonic()
        try:
            filename = str(
                Path(self.preview_directory.name) / f"frame-{self.preview_request}.jpg"
            )
            self.preview_filename = filename
            self._command(
                ["screenshot-to-file", filename, "video"], self.preview_request
            )
        except (OSError, RuntimeError):
            self._disable_preview("Bildvorschau konnte nicht angefordert werden.")
            return False
        return True

    def _disable_preview(self, message: str):
        self.preview_supported = False
        self.preview_request = None
        self.preview_unavailable.emit(message)

    def pause(self):
        if self.state["status"] == "playing":
            self._command(["set_property", "pause", True])
            self._update(status="paused")

    def resume(self):
        if self.state["status"] not in ("paused", "blackout"):
            return
        if self.state["status"] == "blackout":
            self._command(["set_property", "brightness", 0])
            self._command(["set_property", "sub-visibility", True])
        self._command(["set_property", "pause", False])
        self._update(status="playing")

    def blackout(self):
        if self.state["status"] not in ("playing", "paused"):
            return
        self._command(["set_property", "pause", True])
        self._command(["set_property", "sub-visibility", False])
        self._command(["set_property", "brightness", -100])
        self._update(status="blackout")

    def next(self):
        if not self.active() or self.state["status"] == "starting":
            return
        index = self.state["index"] + 1
        if index >= len(self.items):
            duration = self.state["duration"]
            self.stop()
            self._update(
                status="finished",
                index=len(self.items) - 1,
                position=duration,
                duration=duration,
            )
            return
        status = self.state["status"]
        self.file_ready = False
        self._command(["loadfile", self.items[index]["path"], "replace"])
        if status in ("paused", "blackout"):
            self._command(["set_property", "pause", True])
        self._update(index=index, position=0.0, duration=self.items[index]["duration"])

    def stop(self, reason: str = "user"):
        self.intentional_stop = True
        self.file_ready = False
        self.preview_request = None
        self.connect_timer.stop()
        self.watchdog.stop()
        if self.socket.state() == QLocalSocket.ConnectedState:
            try:
                self._command(["quit"])
                self.socket.flush()
            except RuntimeError:
                pass
        self.socket.abort()
        if self.process.state() == QProcess.NotRunning:
            self._cleanup_preview()
        if self.process.state() != QProcess.NotRunning:
            QTimer.singleShot(1500, self._kill_if_running)
        if self.endpoint and sys.platform != "win32":
            try:
                Path(self.endpoint).unlink(missing_ok=True)
            except OSError:
                pass
        self._update(
            status="error" if reason == "error" else "idle",
            index=0,
            position=0.0,
            duration=0.0,
            message="",
        )

    def _kill_if_running(self):
        if self.process.state() != QProcess.NotRunning:
            self.process.kill()

    def fail(self, message: str):
        self.stop(reason="error")
        self._update(status="error", message=message)


class ProjectionTest(QObject):
    finished = Signal(bool, str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._error)
        self.failed = False

    def active(self) -> bool:
        return self.process.state() != QProcess.NotRunning

    def start(self, binary: str, screen_index: int):
        if self.active():
            raise RuntimeError("Der Ausgabetest läuft bereits.")
        if not binary:
            raise RuntimeError("mpv fehlt. Wähle den Player in der Einrichtung aus.")
        self.failed = False
        self.process.start(
            binary,
            [
                "--no-config",
                "--fullscreen=yes",
                *display_args(screen_index),
                "--image-display-duration=12",
                "--no-audio",
                "--no-osc",
                "--osd-level=0",
                "--no-input-terminal",
                "--title=Lichtspiel – Ausgabetest",
                "--",
                test_pattern_path(),
            ],
        )

    def _error(self, _error):
        self.failed = True
        self.finished.emit(False, "Die Testkarte konnte nicht geöffnet werden.")

    def _finished(self, code, _status):
        if not self.failed:
            self.finished.emit(
                code == 0, "" if code == 0 else "Der Ausgabetest wurde beendet."
            )

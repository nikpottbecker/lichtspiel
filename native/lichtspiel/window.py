"""Qt Widgets control room. Video stays in mpv's own process and window."""

import json
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateTimeEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .awake import WakeGuard
from .lighting import EVENTS, LABELS, LightingController
from .model import (
    atomic_json,
    data_directory,
    load_project,
    preflight,
    queued_media,
    save_project,
)
from .player import MpvPlayer, ProjectionTest, audio_devices, find_mpv, probe_duration
from .style import STYLESHEET

VIDEO_FILTER = "Videodateien (*.mp4 *.m4v *.mov *.mkv *.webm *.avi *.mpg *.mpeg)"
CATEGORIES = ("Werbung", "Trailer", "Intro", "Film")


def button(label: str, handler, kind: str = "") -> QPushButton:
    control = QPushButton(label)
    if kind:
        control.setObjectName(kind)
    control.clicked.connect(handler)
    return control


def label(text: str, kind: str = "") -> QLabel:
    control = QLabel(text)
    control.setWordWrap(True)
    if kind:
        control.setObjectName(kind)
    return control


def rule() -> QFrame:
    control = QFrame()
    control.setObjectName("rule")
    control.setFixedHeight(1)
    return control


def import_files(binary: str, paths: list[str]) -> list[dict]:
    result = []
    for filename in paths:
        source = Path(filename)
        if not source.is_file() or source.stat().st_size <= 0:
            raise ValueError(f"Datei ist leer oder fehlt: {source.name}")
        result.append(
            {
                "id": str(uuid4()),
                "name": source.stem,
                "path": str(source),
                "duration": probe_duration(binary, str(source)),
                "category": "Film",
                "size": source.stat().st_size,
            }
        )
    return result


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lichtspiel · Kinoregie")
        self.resize(1260, 820)
        self.setMinimumSize(900, 640)
        self.setStyleSheet(STYLESHEET)
        self.project = load_project()
        self.settings_path = data_directory() / "settings.json"
        self.native_display_id = self._read_settings().get("nativeDisplayId", "")
        self.mpv = ""
        self.player = MpvPlayer(self)
        self.projection = ProjectionTest(self)
        self.wake_guard = WakeGuard()
        self.lighting = LightingController()
        self.executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="lichtspiel-media"
        )
        self.jobs: list[tuple[object, object]] = []
        self.scheduled_at: float | None = None
        self._build()
        self.player.state_changed.connect(self._player_state)
        self.projection.finished.connect(self._projection_finished)
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(100)
        self.poll_timer.timeout.connect(self._poll_jobs)
        self.poll_timer.start()
        self.schedule_timer = QTimer(self)
        self.schedule_timer.setInterval(500)
        self.schedule_timer.timeout.connect(self._schedule_tick)
        self.schedule_timer.start()
        self._refresh_all()
        self._set_page(
            0
            if self.project.get("onboarded") and self._selected_screen_index() >= 0
            else 2
        )
        self._detect_mpv()

    def _saved_mpv_path(self) -> str:
        return self._read_settings().get("mpvPath", "")

    def _read_settings(self) -> dict:
        try:
            settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
            return settings if isinstance(settings, dict) else {}
        except (OSError, ValueError, AttributeError):
            return {}

    def _save_setting(self, key: str, value: str):
        settings = self._read_settings()
        settings[key] = value
        atomic_json(self.settings_path, settings)

    def _save(self):
        try:
            save_project(self.project)
        except (OSError, ValueError) as error:
            self._error(str(error))

    def _error(self, message: str):
        self.status.setText(message)
        QMessageBox.warning(self, "Lichtspiel", message)

    def _build(self):
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(root)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(22, 30, 22, 25)
        side.setSpacing(8)
        side.addWidget(label("LICHTSPIEL", "brand"))
        side.addWidget(label("DEINE KINOREGIE", "brandCaption"))
        side.addSpacing(42)
        self.nav_buttons = []
        for index, title in enumerate(("Regie", "Mediathek", "Bild && Ton", "Licht")):
            nav = button(
                title, lambda _checked=False, page=index: self._set_page(page), "nav"
            )
            nav.setCheckable(True)
            side.addWidget(nav)
            self.nav_buttons.append(nav)
        side.addStretch()
        side.addWidget(label("Lokal auf deinem Rechner\nBildausgabe über mpv", "muted"))
        layout.addWidget(sidebar)

        content = QWidget()
        content.setObjectName("content")
        main = QVBoxLayout(content)
        self.content_layout = main
        main.setContentsMargins(42, 32, 42, 28)
        main.setSpacing(18)
        self.pages = QStackedWidget()
        scroller = QScrollArea()
        scroller.setWidgetResizable(True)
        scroller.setFrameShape(QFrame.NoFrame)
        scroller.setWidget(self.pages)
        main.addWidget(scroller, 1)
        main.addWidget(rule())
        self.status = label("Bereit", "status")
        self.status.setAccessibleName("Statusmeldung")
        main.addWidget(self.status)
        layout.addWidget(content, 1)
        self._build_show()
        self._build_library()
        self._build_setup()
        self._build_lighting()

    def _page(
        self, eyebrow: str, title: str, description: str
    ) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        page.setObjectName("page")
        column = QVBoxLayout(page)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(16)
        column.addWidget(label(eyebrow.upper(), "eyebrow"))
        column.addWidget(label(title, "pageTitle"))
        column.addWidget(label(description, "muted"))
        column.addSpacing(12)
        self.pages.addWidget(page)
        return page, column

    def _build_show(self):
        _, column = self._page(
            "Vorstellung",
            "Regie",
            "Ablauf vorbereiten, prüfen und während der Vorführung steuern.",
        )
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Name der Vorstellung")
        self.title_input.setMaxLength(80)
        self.title_input.editingFinished.connect(self._save_title)
        column.addWidget(self.title_input)
        column.addWidget(rule())
        column.addWidget(label("ABLAUF", "eyebrow"))
        self.queue_list = QListWidget()
        self.queue_list.setAccessibleName("Ablauf")
        column.addWidget(self.queue_list, 1)
        row = QHBoxLayout()
        self.move_up = button("Nach oben", lambda: self._move_queue(-1))
        self.move_down = button("Nach unten", lambda: self._move_queue(1))
        self.remove_queue = button("Entfernen", self._remove_queue)
        for control in (self.move_up, self.move_down, self.remove_queue):
            row.addWidget(control)
        row.addStretch()
        column.addLayout(row)
        self.readiness = label("Startprüfung ausstehend", "hint")
        column.addWidget(self.readiness)
        column.addWidget(button("Jetzt prüfen", self._check_readiness))
        column.addWidget(rule())
        self.current_cue = label("Keine Vorstellung läuft.", "sectionTitle")
        self.progress = label("", "muted")
        self.transport_surface = QWidget()
        self.transport_surface.setObjectName("transportSurface")
        transport_column = QVBoxLayout(self.transport_surface)
        transport_column.setContentsMargins(0, 12, 0, 0)
        transport_column.setSpacing(8)
        transport_column.addWidget(self.current_cue)
        transport_column.addWidget(self.progress)
        transport = QGridLayout()
        transport.setHorizontalSpacing(10)
        transport.setVerticalSpacing(10)
        self.start_button = button("Vorstellung starten", self._start_show, "primary")
        self.pause_button = button("Pause", self._pause)
        self.resume_button = button("Fortsetzen", self._resume)
        self.blackout_button = button("Schwarzbild", self._blackout)
        self.next_button = button("Nächster Clip", self._next)
        self.stop_button = button("Stopp", self._stop, "danger")
        for number, control in enumerate(
            (
                self.start_button,
                self.pause_button,
                self.resume_button,
                self.blackout_button,
                self.next_button,
                self.stop_button,
            )
        ):
            transport.addWidget(control, number // 3, number % 3)
        transport_column.addLayout(transport)
        self.content_layout.insertWidget(1, self.transport_surface)
        schedule = QHBoxLayout()
        schedule.addWidget(label("Startzeit", "muted"))
        self.time_input = QDateTimeEdit(QDateTime.currentDateTime().addSecs(300))
        self.time_input.setCalendarPopup(True)
        self.time_input.setDisplayFormat("dd.MM.yyyy HH:mm")
        schedule.addWidget(self.time_input)
        self.schedule_button = button("Einplanen", self._schedule)
        schedule.addWidget(self.schedule_button)
        self.cancel_schedule = button("Planung löschen", self._cancel_schedule)
        schedule.addWidget(self.cancel_schedule)
        schedule.addStretch()
        column.addLayout(schedule)

    def _build_library(self):
        _, column = self._page(
            "Medien",
            "Mediathek",
            "Dateien bleiben an ihrem Speicherort. Der Ablauf enthält Verweise.",
        )
        column.addWidget(label("IMPORTIERTE MEDIEN", "eyebrow"))
        self.library_list = QListWidget()
        self.library_list.itemDoubleClicked.connect(lambda _item: self._add_to_queue())
        self.library_list.currentRowChanged.connect(self._library_selection)
        column.addWidget(self.library_list, 1)
        row = QHBoxLayout()
        self.import_button = button("Medien hinzufügen", self._import_media, "primary")
        row.addWidget(self.import_button)
        row.addWidget(button("Zum Ablauf", self._add_to_queue))
        row.addWidget(button("Aus Mediathek entfernen", self._remove_library))
        row.addStretch()
        column.addLayout(row)
        category_row = QHBoxLayout()
        category_row.addWidget(label("Kategorie", "muted"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        self.category_combo.currentTextChanged.connect(self._change_category)
        category_row.addWidget(self.category_combo)
        category_row.addStretch()
        column.addLayout(category_row)
        column.addWidget(
            label(
                "Tipp: Doppelklicke ein Medium, um es zum Ablauf hinzuzufügen.", "hint"
            )
        )

    def _build_setup(self):
        _, column = self._page(
            "Einrichtung",
            "Bild & Ton",
            "Regie am Rechner, Film über einen eigenen Player auf der Leinwand.",
        )
        column.addWidget(label("WIEDERGABE", "eyebrow"))
        self.player_path = label("", "muted")
        column.addWidget(self.player_path)
        row = QHBoxLayout()
        row.addWidget(button("mpv auswählen", self._choose_mpv))
        row.addWidget(button("Neu erkennen", self._detect_mpv))
        row.addStretch()
        column.addLayout(row)
        column.addWidget(rule())
        column.addWidget(label("AUSGABE", "eyebrow"))
        column.addWidget(label("Beamer / Bildschirm", "muted"))
        self.display_combo = QComboBox()
        self.display_combo.currentIndexChanged.connect(self._display_changed)
        column.addWidget(self.display_combo)
        self.display_info = label("", "hint")
        column.addWidget(self.display_info)
        self.test_button = button(
            "Testkarte auf dem Beamer zeigen", self._test_projection
        )
        column.addWidget(self.test_button)
        column.addWidget(
            label(
                "Die Testkarte läuft 12 Sekunden über mpv. Prüfe Rahmen, Ecken und Schärfe direkt am Beamer.",
                "hint",
            )
        )
        column.addWidget(rule())
        column.addWidget(label("TONAUSGABE", "eyebrow"))
        self.audio_combo = QComboBox()
        self.audio_combo.currentIndexChanged.connect(self._audio_changed)
        column.addWidget(self.audio_combo)
        column.addWidget(
            label(
                "Verwende einen erweiterten Desktop. Prüfe den Ton danach mit einem kurzen Videoclip.",
                "hint",
            )
        )
        column.addStretch()

    def _build_lighting(self):
        _, column = self._page(
            "Automation",
            "Kinolicht",
            "Optionale Home-Assistant-Regeln für die Vorstellung.",
        )
        self.light_enabled = QCheckBox("Automatische Lichtsteuerung aktivieren")
        column.addWidget(self.light_enabled)
        column.addWidget(label("HOME ASSISTANT", "eyebrow"))
        self.light_url = QLineEdit()
        self.light_url.setPlaceholderText("http://homeassistant.local:8123")
        column.addWidget(self.light_url)
        self.light_entity = QLineEdit()
        self.light_entity.setPlaceholderText("light.kinosaal")
        column.addWidget(self.light_entity)
        self.light_token = QLineEdit()
        self.light_token.setEchoMode(QLineEdit.Password)
        self.light_token.setPlaceholderText(
            "Zugriffstoken · wird im System-Schlüsselbund gespeichert"
        )
        column.addWidget(self.light_token)
        row = QHBoxLayout()
        row.addWidget(button("Einstellungen speichern", self._save_lighting, "primary"))
        row.addWidget(button("Verbindung prüfen", self._test_lighting_connection))
        row.addWidget(button("Token löschen", self._clear_light_token))
        row.addStretch()
        column.addLayout(row)
        column.addWidget(rule())
        column.addWidget(label("LICHTREGELN", "eyebrow"))
        self.light_rules = {}
        for event in EVENTS:
            line = QHBoxLayout()
            enabled = QCheckBox(LABELS[event])
            enabled.setMinimumWidth(145)
            brightness = QSpinBox()
            brightness.setRange(0, 100)
            brightness.setSuffix(" %")
            transition = QSpinBox()
            transition.setRange(0, 120)
            transition.setSuffix(" s")
            line.addWidget(enabled)
            line.addStretch()
            line.addWidget(label("Helligkeit", "muted"))
            line.addWidget(brightness)
            line.addWidget(label("Übergang", "muted"))
            line.addWidget(transition)
            column.addLayout(line)
            self.light_rules[event] = (enabled, brightness, transition)
        column.addWidget(rule())
        test_row = QHBoxLayout()
        self.light_event = QComboBox()
        for event in EVENTS:
            self.light_event.addItem(LABELS[event], event)
        test_row.addWidget(self.light_event)
        test_row.addWidget(button("Licht jetzt testen", self._apply_light_manually))
        test_row.addStretch()
        column.addLayout(test_row)
        column.addWidget(
            label(
                "Der Verbindungstest verändert keine Lampe. „Licht jetzt testen“ sendet einen echten Befehl.",
                "hint",
            )
        )
        column.addStretch()

    def _refresh_lighting(self):
        config = self.lighting.config
        self.light_enabled.setChecked(config["enabled"])
        self.light_url.setText(config["baseUrl"])
        self.light_entity.setText(config["entityId"])
        for event, (enabled, brightness, transition) in self.light_rules.items():
            rule = config["rules"][event]
            enabled.setChecked(rule["enabled"])
            brightness.setValue(rule["brightness"])
            transition.setValue(rule["transition"])

    def _lighting_input(self) -> dict:
        return {
            "enabled": self.light_enabled.isChecked(),
            "baseUrl": self.light_url.text().strip(),
            "entityId": self.light_entity.text().strip(),
            "rules": {
                event: {
                    "enabled": enabled.isChecked(),
                    "brightness": brightness.value(),
                    "transition": transition.value(),
                }
                for event, (enabled, brightness, transition) in self.light_rules.items()
            },
        }

    def _save_lighting(self):
        future = self.lighting.executor.submit(
            self.lighting.save, self._lighting_input(), self.light_token.text()
        )

        def complete(_config):
            self.light_token.clear()
            self.status.setText("Lichteinstellungen gespeichert.")

        self.jobs.append((future, complete))

    def _test_lighting_connection(self):
        future = self.lighting.executor.submit(self.lighting.test_connection)
        self.jobs.append((future, self.status.setText))

    def _apply_light_manually(self):
        event = self.light_event.currentData()
        if not self.lighting.config["enabled"]:
            self._error("Aktiviere und speichere zuerst die Lichtsteuerung.")
            return
        future = self.lighting.executor.submit(self.lighting.apply, event)
        self.jobs.append(
            (
                future,
                lambda message: self.status.setText(
                    message or "Lichtregel deaktiviert."
                ),
            )
        )

    def _clear_light_token(self):
        future = self.lighting.executor.submit(self.lighting.clear_token)

        def complete(_result):
            self.light_token.clear()
            self._refresh_lighting()
            self.status.setText(
                "Token entfernt; automatische Lichtsteuerung deaktiviert."
            )

        self.jobs.append((future, complete))

    def _set_page(self, index: int):
        self.pages.setCurrentIndex(index)
        self.transport_surface.setVisible(index == 0)
        for number, nav in enumerate(self.nav_buttons):
            nav.setChecked(number == index)

    def _refresh_all(self):
        self.title_input.setText(self.project.get("title", "Filmabend"))
        self._refresh_displays()
        self._refresh_audio([("auto", "Systemstandard")])
        if self.mpv:
            self._load_audio()
        self.player_path.setText(
            self.mpv or "mpv nicht gefunden. Installiere mpv und wähle die Datei."
        )
        self._refresh_lists()
        self._refresh_lighting()
        self._player_state(self.player.state)

    def _screens(self):
        from PySide6.QtGui import QGuiApplication

        return QGuiApplication.screens()

    def _screen_id(self, index: int, screen) -> str:
        return f"qt:{index}:{screen.name()}"

    def _selected_screen_index(self) -> int:
        selected = self.display_combo.currentData()
        for index, screen in enumerate(self._screens()):
            if self._screen_id(index, screen) == selected:
                return index
        return -1

    def _refresh_displays(self):
        self.display_combo.blockSignals(True)
        self.display_combo.clear()
        self.display_combo.addItem("Ausgabe wählen", "")
        for index, screen in enumerate(self._screens()):
            size = screen.size()
            name = screen.name() or f"Bildschirm {index + 1}"
            suffix = " · Hauptbildschirm" if screen == self._screens()[0] else ""
            self.display_combo.addItem(
                f"{name} · {size.width()} × {size.height()}{suffix}",
                self._screen_id(index, screen),
            )
        selected = self.display_combo.findData(self.native_display_id)
        self.display_combo.setCurrentIndex(max(0, selected))
        self.display_combo.blockSignals(False)
        self._display_info()

    def _refresh_audio(self, devices):
        self.audio_combo.blockSignals(True)
        self.audio_combo.clear()
        if not any(key == "auto" for key, _ in devices):
            devices.insert(0, ("auto", "Systemstandard"))
        for key, name in devices:
            self.audio_combo.addItem(name, key)
        index = self.audio_combo.findData(self.project.get("audioDevice", "auto"))
        self.audio_combo.setCurrentIndex(max(0, index))
        self.audio_combo.blockSignals(False)

    def _load_audio(self):
        binary = self.mpv
        future = self.executor.submit(audio_devices, binary)

        def complete(devices):
            if self.mpv == binary:
                self._refresh_audio(devices)

        self.jobs.append((future, complete))

    def _display_info(self):
        index = self._selected_screen_index()
        self.display_info.setText(
            "Testkarte auf dem gewünschten Beamer prüfen; Bildschirmnummern können zwischen Qt und mpv abweichen."
            if index >= 0
            else "Schließe den Beamer an und wähle die Ausgabe."
        )
        self.test_button.setEnabled(
            index >= 0 and bool(self.mpv) and not self.projection.active()
        )

    def _display_changed(self, _index):
        self.native_display_id = self.display_combo.currentData() or ""
        self._save_setting("nativeDisplayId", self.native_display_id)
        self.project["onboarded"] = bool(self.native_display_id and self.mpv)
        self._save()
        self._display_info()

    def _audio_changed(self, _index):
        self.project["audioDevice"] = self.audio_combo.currentData() or "auto"
        self._save()

    def _save_title(self):
        self.project["title"] = self.title_input.text().strip() or "Filmabend"
        self._save()

    def _refresh_lists(self):
        selected_library = self.library_list.currentRow()
        selected_queue = self.queue_list.currentRow()
        self.library_list.blockSignals(True)
        self.library_list.clear()
        for media in self.project["library"]:
            item = QListWidgetItem(
                f"{media.get('name', 'Ohne Titel')}   ·   {media.get('category', 'Film')}   ·   {self._duration(media.get('duration', 0))}"
            )
            item.setData(Qt.UserRole, media.get("id"))
            self.library_list.addItem(item)
        self.library_list.setCurrentRow(
            min(selected_library, self.library_list.count() - 1)
        )
        self.library_list.blockSignals(False)
        self.queue_list.clear()
        for index, media in enumerate(queued_media(self.project)):
            self.queue_list.addItem(
                f"{index + 1:02d}   {media.get('category', 'Film').upper():8}   {media.get('name', 'Ohne Titel')}   ·   {self._duration(media.get('duration', 0))}"
            )
        self.queue_list.setCurrentRow(min(selected_queue, self.queue_list.count() - 1))
        self._library_selection(self.library_list.currentRow())
        self.readiness.setText("Ablauf geändert · Startprüfung erneut ausführen")

    @staticmethod
    def _duration(seconds) -> str:
        minutes, second = divmod(int(seconds or 0), 60)
        hours, minute = divmod(minutes, 60)
        return (
            f"{hours}:{minute:02d}:{second:02d}"
            if hours
            else f"{minute:02d}:{second:02d}"
        )

    def _library_selection(self, row: int):
        self.category_combo.blockSignals(True)
        category = (
            self.project["library"][row].get("category", "Film")
            if 0 <= row < len(self.project["library"])
            else "Film"
        )
        self.category_combo.setCurrentText(category)
        self.category_combo.blockSignals(False)

    def _change_category(self, value: str):
        row = self.library_list.currentRow()
        if 0 <= row < len(self.project["library"]):
            self.project["library"][row]["category"] = value
            self._save()
            self._refresh_lists()

    def _import_media(self):
        if not self.mpv:
            self._error("Bitte zuerst mpv in Bild & Ton auswählen.")
            return
        paths, _selected = QFileDialog.getOpenFileNames(
            self, "Medien importieren", "", VIDEO_FILTER
        )
        if not paths:
            return
        self.import_button.setEnabled(False)
        self.status.setText(f"{len(paths)} Datei(en) werden geprüft …")
        future = self.executor.submit(import_files, self.mpv, paths)

        def complete(result):
            self.project["library"].extend(result)
            self.project["queue"].extend(item["id"] for item in result)
            self._save()
            self._refresh_lists()
            self.import_button.setEnabled(True)
            self.status.setText(f"{len(result)} Medium/Medien importiert.")

        self.jobs.append((future, complete))

    def _add_to_queue(self):
        row = self.library_list.currentRow()
        if row < 0:
            return
        self.project["queue"].append(self.project["library"][row]["id"])
        self._save()
        self._refresh_lists()

    def _remove_library(self):
        row = self.library_list.currentRow()
        if row < 0 or self.player.active():
            return
        media = self.project["library"].pop(row)
        self.project["queue"] = [
            value for value in self.project["queue"] if value != media["id"]
        ]
        self._save()
        self._refresh_lists()

    def _move_queue(self, delta: int):
        row = self.queue_list.currentRow()
        target = row + delta
        if (
            self.player.active()
            or row < 0
            or not (0 <= target < len(self.project["queue"]))
        ):
            return
        self.project["queue"][row], self.project["queue"][target] = (
            self.project["queue"][target],
            self.project["queue"][row],
        )
        self._save()
        self._refresh_lists()
        self.queue_list.setCurrentRow(target)

    def _remove_queue(self):
        row = self.queue_list.currentRow()
        if row < 0 or self.player.active():
            return
        self.project["queue"].pop(row)
        self._save()
        self._refresh_lists()

    def _choose_mpv(self):
        filename, _selected = QFileDialog.getOpenFileName(
            self, "mpv-Programm auswählen"
        )
        if not filename:
            return
        self.status.setText("mpv wird geprüft …")
        future = self.executor.submit(find_mpv, filename)

        def complete(found):
            if not found or Path(found).resolve() != Path(filename).resolve():
                raise ValueError(
                    "Das ausgewählte Programm ist kein funktionierender mpv-Player."
                )
            self.mpv = found
            self._save_setting("mpvPath", found)
            self._refresh_all()
            self.status.setText("mpv ist bereit.")

        self.jobs.append((future, complete))

    def _detect_mpv(self):
        self.status.setText("mpv wird gesucht …")
        future = self.executor.submit(find_mpv, self._saved_mpv_path())

        def complete(found):
            self.mpv = found
            self._refresh_all()
            self.status.setText(
                "mpv gefunden." if self.mpv else "mpv wurde nicht gefunden."
            )

        self.jobs.append((future, complete))

    def _test_projection(self):
        if self.player.active() or self.scheduled_at is not None:
            self._error("Während einer Vorstellung oder Startplanung nicht verfügbar.")
            return
        index = self._selected_screen_index()
        if index < 0:
            self._error("Wähle zuerst einen Ausgabebildschirm.")
            return
        try:
            self.projection.start(self.mpv, index)
            self._sync_wake()
            self.test_button.setEnabled(False)
            self.status.setText("Testkarte wird 12 Sekunden auf der Ausgabe gezeigt.")
        except RuntimeError as error:
            self._error(str(error))

    def _projection_finished(self, ok: bool, message: str):
        self._sync_wake()
        self._display_info()
        self.status.setText(
            "Ausgabetest beendet. Prüfe das Bild am Beamer selbst."
            if ok
            else message or "Ausgabetest fehlgeschlagen."
        )

    def _check_readiness(self):
        self.readiness.setText("Medien werden geprüft …")
        future = self.executor.submit(preflight, deepcopy(self.project))

        def complete(items):
            if not self.mpv:
                raise ValueError("mpv fehlt. Wähle den Player in Bild & Ton aus.")
            if self._selected_screen_index() < 0:
                raise ValueError("Beamer / Bildschirm auswählen oder neu erkennen.")
            self.readiness.setText(
                f"Bereit · {len(items)} Medien lesbar · mpv verfügbar · Ausgabe gewählt"
            )

        self.jobs.append((future, complete))

    def _start_show(self):
        if self.player.active() or self.projection.active():
            return
        if not self.mpv or self._selected_screen_index() < 0:
            self._error("Wähle zuerst mpv und einen Ausgabebildschirm.")
            return
        index = self._selected_screen_index()
        audio = self.project.get("audioDevice", "auto")
        queue_snapshot = list(self.project["queue"])
        self.start_button.setEnabled(False)
        self.readiness.setText("Medien werden vor dem Start geprüft …")
        future = self.executor.submit(preflight, deepcopy(self.project))

        def complete(items):
            self.start_button.setEnabled(True)
            if (
                self.project["queue"] != queue_snapshot
                or self._selected_screen_index() != index
            ):
                raise RuntimeError(
                    "Ablauf oder Ausgabe wurde während der Startprüfung geändert. Bitte erneut starten."
                )
            if self.projection.active():
                raise RuntimeError("Der Ausgabetest läuft noch.")
            self.player.start(self.mpv, items, index, audio)
            self.readiness.setText("Startprüfung bestanden")

        self.jobs.append((future, complete))

    def _poll_jobs(self):
        for future, complete in list(self.jobs):
            if not future.done():
                continue
            self.jobs.remove((future, complete))
            try:
                complete(future.result())
            except Exception as error:  # noqa: BLE001 - show any worker or OS error in the UI.
                self.import_button.setEnabled(True)
                self.start_button.setEnabled(True)
                self.readiness.setText(str(error))
                self._error(str(error))

    def _schedule(self):
        when = self.time_input.dateTime().toSecsSinceEpoch()
        if when <= datetime.now().timestamp():
            self._error("Wähle eine zukünftige Startzeit.")
            return
        if self.player.active() or self.projection.active():
            self._error("Eine Vorstellung oder ein Ausgabetest läuft bereits.")
            return
        self.scheduled_at = float(when)
        self._sync_wake()
        self.project["startAt"] = datetime.fromtimestamp(when).isoformat()
        self._save()
        self.status.setText(
            f"Vorstellung für {self.time_input.text()} eingeplant. App geöffnet lassen."
        )

    def _cancel_schedule(self):
        self.scheduled_at = None
        self._sync_wake()
        self.project["startAt"] = ""
        self._save()
        self.status.setText("Startplanung aufgehoben.")

    def _schedule_tick(self):
        if self.scheduled_at is None:
            return
        now = datetime.now().timestamp()
        if now < self.scheduled_at:
            return
        target = self.scheduled_at
        self._cancel_schedule()
        if now - target > 10:
            self.status.setText(
                "Geplanter Start verpasst. Bitte Vorstellung manuell starten."
            )
        elif self.player.active() or self.projection.active():
            self.status.setText("Geplanter Start entfällt: Eine Ausgabe läuft bereits.")
        else:
            self._start_show()

    def _player_state(self, state: dict):
        status = state["status"]
        active = status in ("starting", "playing", "paused", "blackout")
        self._sync_wake()
        light_event = self.lighting.observe(state, self.player.items)
        if light_event:
            future = self.lighting.executor.submit(self.lighting.apply, light_event)
            self.jobs.append(
                (future, lambda message: self.status.setText(message or ""))
            )
        self.start_button.setEnabled(not active)
        self.pause_button.setEnabled(status == "playing")
        self.resume_button.setEnabled(status in ("paused", "blackout"))
        self.blackout_button.setEnabled(status in ("playing", "paused"))
        self.next_button.setEnabled(status in ("playing", "paused", "blackout"))
        self.stop_button.setEnabled(active)
        for control in (self.move_up, self.move_down, self.remove_queue):
            control.setEnabled(not active)
        if active and state["index"] < len(self.player.items):
            media = self.player.items[state["index"]]
            self.current_cue.setText(
                f"{media.get('category', 'Film')}  ·  {media.get('name', '')}"
            )
            self.progress.setText(
                f"{self._duration(state['position'])} / {self._duration(state['duration'])}  ·  {status}"
                + (
                    f"  ·  Danach: {self.player.items[state['index'] + 1].get('name', '')}"
                    if state["index"] + 1 < len(self.player.items)
                    else "  ·  Letzter Clip"
                )
            )
        else:
            self.current_cue.setText(
                "Keine Vorstellung läuft." if status == "idle" else status.title()
            )
            self.progress.setText("")
        if status == "error":
            self.status.setText(state.get("message") or "Playerfehler")
        elif status == "finished":
            self.status.setText("Vorstellung beendet.")

    def _control(self, action):
        try:
            action()
        except RuntimeError as error:
            self._error(str(error))

    def _pause(self):
        self._control(self.player.pause)

    def _resume(self):
        self._control(self.player.resume)

    def _blackout(self):
        self._control(self.player.blackout)

    def _next(self):
        self._control(self.player.next)

    def _stop(self):
        self.player.stop()
        self.status.setText("Vorstellung gestoppt.")

    def closeEvent(self, event: QCloseEvent):
        if self.player.active():
            answer = QMessageBox.question(
                self,
                "Vorstellung beenden?",
                "Eine Vorstellung läuft. Beim Schließen wird die Wiedergabe beendet.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                event.ignore()
                return
        self.player.stop()
        self.wake_guard.close()
        if self.projection.active():
            self.projection.process.kill()
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.lighting.close()
        super().closeEvent(event)

    def _sync_wake(self):
        self.wake_guard.set_active(
            self.player.active()
            or self.projection.active()
            or self.scheduled_at is not None
        )

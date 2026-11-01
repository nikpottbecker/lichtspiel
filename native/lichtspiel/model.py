"""Project persistence shared with the existing desktop implementation."""

import json
import math
import os
import sys
import tempfile
from pathlib import Path


def data_directory() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "lichtspiel"
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "lichtspiel"
    return (
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "lichtspiel"
    )


def empty_project() -> dict:
    return {
        "version": 1,
        "title": "Filmabend",
        "library": [],
        "queue": [],
        "displayId": "",
        "audioDevice": "auto",
        "onboarded": False,
        "startAt": "",
    }


def load_project(directory: Path | None = None) -> dict:
    filename = (directory or data_directory()) / "project.json"
    if not filename.exists():
        return empty_project()
    data = json.loads(filename.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError("Das gespeicherte Projekt hat ein unbekanntes Format.")
    project = empty_project()
    project.update(data)
    if not isinstance(project["library"], list) or not isinstance(
        project["queue"], list
    ):
        raise TypeError("Die gespeicherte Mediathek ist beschädigt.")
    return project


def atomic_json(filename: Path, data: dict) -> None:
    filename.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if len(payload) > 5 * 1024 * 1024:
        raise ValueError("Das Projekt ist zu groß (maximal 5 MB).")
    descriptor, temporary = tempfile.mkstemp(
        prefix="lichtspiel-", suffix=".tmp", dir=filename.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            target.write(payload)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, filename)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_project(project: dict, directory: Path | None = None) -> None:
    atomic_json((directory or data_directory()) / "project.json", project)


def queued_media(project: dict) -> list[dict]:
    library = {
        item.get("id"): item for item in project["library"] if isinstance(item, dict)
    }
    return [library[media_id] for media_id in project["queue"] if media_id in library]


def preflight(project: dict) -> list[dict]:
    items = queued_media(project)
    if len(items) != len(project["queue"]):
        raise ValueError("Der Ablauf enthält fehlende Medieneinträge.")
    if not items or len(items) > 1000:
        raise ValueError("Füge zuerst Medien zum Ablauf hinzu (maximal 1000).")
    for item in items:
        filename = item.get("path")
        if not isinstance(filename, str) or not os.path.isabs(filename):
            raise ValueError(
                "Der Ablauf enthält eine ungültige Datei. Bitte erneut importieren."
            )
        duration = item.get("duration")
        if (
            not isinstance(duration, (int, float))
            or not math.isfinite(duration)
            or duration <= 0
        ):
            raise ValueError(
                f"Ungültige Laufzeit: {Path(filename).name}. Bitte neu importieren."
            )
        try:
            stat = Path(filename).stat()
            if not Path(filename).is_file() or stat.st_size <= 0:
                raise OSError()
            with open(filename, "rb"):
                pass
        except OSError as error:
            raise ValueError(
                f"Datei fehlt oder ist nicht lesbar: {Path(filename).name}"
            ) from error
    return items

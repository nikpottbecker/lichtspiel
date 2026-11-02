"""Validated, local restart point for an interrupted native show."""

import json
import math
from datetime import UTC, datetime
from pathlib import Path

from .model import atomic_json


def checkpoint(project: dict, items: list[dict], state: dict) -> dict:
    index = int(state["index"])
    if (
        not items
        or len(project["queue"]) != len(items)
        or index < 0
        or index >= len(items)
    ):
        raise ValueError("Der aktuelle Clip liegt außerhalb des Ablaufs.")
    position = float(state.get("position") or 0)
    if not math.isfinite(position) or position < 0:
        raise ValueError("Die Wiedergabeposition ist ungültig.")
    return {
        "version": 1,
        "queue": list(project["queue"]),
        "paths": [item["path"] for item in items],
        "index": index,
        "position": position,
        "savedAt": datetime.now(UTC).isoformat(),
    }


def validate_checkpoint(value: dict, project: dict) -> dict:
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("Der Wiederaufnahmepunkt hat ein unbekanntes Format.")
    queue = value.get("queue")
    paths = value.get("paths")
    if not isinstance(queue, list) or not isinstance(paths, list):
        raise TypeError("Der Wiederaufnahmepunkt ist beschädigt.")
    if queue != project.get("queue") or not queue:
        raise ValueError("Der Ablauf hat sich seit der Unterbrechung geändert.")
    library = {
        item.get("id"): item
        for item in project.get("library", [])
        if isinstance(item, dict)
    }
    if paths != [library.get(media_id, {}).get("path") for media_id in queue]:
        raise ValueError("Eine Mediendatei hat sich seit der Unterbrechung geändert.")
    index = value.get("index")
    position = value.get("position")
    if (
        type(index) is not int
        or index < 0
        or index >= len(queue)
        or type(position) not in (int, float)
        or not math.isfinite(position)
        or position < 0
    ):
        raise ValueError("Die gespeicherte Wiedergabeposition ist ungültig.")
    saved_at = value.get("savedAt")
    if not isinstance(saved_at, str) or not saved_at:
        raise ValueError("Der Zeitpunkt der Unterbrechung fehlt.")
    return value


def read_checkpoint(filename: Path, project: dict) -> dict | None:
    try:
        data = json.loads(filename.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        raise ValueError(
            "Der Wiederaufnahmepunkt kann nicht gelesen werden."
        ) from error
    return validate_checkpoint(data, project)


def write_checkpoint(filename: Path, value: dict) -> None:
    atomic_json(filename, value)


def clear_checkpoint(filename: Path) -> None:
    filename.unlink(missing_ok=True)

"""Bounded, local readout of show events; no media paths or credentials."""

import json
import os
from collections import deque
from datetime import UTC, datetime
from pathlib import Path


def append_event(filename: Path, event: dict) -> None:
    record = {
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
        "run": str(event["run"])[:40],
        "kind": str(event["kind"])[:24],
        "text": str(event["text"])[:500],
    }
    line = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
    filename.parent.mkdir(parents=True, exist_ok=True)
    with filename.open("ab") as target:
        target.write(line)
        target.flush()
        os.fsync(target.fileno())


def read_events(filename: Path, limit: int = 100) -> list[dict]:
    if not filename.exists():
        return []
    # Reading just the tail keeps the native UI responsive even after many shows.
    with filename.open("rb") as source:
        source.seek(0, 2)
        length = source.tell()
        source.seek(max(0, length - 256 * 1024))
        if source.tell():
            source.readline()  # Discard a partial first line.
        lines = deque(source, maxlen=max(1, min(limit, 500)))
    events = []
    for line in lines:
        try:
            event = json.loads(line)
        except (UnicodeDecodeError, ValueError):
            continue
        if (
            isinstance(event, dict)
            and isinstance(event.get("at"), str)
            and isinstance(event.get("text"), str)
        ):
            events.append(event)
    return events


def format_events(events: list[dict]) -> str:
    if not events:
        return "Noch keine Vorführereignisse gespeichert."
    rows = []
    last_run = None
    for event in events:
        if event.get("run") != last_run:
            if rows:
                rows.append("")
            rows.append(f"Vorstellung · {event['at'][:16].replace('T', ' ')} UTC")
            last_run = event.get("run")
        rows.append(f"{event['at'][11:19]}  {event['text']}")
    return "\n".join(rows)

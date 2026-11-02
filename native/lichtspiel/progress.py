"""Read-only timing model for the live control room."""

import math


def clock(seconds: float) -> str:
    value = max(0, int(seconds)) if math.isfinite(seconds) else 0
    hours, remainder = divmod(value, 3600)
    minutes, second = divmod(remainder, 60)
    return (
        f"{hours}:{minutes:02d}:{second:02d}"
        if hours
        else f"{minutes:02d}:{second:02d}"
    )


def timing(state: dict, items: list[dict]) -> dict:
    durations = [max(0.0, float(item.get("duration") or 0)) for item in items]
    total = sum(durations)
    index = min(max(int(state.get("index") or 0), 0), max(len(items) - 1, 0))
    duration = max(0.0, float(state.get("duration") or 0))
    if not duration and durations:
        duration = durations[index]
    position = min(max(0.0, float(state.get("position") or 0)), duration)
    elapsed = min(total, sum(durations[:index]) + position) if items else 0.0
    if state.get("status") == "finished":
        elapsed = total
        position = duration
    return {
        "index": index,
        "count": len(items),
        "position": position,
        "duration": duration,
        "clip_remaining": max(0.0, duration - position),
        "elapsed": elapsed,
        "total": total,
        "show_remaining": max(0.0, total - elapsed),
        "clip_fraction": position / duration if duration > 0 else 0.0,
        "show_fraction": elapsed / total if total > 0 else 0.0,
    }

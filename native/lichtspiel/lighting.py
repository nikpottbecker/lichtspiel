"""Optional Home Assistant automation with OS credential storage."""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import keyring

from .model import atomic_json, data_directory

EVENTS = ("preshow", "feature", "pause", "end")
LABELS = {
    "preshow": "Vorprogramm",
    "feature": "Hauptfilm",
    "pause": "Pause",
    "end": "Ende",
}
SERVICE = "Lichtspiel Home Assistant"


def defaults() -> dict:
    return {
        "enabled": False,
        "baseUrl": "",
        "entityId": "",
        "rules": {
            event: {"enabled": True, "brightness": brightness, "transition": 3}
            for event, brightness in (
                ("preshow", 20),
                ("feature", 0),
                ("pause", 40),
                ("end", 80),
            )
        },
    }


def normalize_url(value: str) -> str:
    if not value.strip():
        return ""
    parsed = urlsplit(value.strip())
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Nutze nur die Home-Assistant-Basisadresse ohne Zugangsdaten oder /api."
        )
    return f"{parsed.scheme}://{parsed.netloc}"


def normalize_config(value: dict) -> dict:
    if not isinstance(value, dict):
        raise TypeError("Ungültige Lichteinstellungen.")
    result = defaults()
    result["enabled"] = value.get("enabled") is True
    result["baseUrl"] = normalize_url(str(value.get("baseUrl", "")))
    result["entityId"] = str(value.get("entityId", "")).strip()
    if result["entityId"] and not re.fullmatch(
        r"light\.[a-z0-9_]+", result["entityId"]
    ):
        raise ValueError("Wähle eine Licht-Entität wie light.kinosaal.")
    supplied_rules = value.get("rules")
    if not isinstance(supplied_rules, dict):
        supplied_rules = {}
    for event in EVENTS:
        supplied = supplied_rules.get(event, result["rules"][event])
        if not isinstance(supplied, dict):
            raise TypeError("Ungültige Lichtregel.")
        brightness = supplied.get("brightness")
        transition = supplied.get("transition")
        if (
            not isinstance(brightness, (int, float))
            or not 0 <= brightness <= 100
            or not isinstance(transition, (int, float))
            or not 0 <= transition <= 120
        ):
            raise ValueError(
                "Helligkeit muss 0–100 % und Übergang 0–120 Sekunden betragen."
            )
        result["rules"][event] = {
            "enabled": supplied.get("enabled") is True,
            "brightness": round(brightness),
            "transition": transition,
        }
    if result["enabled"] and not (result["baseUrl"] and result["entityId"]):
        raise ValueError("Wähle zuerst Home-Assistant-Adresse und Licht-Entität.")
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class LightingController:
    def __init__(self, directory: Path | None = None):
        self.directory = directory or data_directory()
        self.filename = self.directory / "native-lighting.json"
        self.executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="lichtspiel-lighting"
        )
        self.config = self._load()
        self.previous = ("idle", -1)

    def _load(self) -> dict:
        source = self.filename
        migrating = False
        if not source.exists():
            source = self.directory / "lighting.json"
            migrating = source.exists()
        if not source.exists():
            return defaults()
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
            config = normalize_config(data)
            if migrating:
                # Electron's encrypted token is not readable from the OS keyring.
                config["enabled"] = False
            return config
        except (OSError, ValueError, TypeError):
            return defaults()

    def has_token(self) -> bool:
        try:
            origin = self.config["baseUrl"]
            return bool(origin and keyring.get_password(SERVICE, origin))
        except Exception:  # noqa: BLE001 - OS keyring backends raise different errors.
            return False

    def save(self, value: dict, token: str = "") -> dict:
        config = normalize_config(value)
        origin = config["baseUrl"]
        secret = token.strip()
        if secret and (
            len(secret) > 8192 or any(character.isspace() for character in secret)
        ):
            raise ValueError("Der Token enthält ungültige Zeichen oder ist zu lang.")
        if secret and not origin:
            raise ValueError("Gib zuerst die Home-Assistant-Adresse ein.")
        if secret:
            keyring.set_password(SERVICE, origin, secret)
        if config["enabled"] and not keyring.get_password(SERVICE, origin):
            raise ValueError(
                "Für diesen Server wird ein Token im System-Schlüsselbund benötigt."
            )
        atomic_json(self.filename, config)
        self.config = config
        return config

    def clear_token(self):
        origin = self.config["baseUrl"]
        if origin:
            try:
                keyring.delete_password(SERVICE, origin)
            except keyring.errors.PasswordDeleteError:
                pass
        self.config["enabled"] = False
        atomic_json(self.filename, self.config)

    def _request(self, method: str, endpoint: str, payload: dict | None = None):
        config = self.config
        origin = config["baseUrl"]
        if not origin:
            raise ValueError("Home-Assistant-Adresse fehlt.")
        token = keyring.get_password(SERVICE, origin)
        if not token:
            raise ValueError("Home-Assistant-Token fehlt. Bitte erneut eingeben.")
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            origin + endpoint,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with build_opener(NoRedirect).open(request, timeout=4) as response:
                return response.read(64 * 1024)
        except (HTTPError, URLError, TimeoutError) as error:
            raise RuntimeError(
                "Home Assistant ist nicht erreichbar oder hat den Befehl abgelehnt."
            ) from error

    def test_connection(self):
        self._request("GET", "/api/")
        return "Home Assistant antwortet."

    def apply(self, event: str):
        config = self.config
        if not config["enabled"] or event not in EVENTS:
            return None
        rule = config["rules"][event]
        if not rule["enabled"]:
            return None
        if rule["brightness"] == 0:
            service, payload = (
                "turn_off",
                {"entity_id": config["entityId"], "transition": rule["transition"]},
            )
        else:
            service, payload = (
                "turn_on",
                {
                    "entity_id": config["entityId"],
                    "brightness_pct": rule["brightness"],
                    "transition": rule["transition"],
                },
            )
        self._request("POST", f"/api/services/light/{service}", payload)
        return f"{LABELS[event]}: Licht auf {rule['brightness']} % gesetzt."

    def observe(self, state: dict, items: list[dict]) -> str | None:
        current = (state["status"], state["index"])
        previous_status, previous_index = self.previous
        self.previous = current
        status, index = current
        if not self.config["enabled"]:
            return None
        if status == "paused" and previous_status == "playing":
            return "pause"
        if status == "playing" and (
            previous_status in ("starting", "paused", "blackout")
            or index != previous_index
        ):
            category = items[index].get("category") if index < len(items) else ""
            return "feature" if category == "Film" else "preshow"
        if status in ("idle", "finished") and previous_status in (
            "playing",
            "paused",
            "blackout",
        ):
            return "end"
        return None

    def close(self):
        self.executor.shutdown(wait=False, cancel_futures=True)

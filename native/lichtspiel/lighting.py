"""Optional Home Assistant automation with OS credential storage."""

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

import keyring

from .model import atomic_json, data_directory

EVENTS = ("preshow", "feature", "pause", "blackout", "end")
LABELS = {
    "preshow": "Vorprogramm",
    "feature": "Hauptfilm",
    "pause": "Pause",
    "blackout": "Schwarzbild",
    "end": "Ende",
}
SERVICE = "Lichtspiel Home Assistant"


def defaults() -> dict:
    return {
        "enabled": False,
        "baseUrl": "",
        "entityIds": [],
        "rules": {
            event: {
                "enabled": event != "blackout",
                "mode": "brightness",
                "brightness": brightness,
                "transition": 3,
                "sceneId": "",
            }
            for event, brightness in (
                ("preshow", 20),
                ("feature", 0),
                ("pause", 40),
                ("blackout", 0),
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
    raw_entities = value.get("entityIds")
    if not raw_entities and value.get("entityId"):
        raw_entities = value.get("entityId", "")
    if isinstance(raw_entities, str):
        raw_entities = [
            part.strip() for part in raw_entities.split(",") if part.strip()
        ]
    if not isinstance(raw_entities, list) or len(raw_entities) > 20:
        raise ValueError("Wähle höchstens 20 Lampen oder Lichtgruppen.")
    entities = []
    for entity in raw_entities:
        if not isinstance(entity, str) or not re.fullmatch(
            r"light\.[a-z0-9_]+", entity
        ):
            raise ValueError("Wähle Licht-Entitäten wie light.kinosaal.")
        if entity not in entities:
            entities.append(entity)
    result["entityIds"] = entities
    supplied_rules = value.get("rules")
    if not isinstance(supplied_rules, dict):
        supplied_rules = {}
    for event in EVENTS:
        supplied = supplied_rules.get(event, result["rules"][event])
        if not isinstance(supplied, dict):
            raise TypeError("Ungültige Lichtregel.")
        brightness = supplied.get("brightness")
        transition = supplied.get("transition")
        mode = supplied.get("mode", "brightness")
        scene_id = supplied.get("sceneId") or ""
        if (
            not isinstance(brightness, (int, float))
            or not 0 <= brightness <= 100
            or not isinstance(transition, (int, float))
            or not 0 <= transition <= 120
        ):
            raise ValueError(
                "Helligkeit muss 0–100 % und Übergang 0–120 Sekunden betragen."
            )
        if mode not in ("brightness", "scene"):
            raise ValueError("Wähle Helligkeit oder Szene als Lichtaktion.")
        if scene_id and (
            not isinstance(scene_id, str)
            or not re.fullmatch(r"scene\.[a-z0-9_]+", scene_id)
        ):
            raise ValueError("Wähle eine Szene wie scene.filmstart.")
        if supplied.get("enabled") is True and mode == "scene" and not scene_id:
            raise ValueError(f"Für {LABELS[event]} fehlt eine Home-Assistant-Szene.")
        result["rules"][event] = {
            "enabled": supplied.get("enabled") is True,
            "mode": mode,
            "brightness": round(brightness),
            "transition": transition,
            "sceneId": scene_id,
        }
    if result["enabled"] and not result["baseUrl"]:
        raise ValueError("Gib zuerst die Home-Assistant-Adresse ein.")
    if (
        result["enabled"]
        and not entities
        and any(
            rule["enabled"] and rule["mode"] == "brightness"
            for rule in result["rules"].values()
        )
    ):
        raise ValueError(
            "Wähle für Helligkeitsregeln mindestens eine Lampe oder Lichtgruppe."
        )
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
        self.auto_ticket = 0

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
        self.auto_ticket += 1
        return config

    def clear_token(self):
        origin = self.config["baseUrl"]
        if origin:
            try:
                keyring.delete_password(SERVICE, origin)
            except keyring.errors.PasswordDeleteError:
                pass
        self.config["enabled"] = False
        self.auto_ticket += 1
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
        opener = build_opener(NoRedirect)
        attempts = 2 if method == "GET" else 1
        for attempt in range(attempts):
            try:
                with opener.open(request, timeout=4) as response:
                    data = response.read(8 * 1024 * 1024 + 1)
                    if len(data) > 8 * 1024 * 1024:
                        raise RuntimeError(
                            "Home Assistant hat eine zu große Antwort gesendet."
                        )
                    return data
            except HTTPError as error:
                if error.code in (429, 502, 503, 504) and attempt + 1 < attempts:
                    time.sleep(0.4)
                    continue
                if error.code in (401, 403):
                    raise RuntimeError(
                        "Home Assistant lehnt den Token ab. Bitte neu eingeben."
                    ) from error
                raise RuntimeError(
                    f"Home Assistant meldet HTTP {error.code}."
                ) from error
            except (URLError, TimeoutError) as error:
                if attempt + 1 < attempts:
                    time.sleep(0.4)
                    continue
                raise RuntimeError(
                    "Home Assistant ist nicht erreichbar. Prüfe Adresse und Netzwerk."
                ) from error
        raise RuntimeError("Home Assistant antwortet nicht.")

    def test_connection(self):
        self._request("GET", "/api/")
        targets = (
            set(self.config["entityIds"])
            if any(
                rule["enabled"] and rule["mode"] == "brightness"
                for rule in self.config["rules"].values()
            )
            else set()
        )
        targets.update(
            rule["sceneId"]
            for rule in self.config["rules"].values()
            if rule["enabled"] and rule["mode"] == "scene"
        )
        if not targets:
            return "Home Assistant antwortet. Noch keine Lichtziele konfiguriert."
        missing = sorted(targets.difference(self._all_states()))
        if missing:
            raise RuntimeError(
                f"Home Assistant kennt diese Ziele nicht: {', '.join(missing)}"
            )
        return f"Home Assistant antwortet · {len(targets)} Lichtziel(e) gefunden."

    def _all_states(self) -> dict[str, dict]:
        states = json.loads(self._request("GET", "/api/states"))
        if not isinstance(states, list):
            raise TypeError("Home Assistant hat keine gültige Geräteliste gesendet.")
        return {
            item["entity_id"]: item
            for item in states
            if isinstance(item, dict) and isinstance(item.get("entity_id"), str)
        }

    def discover_lights(self) -> list[tuple[str, str]]:
        discovered = []
        for entity_id, state in self._all_states().items():
            if not re.fullmatch(r"light\.[a-z0-9_]+", entity_id):
                continue
            attributes = state.get("attributes") or {}
            friendly = (
                attributes.get("friendly_name")
                if isinstance(attributes, dict)
                else None
            )
            name = friendly if isinstance(friendly, str) else entity_id
            if state.get("state") == "unavailable":
                name += " · nicht verfügbar"
            discovered.append((entity_id, name))
        return sorted(discovered, key=lambda item: item[1].casefold())

    def apply(self, event: str):
        config = self.config
        if not config["enabled"] or event not in EVENTS:
            return None
        rule = config["rules"][event]
        if not rule["enabled"]:
            return None
        if rule["mode"] == "scene":
            service = "scene/turn_on"
            payload = {"entity_id": rule["sceneId"], "transition": rule["transition"]}
        elif rule["brightness"] == 0:
            service, payload = (
                "light/turn_off",
                {"entity_id": config["entityIds"], "transition": rule["transition"]},
            )
        else:
            service, payload = (
                "light/turn_on",
                {
                    "entity_id": config["entityIds"],
                    "brightness_pct": rule["brightness"],
                    "transition": rule["transition"],
                },
            )
        self._request("POST", f"/api/services/{service}", payload)
        return (
            f"{LABELS[event]}: Szene {rule['sceneId']} aktiviert."
            if rule["mode"] == "scene"
            else f"{LABELS[event]}: Licht auf {rule['brightness']} % gesetzt."
        )

    def submit_auto(self, event: str):
        self.auto_ticket += 1
        ticket = self.auto_ticket

        def latest_only():
            if ticket != self.auto_ticket:
                return None
            return self.apply(event)

        return self.executor.submit(latest_only)

    def cancel_pending_auto(self):
        self.auto_ticket += 1

    def observe(self, state: dict, items: list[dict]) -> str | None:
        current = (state["status"], state["index"])
        previous_status, previous_index = self.previous
        self.previous = current
        status, index = current
        if not self.config["enabled"]:
            return None
        if status == "paused" and previous_status == "playing":
            return "pause"
        if status == "blackout" and previous_status in ("playing", "paused"):
            return "blackout" if self.config["rules"]["blackout"]["enabled"] else None
        if status == "playing" and (
            previous_status in ("starting", "paused", "blackout")
            or index != previous_index
        ):
            category = items[index].get("category") if index < len(items) else ""
            if previous_status == "playing" and previous_index < len(items):
                previous_category = items[previous_index].get("category")
                if (previous_category == "Film") == (category == "Film"):
                    return None
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

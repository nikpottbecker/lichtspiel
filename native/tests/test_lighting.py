import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError

from native.lichtspiel.lighting import (
    LightingController,
    defaults,
    normalize_config,
    normalize_url,
)


class LightingTests(unittest.TestCase):
    def test_url_does_not_accept_credentials_paths_or_redirect_targets(self):
        self.assertEqual(
            normalize_url("http://homeassistant.local:8123/"),
            "http://homeassistant.local:8123",
        )
        for value in (
            "https://user:pass@example.com",
            "https://example.com/api",
            "https://example.com?a=1",
        ):
            with self.assertRaises(ValueError):
                normalize_url(value)

    def test_token_stays_out_of_config_and_transitions_fire_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller = LightingController(Path(temporary))
            config = defaults()
            config.update(
                enabled=True, baseUrl="http://ha.local:8123", entityId="light.kinosaal"
            )
            with (
                mock.patch(
                    "native.lichtspiel.lighting.keyring.set_password"
                ) as set_secret,
                mock.patch(
                    "native.lichtspiel.lighting.keyring.get_password",
                    return_value="secret",
                ),
            ):
                controller.save(config, "secret")
                set_secret.assert_called_once()
                stored = (Path(temporary) / "native-lighting.json").read_text()
                self.assertNotIn("secret", stored)
                self.assertEqual(json.loads(stored)["baseUrl"], "http://ha.local:8123")
                items = [{"category": "Werbung"}, {"category": "Film"}]
                self.assertIsNone(
                    controller.observe({"status": "starting", "index": 0}, items)
                )
                self.assertEqual(
                    controller.observe({"status": "playing", "index": 0}, items),
                    "preshow",
                )
                self.assertIsNone(
                    controller.observe({"status": "playing", "index": 0}, items)
                )
                self.assertEqual(
                    controller.observe({"status": "paused", "index": 0}, items), "pause"
                )
                self.assertEqual(
                    controller.observe({"status": "playing", "index": 0}, items),
                    "preshow",
                )
                self.assertEqual(
                    controller.observe({"status": "playing", "index": 1}, items),
                    "feature",
                )
                self.assertIsNone(
                    controller.observe({"status": "error", "index": 1}, items)
                )
            controller.close()

    def test_electron_public_rules_migrate_disabled_until_native_token_is_set(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "lighting.json"
            data = defaults()
            data.update(
                enabled=True, baseUrl="http://ha.local:8123", entityId="light.kinosaal"
            )
            data["encryptedToken"] = "opaque-electron-token"
            source.write_text(json.dumps(data))
            controller = LightingController(Path(temporary))
            self.assertFalse(controller.config["enabled"])
            self.assertEqual(controller.config["rules"]["feature"]["brightness"], 0)
            controller.close()

    def test_multiple_lights_scenes_and_blackout_are_explicit(self):
        config = defaults()
        self.assertFalse(config["rules"]["blackout"]["enabled"])
        config.update(
            enabled=True,
            baseUrl="http://ha.local:8123",
            entityIds=["light.wand", "light.wand", "light.decke"],
        )
        config["rules"]["feature"].update(mode="scene", sceneId="scene.filmstart")
        normalized = normalize_config(config)
        self.assertEqual(normalized["entityIds"], ["light.wand", "light.decke"])
        with tempfile.TemporaryDirectory() as temporary:
            controller = LightingController(Path(temporary))
            controller.config = normalized
            with mock.patch.object(controller, "_request") as request:
                controller.apply("preshow")
                request.assert_called_with(
                    "POST",
                    "/api/services/light/turn_on",
                    {
                        "entity_id": ["light.wand", "light.decke"],
                        "brightness_pct": 20,
                        "transition": 3,
                    },
                )
                controller.apply("feature")
                request.assert_called_with(
                    "POST",
                    "/api/services/scene/turn_on",
                    {"entity_id": "scene.filmstart", "transition": 3},
                )
                self.assertIsNone(controller.apply("blackout"))
            controller.close()

    def test_adjacent_preshow_cues_do_not_repeat_lighting(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller = LightingController(Path(temporary))
            controller.config = normalize_config(
                {
                    **defaults(),
                    "enabled": True,
                    "baseUrl": "http://ha.local:8123",
                    "entityId": "light.saal",
                }
            )
            items = [
                {"category": "Werbung"},
                {"category": "Trailer"},
                {"category": "Film"},
            ]
            controller.observe({"status": "starting", "index": 0}, items)
            self.assertEqual(
                controller.observe({"status": "playing", "index": 0}, items), "preshow"
            )
            self.assertIsNone(
                controller.observe({"status": "playing", "index": 1}, items)
            )
            self.assertEqual(
                controller.observe({"status": "playing", "index": 2}, items), "feature"
            )
            self.assertIsNone(
                controller.observe({"status": "blackout", "index": 2}, items)
            )
            controller.close()

    def test_queued_automatic_light_actions_keep_only_latest_event(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller = LightingController(Path(temporary))
            gate = threading.Event()
            controller.executor.submit(lambda: gate.wait(2))
            calls = []
            with mock.patch.object(
                controller, "apply", side_effect=lambda event: calls.append(event)
            ):
                older = controller.submit_auto("preshow")
                newest = controller.submit_auto("feature")
                gate.set()
                older.result(timeout=2)
                newest.result(timeout=2)
            self.assertEqual(calls, ["feature"])
            controller.close()

    def test_light_discovery_is_read_only_and_filters_entities(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller = LightingController(Path(temporary))
            response = [
                {
                    "entity_id": "light.saal",
                    "attributes": {"friendly_name": "Kinosaal"},
                },
                {
                    "entity_id": "switch.steckdose",
                    "attributes": {"friendly_name": "Steckdose"},
                },
            ]
            with mock.patch.object(
                controller, "_request", return_value=json.dumps(response).encode()
            ) as request:
                self.assertEqual(
                    controller.discover_lights(), [("light.saal", "Kinosaal")]
                )
                request.assert_called_once_with("GET", "/api/states")
            controller.close()

    def test_connection_checks_configured_lights_and_scenes(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller = LightingController(Path(temporary))
            config = defaults()
            config.update(
                enabled=True, baseUrl="http://ha.local:8123", entityIds=["light.saal"]
            )
            config["rules"]["feature"].update(mode="scene", sceneId="scene.filmstart")
            controller.config = normalize_config(config)
            states = [
                {"entity_id": "light.saal", "attributes": {}},
                {"entity_id": "scene.filmstart", "attributes": {}},
            ]
            with mock.patch.object(
                controller, "_request", side_effect=[b"{}", json.dumps(states).encode()]
            ) as request:
                self.assertIn("2 Lichtziel", controller.test_connection())
                self.assertEqual(
                    request.call_args_list,
                    [mock.call("GET", "/api/"), mock.call("GET", "/api/states")],
                )
            with (
                mock.patch.object(controller, "_request", side_effect=[b"{}", b"[]"]),
                self.assertRaisesRegex(RuntimeError, "light.saal"),
            ):
                controller.test_connection()
            controller.close()

    def test_network_retry_is_bounded_and_auth_error_is_actionable(self):
        with tempfile.TemporaryDirectory() as temporary:
            controller = LightingController(Path(temporary))
            controller.config["baseUrl"] = "http://ha.local:8123"
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = b"ok"
            opener = mock.MagicMock()
            opener.open.side_effect = [URLError("offline"), response]
            with (
                mock.patch(
                    "native.lichtspiel.lighting.keyring.get_password",
                    return_value="token",
                ),
                mock.patch(
                    "native.lichtspiel.lighting.build_opener", return_value=opener
                ),
                mock.patch("native.lichtspiel.lighting.time.sleep"),
            ):
                self.assertEqual(controller._request("GET", "/api/"), b"ok")
            self.assertEqual(opener.open.call_count, 2)
            opener.open.reset_mock(side_effect=True)
            opener.open.side_effect = HTTPError(
                "http://ha.local", 401, "Unauthorized", {}, None
            )
            with (
                mock.patch(
                    "native.lichtspiel.lighting.keyring.get_password",
                    return_value="token",
                ),
                mock.patch(
                    "native.lichtspiel.lighting.build_opener", return_value=opener
                ),
                self.assertRaisesRegex(RuntimeError, "Token"),
            ):
                controller._request("GET", "/api/")
            self.assertEqual(opener.open.call_count, 1)
            opener.open.reset_mock(side_effect=True)
            opener.open.side_effect = URLError("connection lost")
            with (
                mock.patch(
                    "native.lichtspiel.lighting.keyring.get_password",
                    return_value="token",
                ),
                mock.patch(
                    "native.lichtspiel.lighting.build_opener", return_value=opener
                ),
                self.assertRaisesRegex(RuntimeError, "nicht erreichbar"),
            ):
                controller._request(
                    "POST", "/api/services/light/turn_on", {"entity_id": "light.saal"}
                )
            self.assertEqual(opener.open.call_count, 1)
            controller.close()

    def test_home_assistant_http_contract_with_local_server(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                pass

            def _respond(self, payload):
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                requests.append(
                    ("GET", self.path, None, self.headers.get("Authorization"))
                )
                if self.path == "/api/states":
                    self._respond(
                        [
                            {
                                "entity_id": "light.saal",
                                "attributes": {"friendly_name": "Saal"},
                            },
                            {
                                "entity_id": "light.wand",
                                "attributes": {"friendly_name": "Wand"},
                            },
                            {"entity_id": "scene.filmstart", "attributes": {}},
                        ]
                    )
                else:
                    self._respond({"message": "API running."})

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                requests.append(
                    ("POST", self.path, body, self.headers.get("Authorization"))
                )
                self._respond([])

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                controller = LightingController(Path(temporary))
                config = defaults()
                config.update(
                    enabled=True,
                    baseUrl=f"http://127.0.0.1:{server.server_port}",
                    entityIds=["light.saal", "light.wand"],
                )
                config["rules"]["feature"].update(
                    mode="scene", sceneId="scene.filmstart"
                )
                controller.config = normalize_config(config)
                with mock.patch(
                    "native.lichtspiel.lighting.keyring.get_password",
                    return_value="test-token",
                ):
                    self.assertIn("3 Lichtziel", controller.test_connection())
                    controller.apply("preshow")
                    controller.apply("feature")
                self.assertEqual(
                    [item[1] for item in requests],
                    [
                        "/api/",
                        "/api/states",
                        "/api/services/light/turn_on",
                        "/api/services/scene/turn_on",
                    ],
                )
                self.assertEqual(
                    requests[2][2]["entity_id"], ["light.saal", "light.wand"]
                )
                self.assertEqual(requests[3][2]["entity_id"], "scene.filmstart")
                self.assertTrue(
                    all(item[3] == "Bearer test-token" for item in requests)
                )
                controller.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

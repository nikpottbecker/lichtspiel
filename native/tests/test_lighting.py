import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from native.lichtspiel.lighting import LightingController, defaults, normalize_url


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

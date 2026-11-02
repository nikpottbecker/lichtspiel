import tempfile
import unittest
from pathlib import Path

from native.lichtspiel.model import empty_project
from native.lichtspiel.recovery import (
    checkpoint,
    clear_checkpoint,
    read_checkpoint,
    validate_checkpoint,
    write_checkpoint,
)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.project = empty_project()
        self.project["library"] = [
            {"id": "spot", "path": "/film/spot.mp4"},
            {"id": "film", "path": "/film/feature.mp4"},
        ]
        self.project["queue"] = ["spot", "film"]
        self.items = self.project["library"]

    def test_checkpoint_roundtrip_and_explicit_clear(self):
        state = {"index": 1, "position": 372.5}
        with tempfile.TemporaryDirectory() as temporary:
            filename = Path(temporary) / "show-recovery.json"
            point = checkpoint(self.project, self.items, state)
            write_checkpoint(filename, point)
            self.assertEqual(read_checkpoint(filename, self.project)["position"], 372.5)
            clear_checkpoint(filename)
            self.assertIsNone(read_checkpoint(filename, self.project))

    def test_modified_queue_and_paths_cannot_resume_wrong_media(self):
        point = checkpoint(self.project, self.items, {"index": 1, "position": 10})
        changed = {**self.project, "queue": ["film", "spot"]}
        with self.assertRaisesRegex(ValueError, "Ablauf"):
            validate_checkpoint(point, changed)
        changed = {
            **self.project,
            "library": [
                self.project["library"][0],
                {"id": "film", "path": "/elsewhere"},
            ],
        }
        with self.assertRaisesRegex(ValueError, "Mediendatei"):
            validate_checkpoint(point, changed)

    def test_invalid_position_is_rejected(self):
        point = checkpoint(self.project, self.items, {"index": 0, "position": 5})
        for invalid in (-1, float("nan"), True):
            with (
                self.subTest(invalid=invalid),
                self.assertRaisesRegex(ValueError, "Wiedergabeposition"),
            ):
                validate_checkpoint({**point, "position": invalid}, self.project)


if __name__ == "__main__":
    unittest.main()

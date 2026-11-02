import unittest

from native.lichtspiel.progress import clock, timing


class ProgressTests(unittest.TestCase):
    def test_clip_and_full_show_progress_include_previous_cues(self):
        items = [{"duration": 30}, {"duration": 90}, {"duration": 3600}]
        state = {"status": "playing", "index": 1, "position": 45, "duration": 90}
        result = timing(state, items)
        self.assertEqual(result["clip_remaining"], 45)
        self.assertEqual(result["elapsed"], 75)
        self.assertEqual(result["show_remaining"], 3645)
        self.assertEqual(result["clip_fraction"], 0.5)
        self.assertAlmostEqual(result["show_fraction"], 75 / 3720)
        self.assertEqual(clock(result["show_remaining"]), "1:00:45")

    def test_positions_are_clamped_and_finished_show_is_complete(self):
        items = [{"duration": 10}, {"duration": 20}]
        self.assertEqual(
            timing(
                {"status": "playing", "index": 0, "position": 100, "duration": 10},
                items,
            )["clip_fraction"],
            1,
        )
        result = timing(
            {"status": "finished", "index": 1, "position": 20, "duration": 20}, items
        )
        self.assertEqual(result["show_fraction"], 1)
        self.assertEqual(result["show_remaining"], 0)

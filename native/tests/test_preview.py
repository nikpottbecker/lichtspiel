import tempfile
import unittest
from pathlib import Path

from PySide6.QtGui import QImage

from native.lichtspiel.preview import read_preview_frame


class PreviewTests(unittest.TestCase):
    def test_large_frame_is_decoded_at_monitor_size_and_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            filename = Path(temporary) / "frame.jpg"
            source = QImage(3840, 2160, QImage.Format_RGB32)
            source.fill("#6c8f9f")
            self.assertTrue(source.save(str(filename)))
            frame = read_preview_frame(str(filename))
            self.assertLessEqual(frame.width(), 500)
            self.assertLessEqual(frame.height(), 300)
            self.assertFalse(filename.exists())


if __name__ == "__main__":
    unittest.main()

"""Decode projector snapshots at monitor size outside the Qt UI thread."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader


def read_preview_frame(filename: str) -> QImage:
    source = Path(filename)
    try:
        reader = QImageReader(str(source))
        reader.setAutoTransform(True)
        dimensions = reader.size()
        if dimensions.isValid():
            reader.setScaledSize(dimensions.scaled(QSize(500, 300), Qt.KeepAspectRatio))
        frame = reader.read()
        if frame.isNull():
            raise ValueError("Das Vorschaubild konnte nicht gelesen werden.")
        return frame
    finally:
        try:
            source.unlink(missing_ok=True)
        except OSError:
            # Windows may still hold the completed screenshot briefly.
            pass

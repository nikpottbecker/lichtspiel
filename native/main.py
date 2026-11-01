"""Lichtspiel native desktop entry point."""

import sys
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

# Also works when started directly from the repository.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lichtspiel.model import data_directory
from lichtspiel.window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Lichtspiel")
    directory = data_directory()
    directory.mkdir(parents=True, exist_ok=True)
    lock = QLockFile(str(directory / "native.lock"))
    if not lock.tryLock(100):
        QMessageBox.information(
            None, "Lichtspiel", "Die native Kinoregie ist bereits geöffnet."
        )
        return 1
    try:
        window = MainWindow()
    except (OSError, ValueError, TypeError) as error:
        QMessageBox.critical(None, "Lichtspiel", str(error))
        lock.unlock()
        return 1
    window.show()
    result = app.exec()
    lock.unlock()
    return result


if __name__ == "__main__":
    raise SystemExit(main())

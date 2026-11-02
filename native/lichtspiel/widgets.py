"""Small native widgets used by the control room."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy


class ElidedLabel(QLabel):
    """Keep long media titles on one line while preserving the full tooltip."""

    def __init__(self, text: str = "", kind: str = ""):
        super().__init__("")
        if kind:
            self.setObjectName(kind)
        self.setWordWrap(False)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.full_text = ""
        self.set_full_text(text)

    def set_full_text(self, text: str):
        self.full_text = text
        self.setToolTip(text)
        self._update_elision()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elision()

    def _update_elision(self):
        available = max(0, self.contentsRect().width())
        shortened = self.fontMetrics().elidedText(
            self.full_text, Qt.ElideRight, available
        )
        if shortened != self.text():
            super().setText(shortened)

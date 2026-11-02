"""Small native widgets used by the control room."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget


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


class PreviewFrame(QWidget):
    """Letterboxed monitor frame; painting never touches the projector process."""

    activated = Signal()

    def __init__(self):
        super().__init__()
        self.frame = QImage()
        self.caption = "Vorschau startet mit der Vorstellung"
        self.setMinimumSize(170, 90)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.setAccessibleName("Kontrollbild der Leinwand")

    def sizeHint(self):
        return QSize(220, 132)

    def mouseDoubleClickEvent(self, event):
        self.activated.emit()
        super().mouseDoubleClickEvent(event)

    def show_frame(self, frame: QImage):
        self.frame = frame
        self.update()

    def show_message(self, message: str, clear: bool = False):
        self.caption = message
        if clear:
            self.frame = QImage()
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#101213"))
        if self.frame.isNull():
            painter.setPen(QColor("#a3aaa8"))
            painter.drawText(
                self.rect().adjusted(10, 10, -10, -10),
                Qt.AlignCenter | Qt.TextWordWrap,
                self.caption,
            )
        else:
            size = self.frame.size().scaled(self.size(), Qt.KeepAspectRatio)
            x = (self.width() - size.width()) // 2
            y = (self.height() - size.height()) // 2
            painter.drawImage(
                x,
                y,
                self.frame.scaled(size, Qt.KeepAspectRatio, Qt.SmoothTransformation),
            )
        painter.setPen(QColor("#444a49"))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

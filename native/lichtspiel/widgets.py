"""Small native widgets used by the control room."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QLinearGradient,
    QPainter,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class AtmosphereHeader(QWidget):
    """Native, static cinematic header; never part of the projector output."""

    def __init__(self, eyebrow: str, title: str, description: str):
        super().__init__()
        self.setObjectName("atmosphereHeader")
        self.setFixedHeight(128)
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(26, 14, 26, 14)
        self.column.setSpacing(5)
        for copy, kind in (
            (eyebrow.upper(), "heroEyebrow"),
            (title, "heroTitle"),
            (description, "heroDescription"),
        ):
            item = QLabel(copy)
            item.setObjectName(kind)
            item.setWordWrap(True)
            item.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            self.column.addWidget(item)
            if kind == "heroDescription":
                self.description_label = item
        self.column.addStretch()

    def set_compact(self, compact: bool):
        self.setFixedHeight(82 if compact else 128)
        if compact:
            self.column.setContentsMargins(20, 8, 20, 8)
        else:
            self.column.setContentsMargins(26, 14, 26, 14)
        self.description_label.setVisible(not compact)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        base = QLinearGradient(0, 0, self.width(), self.height())
        base.setColorAt(0, QColor("#202020"))
        base.setColorAt(0.55, QColor("#171717"))
        base.setColorAt(1, QColor("#262626"))
        painter.setPen(QPen(QColor("#666666"), 1))
        painter.setBrush(base)
        painter.drawRoundedRect(rect, 18, 18)

        painter.save()
        painter.setClipRect(self.rect().adjusted(2, 2, -2, -2))
        glow = QRadialGradient(self.width() * 0.85, self.height() * 0.5, 250)
        glow.setColorAt(0, QColor(255, 255, 255, 55))
        glow.setColorAt(0.55, QColor(220, 220, 220, 22))
        glow.setColorAt(1, QColor(220, 220, 220, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(glow)
        painter.drawRect(self.rect())
        rim_light = QRadialGradient(self.width() * 0.97, self.height() * 0.05, 160)
        rim_light.setColorAt(0, QColor(255, 255, 255, 38))
        rim_light.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(rim_light)
        painter.drawRect(self.rect())
        painter.setPen(QPen(QColor(255, 255, 255, 27), 1))
        for offset in (0, 34, 68, 102):
            painter.drawLine(
                self.width() - 245 + offset,
                self.height(),
                self.width() - 90 + offset,
                0,
            )
        painter.restore()
        painter.setPen(QPen(QColor("#f2f2f2"), 3))
        painter.drawLine(27, self.height() - 2, 105, self.height() - 2)


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
        return QSize(195, 132)

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
        painter.fillRect(self.rect(), QColor("#080808"))
        if self.frame.isNull():
            painter.setPen(QColor("#aaaaaa"))
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
        painter.setPen(QColor("#4b4b4b"))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1))

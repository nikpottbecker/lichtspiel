"""Local 2D room plan for Home Assistant light positions."""

import json
import math
import re
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
)

from .model import atomic_json

ROOM_LEFT = 40
ROOM_TOP = 40
ROOM_WIDTH = 560
ROOM_HEIGHT = 280


def empty_plan() -> dict:
    return {"version": 1, "markers": []}


def validate_plan(value: dict) -> dict:
    if not isinstance(value, dict) or value.get("version") != 1:
        raise ValueError("Der Raumplan hat ein unbekanntes Format.")
    markers = value.get("markers")
    if not isinstance(markers, list) or len(markers) > 20:
        raise ValueError("Der Raumplan enthält zu viele oder ungültige Lampen.")
    seen = set()
    cleaned = []
    for item in markers:
        if not isinstance(item, dict):
            raise TypeError("Der Raumplan enthält eine ungültige Markierung.")
        entity_id = item.get("entityId")
        x, y = item.get("x"), item.get("y")
        if (
            not isinstance(entity_id, str)
            or not re.fullmatch(r"light\.[a-z0-9_]+", entity_id)
            or entity_id in seen
            or type(x) not in (int, float)
            or type(y) not in (int, float)
            or not math.isfinite(x)
            or not math.isfinite(y)
            or not 0 <= x <= 1
            or not 0 <= y <= 1
        ):
            raise ValueError("Der Raumplan enthält eine ungültige Markierung.")
        seen.add(entity_id)
        cleaned.append({"entityId": entity_id, "x": float(x), "y": float(y)})
    return {"version": 1, "markers": cleaned}


def load_plan(filename: Path) -> dict:
    try:
        raw = json.loads(filename.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return empty_plan()
    except (OSError, ValueError) as error:
        raise ValueError("Der Raumplan konnte nicht gelesen werden.") from error
    return validate_plan(raw)


def save_plan(filename: Path, plan: dict):
    atomic_json(filename, validate_plan(plan))


class LightMarker(QGraphicsEllipseItem):
    def __init__(self, entity_id: str, moved):
        super().__init__(-12, -12, 24, 24)
        self.entity_id = entity_id
        self.moved = moved
        self.press_position = self.pos()
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setZValue(2)
        self.setToolTip(entity_id)
        short_name = entity_id.removeprefix("light.")
        if len(short_name) > 18:
            short_name = short_name[:17] + "…"
        self.label = QGraphicsSimpleTextItem(short_name, self)
        self.label.setFont(QFont("Segoe UI", 9))
        self.label.setPos(17, -9)

    def set_active(self, active: bool):
        color = QColor("#b391ff") if active else QColor("#777583")
        self.setBrush(QBrush(color))
        self.setPen(QPen(QColor("#17141f"), 2))
        self.label.setBrush(QBrush(QColor("#f2eefb") if active else QColor("#aaa8b5")))

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            point = value
            point.setX(min(ROOM_LEFT + ROOM_WIDTH, max(ROOM_LEFT, point.x())))
            point.setY(min(ROOM_TOP + ROOM_HEIGHT, max(ROOM_TOP, point.y())))
            return point
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.pos() != self.press_position:
            self.moved(self.entity_id)

    def mousePressEvent(self, event):
        self.press_position = self.pos()
        super().mousePressEvent(event)


class RoomPlan(QGraphicsView):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(0, 0, 640, 360, self))
        self.setFrameShape(QFrame.NoFrame)
        self.setMinimumHeight(300)
        self.setAccessibleName("2D-Raumplan der Kinolichter")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor("#171720")))
        self.markers = {}
        self.editable = True
        self.background_item = None
        self._draw_room()

    def set_background(self, image: QImage | None):
        if self.background_item is not None:
            self.scene().removeItem(self.background_item)
            self.background_item = None
        if image is None or image.isNull():
            return
        shown = image.scaled(
            ROOM_WIDTH,
            ROOM_HEIGHT,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation,
        )
        x = (shown.width() - ROOM_WIDTH) // 2
        y = (shown.height() - ROOM_HEIGHT) // 2
        cropped = shown.copy(x, y, ROOM_WIDTH, ROOM_HEIGHT)
        self.background_item = self.scene().addPixmap(QPixmap.fromImage(cropped))
        self.background_item.setPos(ROOM_LEFT, ROOM_TOP)
        self.background_item.setOpacity(0.45)
        self.background_item.setZValue(-1)

    def _draw_room(self):
        grid = QPen(QColor("#292936"), 1)
        for x in range(ROOM_LEFT + 40, ROOM_LEFT + ROOM_WIDTH, 40):
            self.scene().addLine(x, ROOM_TOP, x, ROOM_TOP + ROOM_HEIGHT, grid)
        for y in range(ROOM_TOP + 40, ROOM_TOP + ROOM_HEIGHT, 40):
            self.scene().addLine(ROOM_LEFT, y, ROOM_LEFT + ROOM_WIDTH, y, grid)
        wall = QPen(QColor("#6e6a7c"), 3)
        self.scene().addRect(ROOM_LEFT, ROOM_TOP, ROOM_WIDTH, ROOM_HEIGHT, wall)
        self.scene().addRect(
            220, 27, 200, 8, QPen(QColor("#ad83f4")), QBrush(QColor("#ad83f4"))
        )
        screen = self.scene().addText("LEINWAND", QFont("Segoe UI", 8))
        screen.setDefaultTextColor(QColor("#ad83f4"))
        screen.setPos(290, 5)
        entrance = self.scene().addText("EINGANG", QFont("Segoe UI", 8))
        entrance.setDefaultTextColor(QColor("#aaa8b5"))
        entrance.setPos(288, 326)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def set_editable(self, editable: bool):
        self.editable = editable
        for marker in self.markers.values():
            marker.setFlag(QGraphicsItem.ItemIsMovable, editable)

    def set_plan(self, plan: dict, active_entities: list[str]):
        for marker in self.markers.values():
            self.scene().removeItem(marker)
        self.markers.clear()
        for item in validate_plan(plan)["markers"]:
            self._create_marker(item, item["entityId"] in active_entities)

    def _create_marker(self, item: dict, active: bool):
        entity_id = item["entityId"]
        marker = LightMarker(entity_id, lambda _id: self.changed.emit())
        marker.set_active(active)
        marker.setFlag(QGraphicsItem.ItemIsMovable, self.editable)
        self.scene().addItem(marker)
        marker.setPos(
            ROOM_LEFT + item["x"] * ROOM_WIDTH,
            ROOM_TOP + item["y"] * ROOM_HEIGHT,
        )
        self.markers[entity_id] = marker
        return marker

    def add_light(self, entity_id: str, active_entities: list[str]) -> bool:
        if (
            not re.fullmatch(r"light\.[a-z0-9_]+", entity_id)
            or entity_id in self.markers
            or len(self.markers) >= 20
        ):
            return False
        index = len(self.markers)
        self._create_marker(
            {
                "entityId": entity_id,
                "x": 0.18 + (index % 4) * 0.21,
                "y": 0.2 + (index // 4) * 0.15,
            },
            entity_id in active_entities,
        )
        self.changed.emit()
        return True

    def remove_selected(self) -> bool:
        selected = [
            item
            for item in self.scene().selectedItems()
            if isinstance(item, LightMarker)
        ]
        if not selected:
            return False
        marker = selected[0]
        self.scene().removeItem(marker)
        del self.markers[marker.entity_id]
        self.changed.emit()
        return True

    def keyPressEvent(self, event):
        if self.editable:
            if event.key() == Qt.Key_Delete and self.remove_selected():
                return
            selected = [
                item
                for item in self.scene().selectedItems()
                if isinstance(item, LightMarker)
            ]
            if selected:
                step = 28 if event.modifiers() & Qt.ShiftModifier else 7
                offsets = {
                    Qt.Key_Left: (-step, 0),
                    Qt.Key_Right: (step, 0),
                    Qt.Key_Up: (0, -step),
                    Qt.Key_Down: (0, step),
                }
                if event.key() in offsets:
                    x, y = offsets[event.key()]
                    selected[0].setPos(
                        selected[0].pos().x() + x, selected[0].pos().y() + y
                    )
                    self.changed.emit()
                    return
        super().keyPressEvent(event)

    def current_plan(self) -> dict:
        return {
            "version": 1,
            "markers": [
                {
                    "entityId": entity_id,
                    "x": round((marker.pos().x() - ROOM_LEFT) / ROOM_WIDTH, 4),
                    "y": round((marker.pos().y() - ROOM_TOP) / ROOM_HEIGHT, 4),
                }
                for entity_id, marker in self.markers.items()
            ],
        }

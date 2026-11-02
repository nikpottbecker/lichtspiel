import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGraphicsItem

from native.lichtspiel.room_plan import (
    ROOM_LEFT,
    ROOM_TOP,
    RoomPlan,
    empty_plan,
    load_plan,
    save_plan,
    validate_plan,
)


class RoomPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_positions_survive_roundtrip_and_invalid_targets_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            filename = Path(temporary) / "room-plan.json"
            self.assertEqual(load_plan(filename), empty_plan())
            plan = {
                "version": 1,
                "markers": [{"entityId": "light.decke", "x": 0.3, "y": 0.7}],
            }
            save_plan(filename, plan)
            self.assertEqual(load_plan(filename), plan)
            with self.assertRaisesRegex(ValueError, "ungültige Markierung"):
                validate_plan(
                    {
                        "version": 1,
                        "markers": [{"entityId": "switch.anderes", "x": 0.3, "y": 0.7}],
                    }
                )

    def test_drag_positions_are_bounded_and_editing_can_be_disabled(self):
        plan = RoomPlan()
        self.assertTrue(plan.add_light("light.decke", ["light.decke"]))
        marker = plan.markers["light.decke"]
        marker.setPos(QPointF(-500, 999))
        self.assertEqual(marker.pos().x(), ROOM_LEFT)
        self.assertEqual(marker.pos().y(), ROOM_TOP + 280)
        self.assertEqual(plan.current_plan()["markers"][0]["x"], 0)
        plan.set_editable(False)
        self.assertFalse(marker.flags() & QGraphicsItem.ItemIsMovable)
        plan.set_background(QImage(1280, 720, QImage.Format_RGB32))
        self.assertIsNotNone(plan.background_item)
        marker.setSelected(True)
        self.assertTrue(plan.remove_selected())
        self.assertEqual(plan.current_plan()["markers"], [])
        plan.close()

    def test_selected_light_moves_by_keyboard_and_can_be_removed(self):
        plan = RoomPlan()
        plan.show()
        self.app.processEvents()
        plan.add_light("light.wand", ["light.wand"])
        marker = plan.markers["light.wand"]
        marker.setSelected(True)
        before = marker.pos().x()
        QTest.keyClick(plan, Qt.Key_Right)
        self.assertGreater(marker.pos().x(), before)
        QTest.keyClick(plan, Qt.Key_Delete)
        self.assertEqual(plan.markers, {})
        plan.close()


if __name__ == "__main__":
    unittest.main()

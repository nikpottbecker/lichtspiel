import json
import os
import tempfile
import unittest
from concurrent.futures import Future
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QScrollArea

from native.lichtspiel.model import (
    empty_project,
    load_project,
    preflight,
    queued_media,
    save_project,
)
from native.lichtspiel.player import display_args, test_pattern_path
from native.lichtspiel.recovery import checkpoint, write_checkpoint
from native.lichtspiel.room_plan import load_plan
from native.lichtspiel.widgets import ElidedLabel
from native.lichtspiel.window import MainWindow


class NativeModelTests(unittest.TestCase):
    def test_project_roundtrip_keeps_duplicate_cues_and_real_file_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            filename = directory / "short.mp4"
            filename.write_bytes(b"sample")
            project = empty_project()
            project["library"].append(
                {
                    "id": "film",
                    "name": "Short",
                    "path": str(filename),
                    "duration": 90,
                    "category": "Film",
                    "size": 6,
                }
            )
            project["queue"] = ["film", "film"]
            save_project(project, directory)
            restored = load_project(directory)
            self.assertEqual(restored["queue"], ["film", "film"])
            self.assertEqual(len(queued_media(restored)), 2)
            self.assertEqual(len(preflight(restored)), 2)
            filename.unlink()
            with self.assertRaisesRegex(ValueError, "fehlt"):
                preflight(restored)

    def test_preflight_rejects_invalid_duration_and_dangling_queue(self):
        with tempfile.TemporaryDirectory() as temporary:
            filename = Path(temporary) / "clip.mp4"
            filename.write_bytes(b"sample")
            project = empty_project()
            project["library"] = [
                {"id": "clip", "path": str(filename), "duration": float("nan")}
            ]
            project["queue"] = ["clip"]
            with self.assertRaisesRegex(ValueError, "Laufzeit"):
                preflight(project)
            project["queue"] = ["missing"]
            with self.assertRaisesRegex(ValueError, "fehlende Medieneinträge"):
                preflight(project)

    def test_projection_card_is_bundled_and_display_arguments_are_shared(self):
        self.assertTrue(Path(test_pattern_path()).is_file())
        self.assertEqual(display_args(2), ["--screen=2", "--fs-screen=2"])
        with self.assertRaisesRegex(ValueError, "Ausgabebildschirm"):
            display_args(-1)


class NativeWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_four_qt_pages_open_without_web_renderer(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            self.assertEqual(window.pages.count(), 4)
            self.assertEqual(window.pages.currentIndex(), 2)
            window.close()

    def test_onboarding_requires_visible_projection_check_and_valid_media(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            media = directory / "clip.mp4"
            media.write_bytes(b"video")
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project",
                    return_value=empty_project(),
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory", return_value=directory
                ),
                mock.patch.object(MainWindow, "_detect_mpv"),
            ):
                window = MainWindow()
                self.assertEqual(window.pages.currentIndex(), 2)
                self.assertEqual(window._onboarding_step(), "player")
                window.mpv = "/test/mpv"
                window._update_onboarding()
                self.assertEqual(window._onboarding_step(), "display")
                window.display_combo.setCurrentIndex(1)
                self.assertEqual(window._onboarding_step(), "projection")
                window.projection_test_screen = window.native_display_id
                window._projection_finished(True, "")
                self.assertTrue(window.projection_confirm.isEnabled())
                self.assertEqual(window._onboarding_step(), "projection")
                window.projection_confirm.setChecked(True)
                self.assertEqual(window._onboarding_step(), "media")
                window.project["library"] = [
                    {
                        "id": "clip",
                        "name": "Clip",
                        "path": str(media),
                        "duration": 10,
                        "category": "Film",
                    }
                ]
                window.project["queue"] = ["clip"]
                window._refresh_lists()
                self.assertEqual(window._onboarding_step(), "ready")
                media.unlink()
                window._finish_onboarding()
                with self.assertRaises(ValueError):
                    window.jobs[-1][0].result(timeout=2)
                window._poll_jobs()
                self.assertFalse(window.native_onboarded)
                self.assertIn("fehlt", window.onboarding_description.text())
                media.write_bytes(b"video")
                window._finish_onboarding()
                window.jobs[-1][0].result(timeout=2)
                window._poll_jobs()
                self.assertTrue(window.native_onboarded)
                self.assertEqual(window.pages.currentIndex(), 0)
                self.assertTrue(
                    json.loads((directory / "settings.json").read_text())[
                        "nativeOnboarded"
                    ]
                )
                self.assertFalse(window.project["onboarded"])
                window.close()

    def test_onboarding_rechecks_projection_when_display_changes(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            mock.patch(
                "native.lichtspiel.window.load_project", return_value=empty_project()
            ),
            mock.patch(
                "native.lichtspiel.window.data_directory",
                return_value=Path(temporary),
            ),
            mock.patch.object(MainWindow, "_detect_mpv"),
        ):
            window = MainWindow()
            window.mpv = "/test/mpv"
            window.display_combo.setCurrentIndex(1)
            window.projection_test_screen = window.native_display_id
            window._projection_finished(True, "")
            window.projection_confirm.setChecked(True)
            window.display_combo.setCurrentIndex(0)
            self.assertFalse(window.projection_confirm.isChecked())
            self.assertFalse(window.projection_confirm.isEnabled())
            self.assertEqual(window._onboarding_step(), "display")
            window.close()

    def test_short_page_does_not_inherit_lighting_scrollbar(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.resize(1260, 900)
            window.show()
            window._set_page(1)
            self.app.processEvents()
            library_scroller = window.pages.currentWidget()
            self.assertIsInstance(library_scroller, QScrollArea)
            self.assertEqual(library_scroller.verticalScrollBar().maximum(), 0)
            window._set_page(3)
            window._set_light_section(2)
            self.app.processEvents()
            self.assertGreater(
                window.pages.currentWidget().verticalScrollBar().maximum(), 0
            )
            window.close()

    def test_lighting_sections_keep_plan_and_rules_one_click_away(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.resize(1260, 900)
            window.show()
            window._set_page(3)
            window.light_section_buttons[1].click()
            self.app.processEvents()
            self.assertTrue(window.room_plan.isVisible())
            self.assertFalse(window.light_url.isVisible())
            self.assertTrue(window.light_section_buttons[1].isChecked())
            window.light_section_buttons[2].click()
            self.app.processEvents()
            self.assertFalse(window.room_plan.isVisible())
            self.assertTrue(next(iter(window.light_rules.values()))[0].isVisible())
            window.close()

    def test_small_window_compacts_heading_and_keeps_plan_accessible(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.resize(900, 640)
            window.show()
            window._set_page(3)
            window._set_light_section(1)
            self.app.processEvents()
            self.assertEqual(window.page_headers[3].height(), 82)
            self.assertFalse(window.page_headers[3].description_label.isVisible())
            self.assertTrue(window.room_plan.isVisible())
            window.resize(1260, 900)
            self.app.processEvents()
            self.assertEqual(window.page_headers[3].height(), 128)
            self.assertTrue(window.page_headers[3].description_label.isVisible())
            window.close()

    def test_live_controls_show_clip_and_show_progress(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.player.items = [
                {"name": "Trailer", "category": "Trailer", "duration": 30},
                {"name": "Hauptfilm", "category": "Film", "duration": 90},
            ]
            window._player_state(
                {"status": "playing", "index": 1, "position": 45, "duration": 90}
            )
            self.assertEqual(window.clip_progress.value(), 500)
            self.assertEqual(window.show_progress.value(), 625)
            self.assertIn("Hauptfilm", window.current_cue.text())
            self.assertIn("Noch 00:45", window.clip_remaining.text())
            window.player.state["status"] = "idle"
            window.close()

    def test_live_regie_prioritizes_rundown_and_restores_preparation(self):
        project = empty_project()
        project["library"] = [
            {"id": "a", "name": "Trailer", "category": "Trailer", "duration": 30},
            {"id": "b", "name": "Hauptfilm", "category": "Film", "duration": 90},
        ]
        project["queue"] = ["a", "b"]
        with mock.patch("native.lichtspiel.window.load_project", return_value=project):
            window = MainWindow()
            window.resize(900, 640)
            window.show()
            window._set_page(0)
            window.player.items = project["library"]
            live = {"status": "playing", "index": 1, "position": 12, "duration": 90}
            window.player.state = live
            window._player_state(live)
            self.app.processEvents()
            self.assertFalse(window.page_headers[0].isVisible())
            self.assertFalse(window.stage_card.isVisible())
            self.assertFalse(window.schedule_surface.isVisible())
            self.assertTrue(window.queue_list.isVisible())
            self.assertTrue(window.preview_frame.isVisible())
            self.assertTrue(window.stop_button.isVisible())
            self.assertTrue(window.queue_list.item(0).text().startswith("✓"))
            self.assertTrue(window.queue_list.item(1).text().startswith("→"))
            self.assertEqual(window.workbench_surface.height(), 205)
            idle = {"status": "idle", "index": 0, "position": 0, "duration": 0}
            window.player.state = idle
            window._player_state(idle)
            self.app.processEvents()
            self.assertTrue(window.page_headers[0].isVisible())
            self.assertTrue(window.stage_card.isVisible())
            self.assertTrue(window.schedule_surface.isVisible())
            self.assertEqual(window.workbench_surface.height(), 230)
            window.close()

    def test_next_cue_stays_inside_live_card_at_minimum_width(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.resize(900, 640)
            window.show()
            window._set_page(0)
            self.app.processEvents()
            card = window.next_cue.parentWidget()
            self.assertLessEqual(
                window.next_cue.geometry().right(), card.contentsRect().right()
            )
            self.assertLessEqual(
                window.stage_preview.geometry().right(), window.pages.width()
            )
            window.close()

    def test_live_transport_remains_visible_on_every_page_during_show(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = empty_project()
            project["library"] = [
                {
                    "id": "film",
                    "name": "Hauptfilm",
                    "path": "/tmp/film.mp4",
                    "category": "Film",
                    "duration": 120,
                }
            ]
            project["queue"] = ["film"]
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project", return_value=project
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory",
                    return_value=Path(temporary),
                ),
            ):
                window = MainWindow()
                window.resize(900, 640)
                window.show()
                window._set_page(3)
                self.app.processEvents()
                self.assertFalse(window.transport_surface.isVisible())
                window.player.items = project["library"]
                state = {
                    "status": "playing",
                    "index": 0,
                    "position": 35,
                    "duration": 120,
                }
                window.player.state = state
                window._player_state(state)
                self.app.processEvents()
                self.assertTrue(window.transport_surface.isVisible())
                for page in range(window.pages.count()):
                    window._set_page(page)
                    self.app.processEvents()
                    self.assertTrue(window.transport_surface.isVisible())
                    self.assertTrue(window.stop_button.isVisible())
                    self.assertLessEqual(
                        window.transport_surface.geometry().bottom(),
                        window.content_layout.parentWidget().height(),
                    )
                window.player.stop()
                window.jobs[-1][0].result(timeout=2)
                window._set_page(3)
                self.app.processEvents()
                self.assertFalse(window.transport_surface.isVisible())
                window.close()

    def test_light_network_error_does_not_open_modal_over_show_controls(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            with mock.patch("native.lichtspiel.window.QMessageBox.warning") as warning:
                failed = Future()
                failed.set_exception(RuntimeError("Verbindung unterbrochen"))
                window._queue_light_job(failed, lambda _result: None)
                window._poll_jobs()
                warning.assert_not_called()
            self.assertIn("Verbindung unterbrochen", window.status.text())
            window.close()

    def test_unsaved_light_target_is_not_used_for_read_only_connection_test(self):
        with mock.patch(
            "native.lichtspiel.window.load_project", return_value=empty_project()
        ):
            window = MainWindow()
            window.light_entity.setText("light.neue_lampe")
            with mock.patch.object(window.lighting.executor, "submit") as submit:
                window._test_lighting_connection()
                submit.assert_not_called()
            self.assertIn("zuerst", window.light_feedback.text())
            window.close()

    def test_long_media_title_stays_on_one_line(self):
        full = "Ein sehr langer Filmname mit vielen weiteren Wörtern"
        title = ElidedLabel(full)
        title.resize(110, 25)
        title.show()
        self.app.processEvents()
        self.assertTrue(title.text().endswith("…"))
        self.assertEqual(title.toolTip(), full)
        title.close()

    def test_preview_decodes_a_frame_without_blocking_the_control_room(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            filename = directory / "frame.jpg"
            frame = QImage(640, 360, QImage.Format_RGB32)
            frame.fill("#496c78")
            self.assertTrue(frame.save(str(filename)))
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project",
                    return_value=empty_project(),
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory", return_value=directory
                ),
            ):
                window = MainWindow()
                window.jobs.clear()
                window.player.state["status"] = "playing"
                window._preview_frame_ready(str(filename))
                self.assertTrue(window.preview_loading)
                window.jobs[-1][0].result(timeout=2)
                window._poll_jobs()
                self.assertFalse(window.preview_frame.frame.isNull())
                self.assertFalse(window.stage_preview.frame.isNull())
                self.assertFalse(filename.exists())
                window._show_preview_dialog()
                self.assertFalse(window.preview_dialog.isModal())
                window.player.state["status"] = "idle"
                window.close()

    def test_light_plan_saves_markers_and_local_floorplan(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "my-room.jpg"
            picture = QImage(1200, 800, QImage.Format_RGB32)
            picture.fill("#f2f0e8")
            self.assertTrue(picture.save(str(source)))
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project",
                    return_value=empty_project(),
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory", return_value=directory
                ),
            ):
                window = MainWindow()
                window.lighting.config["entityIds"] = ["light.decke"]
                window._refresh_lighting()
                window.plan_entity.setCurrentIndex(
                    window.plan_entity.findData("light.decke")
                )
                with mock.patch.object(window.lighting.executor, "submit") as submit:
                    window._add_plan_light()
                    submit.assert_not_called()
                self.assertEqual(
                    load_plan(directory / "room-plan.json")["markers"][0]["entityId"],
                    "light.decke",
                )
                with mock.patch(
                    "native.lichtspiel.window.QFileDialog.getOpenFileName",
                    return_value=(str(source), ""),
                ):
                    window._choose_room_background()
                self.assertTrue((directory / "room-background.png").exists())
                self.assertIsNotNone(window.room_plan.background_item)
                window._load_room_background()
                self.assertIsNotNone(window.room_plan.background_item)
                window._clear_room_background()
                self.assertFalse((directory / "room-background.png").exists())
                window.room_plan.markers["light.decke"].setSelected(True)
                window._remove_plan_light()
                self.assertEqual(load_plan(directory / "room-plan.json")["markers"], [])
                window.close()

    def test_preview_frequency_can_be_disabled_without_stopping_playback(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project",
                    return_value=empty_project(),
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory", return_value=directory
                ),
            ):
                window = MainWindow()
                window.preview_interval_combo.setCurrentIndex(
                    window.preview_interval_combo.findData(0)
                )
                self.assertFalse(window.preview_timer.isActive())
                self.assertIn("AUS", window.preview_caption.text())
                self.assertEqual(
                    json.loads((directory / "settings.json").read_text())[
                        "previewIntervalMs"
                    ],
                    0,
                )
                window.preview_interval_combo.setCurrentIndex(
                    window.preview_interval_combo.findData(500)
                )
                self.assertTrue(window.preview_timer.isActive())
                self.assertEqual(window.preview_timer.interval(), 500)
                window.close()

    def test_restart_point_requires_explicit_resume_and_preflight(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            media = directory / "film.mp4"
            media.write_bytes(b"sample")
            project = empty_project()
            project["library"] = [
                {
                    "id": "film",
                    "name": "Hauptfilm",
                    "path": str(media),
                    "category": "Film",
                    "duration": 120,
                    "size": 6,
                }
            ]
            project["queue"] = ["film"]
            write_checkpoint(
                directory / "show-recovery.json",
                checkpoint(project, project["library"], {"index": 0, "position": 40}),
            )
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project", return_value=project
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory", return_value=directory
                ),
            ):
                window = MainWindow()
                window.mpv = "/fake/mpv"
                window._set_page(0)
                self.assertTrue(window.recovery_card.isVisible() is False)
                window.show()
                self.app.processEvents()
                self.assertTrue(window.recovery_card.isVisible())
                self.assertEqual(window.player.state["status"], "idle")
                self.assertFalse(window.start_button.isEnabled())
                self.assertFalse(window.schedule_button.isEnabled())
                window.jobs.clear()
                window.mpv = "/fake/mpv"
                completed = Future()
                completed.set_result(project["library"])
                with (
                    mock.patch.object(window, "_selected_screen_index", return_value=0),
                    mock.patch.object(
                        window.executor, "submit", return_value=completed
                    ),
                    mock.patch.object(window.player, "start") as start,
                ):
                    window._resume_recovery()
                    start.assert_not_called()
                    window._poll_jobs()
                    start.assert_called_once_with(
                        "/fake/mpv", project["library"], 0, "auto", 0, 40.0
                    )
                window._discard_recovery()
                self.assertTrue(window.start_button.isEnabled())
                window.jobs[-1][0].result(timeout=2)
                self.assertFalse((directory / "show-recovery.json").exists())
                window.close()

    def test_active_show_saves_restart_point_and_clean_stop_removes_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            project = empty_project()
            project["library"] = [
                {"id": "clip", "name": "Clip", "path": "/tmp/clip.mp4", "duration": 80}
            ]
            project["queue"] = ["clip"]
            with (
                mock.patch(
                    "native.lichtspiel.window.load_project", return_value=project
                ),
                mock.patch(
                    "native.lichtspiel.window.data_directory", return_value=directory
                ),
            ):
                window = MainWindow()
                window.player.items = project["library"]
                window._player_state(
                    {"status": "playing", "index": 0, "position": 24, "duration": 80}
                )
                window.jobs[-1][0].result(timeout=2)
                self.assertTrue((directory / "show-recovery.json").exists())
                window._player_state(
                    {"status": "idle", "index": 0, "position": 0, "duration": 0}
                )
                window.jobs[-1][0].result(timeout=2)
                self.assertFalse((directory / "show-recovery.json").exists())
                window._player_state(
                    {"status": "playing", "index": 0, "position": 30, "duration": 80}
                )
                window._player_state(
                    {"status": "idle", "index": 0, "position": 0, "duration": 0}
                )
                window.jobs[-1][0].result(timeout=2)
                self.assertFalse((directory / "show-recovery.json").exists())
                window.close()


if __name__ == "__main__":
    unittest.main()

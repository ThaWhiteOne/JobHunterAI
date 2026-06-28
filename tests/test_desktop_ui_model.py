import os
import tempfile
import unittest
from pathlib import Path

from desktop_ui_model import (
    DesktopSettings,
    actions_by_category,
    apply_prep_command,
    build_output_snapshot,
    command_text,
    desktop_actions,
    latest_existing_artifact,
    pipeline_command,
    read_preview_text,
)


class DesktopUiModelTests(unittest.TestCase):
    def test_pipeline_command_uses_selected_job_and_output_paths(self) -> None:
        settings = DesktopSettings(
            job_path=Path("jobs/support.txt"),
            output_dir=Path("outputs/support"),
            use_ai=True,
            use_ai_review=True,
        )

        command = pipeline_command(settings)

        self.assertEqual(command[0], "pipeline.py")
        self.assertIn(str(Path("jobs/support.txt")), command)
        self.assertIn(str(Path("outputs/support")), command)
        self.assertIn("--ai", command)
        self.assertIn("--ai-review", command)

    def test_apply_prep_command_can_enable_browser_opening(self) -> None:
        settings = DesktopSettings(
            job_path=Path("jobs/support.txt"),
            output_dir=Path("outputs/support"),
            answers_path=Path("profiles/application_answers.md"),
            open_browser=True,
        )

        command = apply_prep_command(settings)

        self.assertEqual(command[0], "apply_prep_pipeline.py")
        self.assertIn("--answers", command)
        self.assertIn("--open-browser", command)

    def test_desktop_actions_include_core_sidebar_workflows(self) -> None:
        actions = desktop_actions(DesktopSettings())
        labels = [action.label for action in actions]

        self.assertIn("Generate Package", labels)
        self.assertIn("Run Apply Prep", labels)
        self.assertIn("Browser Review", labels)
        self.assertIn("Refresh Status", labels)

    def test_actions_by_category_groups_for_ui_navigation(self) -> None:
        grouped = actions_by_category(DesktopSettings())

        self.assertIn("Pipeline", grouped)
        self.assertIn("Automation", grouped)
        self.assertIn("Dashboard", grouped)

    def test_command_text_formats_command_for_console(self) -> None:
        self.assertEqual(
            command_text(["python", "main.py", "--debug"]),
            "python main.py --debug",
        )

    def test_build_output_snapshot_detects_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "resume.md").write_text("# Resume", encoding="utf-8")
            (output_dir / "cover_letter.md").write_text("Cover", encoding="utf-8")

            snapshot = build_output_snapshot(output_dir)

            self.assertEqual(snapshot.generated_count, 2)
            self.assertGreater(snapshot.total_count, snapshot.generated_count)
            found = {artifact.filename for artifact in snapshot.artifacts if artifact.exists}
            self.assertIn("resume.md", found)
            self.assertIn("cover_letter.md", found)

    def test_latest_existing_artifact_returns_newest_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            resume = output_dir / "resume.md"
            cover_letter = output_dir / "cover_letter.md"
            resume.write_text("# Resume", encoding="utf-8")
            cover_letter.write_text("Cover", encoding="utf-8")
            os.utime(resume, (1000, 1000))
            os.utime(cover_letter, (2000, 2000))

            snapshot = build_output_snapshot(output_dir)

            self.assertEqual(latest_existing_artifact(snapshot.artifacts), cover_letter)

    def test_read_preview_text_handles_missing_and_truncation(self) -> None:
        self.assertIn("No generated files yet", read_preview_text(None))

        with tempfile.TemporaryDirectory() as temp_dir:
            preview_path = Path(temp_dir) / "resume.md"
            preview_path.write_text("abcdef", encoding="utf-8")

            self.assertEqual(read_preview_text(preview_path, max_chars=3), "abc\n\n[Preview truncated]")


if __name__ == "__main__":
    unittest.main()

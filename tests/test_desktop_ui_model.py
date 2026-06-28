import unittest
from pathlib import Path

from desktop_ui_model import (
    DesktopSettings,
    actions_by_category,
    apply_prep_command,
    command_text,
    desktop_actions,
    pipeline_command,
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


if __name__ == "__main__":
    unittest.main()

import argparse
import io
import unittest
from pathlib import Path
from unittest.mock import patch

from apply_prep_pipeline import (
    apply_prep_report_path,
    build_apply_assistant_command,
    build_browser_dry_run_command,
    build_apply_prep_report,
    build_apply_prep_steps,
    build_form_fill_command,
    build_package_command,
    run_apply_prep,
)
from pipeline import PipelineStep


def make_args(**overrides) -> argparse.Namespace:
    values = {
        "job_file": None,
        "job_option": Path("examples/sample_job.txt"),
        "output_dir": Path("outputs/example"),
        "answers": None,
        "ai": False,
        "ai_review": False,
        "strict_profile": False,
        "open_browser": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class ApplyPrepPipelineTests(unittest.TestCase):
    def test_build_package_command_can_enable_ai_flags(self) -> None:
        command = build_package_command(
            make_args(ai=True, ai_review=True, strict_profile=True)
        )

        self.assertIn("pipeline.py", command)
        self.assertIn("--ai", command)
        self.assertIn("--ai-review", command)
        self.assertIn("--strict-profile", command)

    def test_build_form_fill_command_can_use_answers_file(self) -> None:
        command = build_form_fill_command(
            make_args(answers=Path("profiles/application_answers.md"))
        )

        self.assertIn("form_fill_planner.py", command)
        self.assertIn("--answers", command)
        self.assertIn(str(Path("profiles/application_answers.md")), command)

    def test_build_apply_assistant_command_can_open_browser(self) -> None:
        command = build_apply_assistant_command(make_args(open_browser=True))

        self.assertIn("apply_assistant.py", command)
        self.assertIn("--open-browser", command)

    def test_build_browser_dry_run_command_writes_report(self) -> None:
        command = build_browser_dry_run_command(make_args())

        self.assertIn("browser_dry_run.py", command)
        self.assertIn("--write", command)

    def test_build_apply_prep_steps_runs_gate_before_apply_session(self) -> None:
        steps = build_apply_prep_steps(make_args())
        names = [name for name, _command in steps]

        self.assertEqual(
            names,
            [
                "Application package pipeline",
                "Form-fill plan",
                "Apply readiness gate",
                "Browser automation dry run",
                "Controlled apply session",
            ],
        )

    @patch("apply_prep_pipeline.run_step")
    def test_run_apply_prep_stops_on_failed_gate(self, run_step_mock) -> None:
        run_step_mock.side_effect = [
            PipelineStep("Application package pipeline", ["python"], 0, "", ""),
            PipelineStep("Form-fill plan", ["python"], 0, "", ""),
            PipelineStep("Apply readiness gate", ["python"], 1, "", "not ready"),
            PipelineStep("Browser automation dry run", ["python"], 0, "", ""),
            PipelineStep("Controlled apply session", ["python"], 0, "", ""),
        ]

        with patch("sys.stdout", new_callable=io.StringIO):
            steps = run_apply_prep(make_args())

        self.assertEqual(len(steps), 3)
        self.assertEqual(steps[-1].name, "Apply readiness gate")

    def test_build_apply_prep_report_lists_generated_files(self) -> None:
        steps = [
            PipelineStep("Application package pipeline", ["python"], 0, "ok", ""),
        ]

        report = build_apply_prep_report(steps, Path("outputs/example"))

        self.assertIn("Apply Prep Pipeline Report", report)
        self.assertIn("apply_readiness_report.md", report)
        self.assertIn("browser_dry_run.md", report)
        self.assertIn("It does not fill forms", report)

    def test_apply_prep_report_path_lives_in_output_dir(self) -> None:
        self.assertEqual(
            apply_prep_report_path(Path("outputs/example")),
            Path("outputs/example/apply_prep_report.md"),
        )


if __name__ == "__main__":
    unittest.main()

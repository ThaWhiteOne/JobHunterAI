import argparse
import unittest
from pathlib import Path

from pipeline import (
    build_generation_command,
    build_pipeline_report,
    build_pipeline_steps,
    pipeline_report_path,
)


def make_args(**overrides) -> argparse.Namespace:
    values = {
        "job_file": None,
        "job_option": Path("examples/sample_job.txt"),
        "output_dir": Path("outputs/example-ltd-support-engineer"),
        "ai": False,
        "ai_review": False,
        "strict_profile": False,
        "track": False,
        "company": "",
        "position": "",
        "url": "",
        "notes": "",
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class PipelineTests(unittest.TestCase):
    def test_build_generation_command_uses_full_package(self) -> None:
        command = build_generation_command(make_args())

        self.assertIn("main.py", command)
        self.assertIn("--full-package", command)
        self.assertIn("--output-dir", command)

    def test_build_generation_command_can_enable_ai_workflow(self) -> None:
        command = build_generation_command(make_args(ai=True))

        self.assertIn("--ai-drafts", command)
        self.assertIn("--ai-auto-revise", command)

    def test_build_generation_command_can_track_job(self) -> None:
        command = build_generation_command(
            make_args(
                track=True,
                company="Example Ltd",
                position="Support Engineer",
                url="https://example.com/job",
                notes="Interesting role",
            )
        )

        self.assertIn("--track", command)
        self.assertIn("Example Ltd", command)
        self.assertIn("Support Engineer", command)
        self.assertIn("https://example.com/job", command)
        self.assertIn("Interesting role", command)

    def test_build_pipeline_steps_includes_validation_generation_check_and_review(self) -> None:
        steps = build_pipeline_steps(make_args(ai_review=True, strict_profile=True))
        names = [name for name, _command in steps]
        commands = [command for _name, command in steps]

        self.assertEqual(
            names,
            [
                "Profile validation",
                "Application package generation",
                "Automation Unit check",
                "Recruiter review",
                "Readiness check",
            ],
        )
        self.assertIn("--strict", commands[0])
        self.assertIn("--ai-review", commands[-2])

    def test_build_pipeline_report_marks_stopped_when_step_fails(self) -> None:
        args = make_args()
        steps = []
        report = build_pipeline_report(steps, args.output_dir)

        self.assertIn("JobHunterAI Pipeline Report", report)
        self.assertIn("Status: Complete", report)

    def test_pipeline_report_path_lives_in_output_dir(self) -> None:
        output_dir = Path("outputs/example")

        self.assertEqual(
            pipeline_report_path(output_dir),
            output_dir / "pipeline_report.md",
        )


if __name__ == "__main__":
    unittest.main()

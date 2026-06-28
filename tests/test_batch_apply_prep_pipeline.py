import argparse
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from batch_apply_prep_pipeline import (
    BatchApplyPrepResult,
    batch_apply_prep_report_path,
    build_apply_prep_command,
    build_batch_apply_prep_report,
    process_job,
    run_batch,
)


class BatchApplyPrepPipelineTests(unittest.TestCase):
    def test_build_apply_prep_command_can_enable_options(self) -> None:
        command = build_apply_prep_command(
            Path("jobs/support.txt"),
            Path("outputs/batch/support"),
            answers=Path("profiles/application_answers.md"),
            ai=True,
            ai_review=True,
            strict_profile=True,
        )

        self.assertIn("apply_prep_pipeline.py", command)
        self.assertIn("--answers", command)
        self.assertIn(str(Path("profiles/application_answers.md")), command)
        self.assertIn("--ai", command)
        self.assertIn("--ai-review", command)
        self.assertIn("--strict-profile", command)

    @patch("batch_apply_prep_pipeline.run_apply_prep_command")
    def test_process_job_returns_apply_prep_result(self, run_apply_prep_command_mock) -> None:
        run_apply_prep_command_mock.return_value = argparse.Namespace(
            returncode=0,
            stdout="Apply prep OK",
            stderr="",
        )

        result = process_job(Path("jobs/support.txt"), Path("outputs/batch-apply-prep"))

        self.assertTrue(result.succeeded)
        self.assertEqual(result.output_dir, Path("outputs/batch-apply-prep/support"))
        self.assertIn("Apply prep OK", result.stdout)

    def test_build_batch_apply_prep_report_summarizes_results(self) -> None:
        results = [
            BatchApplyPrepResult(
                job_path=Path("jobs/support.txt"),
                output_dir=Path("outputs/batch/support"),
                command=["python", "apply_prep_pipeline.py"],
                returncode=0,
                stdout="OK",
                stderr="",
            ),
            BatchApplyPrepResult(
                job_path=Path("jobs/dev.txt"),
                output_dir=Path("outputs/batch/dev"),
                command=["python", "apply_prep_pipeline.py"],
                returncode=1,
                stdout="",
                stderr="Failed",
            ),
        ]

        report = build_batch_apply_prep_report(results, Path("outputs/batch"))

        self.assertIn("Batch Apply Prep Report", report)
        self.assertIn("Jobs processed: 2", report)
        self.assertIn("Successful: 1", report)
        self.assertIn("Failed: 1", report)
        self.assertIn("does not open browsers", report)

    @patch("batch_apply_prep_pipeline.process_job")
    def test_run_batch_can_stop_on_first_error(self, process_job_mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            (jobs_dir / "first.txt").write_text("first", encoding="utf-8")
            (jobs_dir / "second.txt").write_text("second", encoding="utf-8")
            process_job_mock.return_value = BatchApplyPrepResult(
                job_path=jobs_dir / "first.txt",
                output_dir=Path("outputs/batch/first"),
                command=["python", "apply_prep_pipeline.py"],
                returncode=1,
                stdout="",
                stderr="Failed",
            )
            args = argparse.Namespace(
                jobs_dir=jobs_dir,
                output_root=Path("outputs/batch"),
                answers=None,
                ai=False,
                ai_review=False,
                strict_profile=False,
                stop_on_error=True,
            )

            with patch("sys.stdout", new_callable=io.StringIO):
                results = run_batch(args)

            self.assertEqual(len(results), 1)

    def test_batch_apply_prep_report_path_lives_in_output_root(self) -> None:
        self.assertEqual(
            batch_apply_prep_report_path(Path("outputs/batch-apply-prep")),
            Path("outputs/batch-apply-prep/batch_apply_prep_report.md"),
        )


if __name__ == "__main__":
    unittest.main()

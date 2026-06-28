import argparse
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from batch_pipeline import (
    BatchJobResult,
    batch_report_path,
    build_batch_report,
    build_pipeline_command,
    discover_job_files,
    output_dir_for_job,
    process_job,
    run_batch,
    slugify,
)


class BatchPipelineTests(unittest.TestCase):
    def test_slugify_creates_folder_safe_names(self) -> None:
        self.assertEqual(slugify("Junior Python Developer!"), "junior-python-developer")

    def test_discover_job_files_returns_sorted_txt_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            (jobs_dir / "b-job.txt").write_text("B", encoding="utf-8")
            (jobs_dir / "a-job.txt").write_text("A", encoding="utf-8")
            (jobs_dir / "notes.md").write_text("ignore", encoding="utf-8")

            job_files = discover_job_files(jobs_dir)

            self.assertEqual([path.name for path in job_files], ["a-job.txt", "b-job.txt"])

    def test_output_dir_for_job_uses_job_file_stem(self) -> None:
        output_dir = output_dir_for_job(
            Path("outputs/batch"),
            Path("jobs/Junior Python Developer.txt"),
        )

        self.assertEqual(output_dir, Path("outputs/batch/junior-python-developer"))

    def test_build_pipeline_command_can_enable_ai_flags(self) -> None:
        command = build_pipeline_command(
            Path("jobs/job.txt"),
            Path("outputs/batch/job"),
            ai=True,
            ai_review=True,
            strict_profile=True,
        )

        self.assertIn("--ai", command)
        self.assertIn("--ai-review", command)
        self.assertIn("--strict-profile", command)

    @patch("batch_pipeline.run_job_pipeline")
    def test_process_job_returns_pipeline_result(self, run_job_pipeline_mock) -> None:
        run_job_pipeline_mock.return_value = argparse.Namespace(
            returncode=0,
            stdout="Pipeline OK",
            stderr="",
        )

        result = process_job(Path("jobs/support.txt"), Path("outputs/batch"))

        self.assertTrue(result.succeeded)
        self.assertEqual(result.output_dir, Path("outputs/batch/support"))
        self.assertIn("Pipeline OK", result.stdout)

    def test_build_batch_report_summarizes_results(self) -> None:
        results = [
            BatchJobResult(
                job_path=Path("jobs/support.txt"),
                output_dir=Path("outputs/batch/support"),
                command=["python", "pipeline.py"],
                returncode=0,
                stdout="OK",
                stderr="",
            ),
            BatchJobResult(
                job_path=Path("jobs/dev.txt"),
                output_dir=Path("outputs/batch/dev"),
                command=["python", "pipeline.py"],
                returncode=1,
                stdout="",
                stderr="Failed",
            ),
        ]

        report = build_batch_report(results, Path("outputs/batch"))

        self.assertIn("Jobs processed: 2", report)
        self.assertIn("Successful: 1", report)
        self.assertIn("Failed: 1", report)
        self.assertIn("Completed with failures", report)

    @patch("batch_pipeline.process_job")
    def test_run_batch_can_stop_on_first_error(self, process_job_mock) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            (jobs_dir / "first.txt").write_text("first", encoding="utf-8")
            (jobs_dir / "second.txt").write_text("second", encoding="utf-8")
            process_job_mock.return_value = BatchJobResult(
                job_path=jobs_dir / "first.txt",
                output_dir=Path("outputs/batch/first"),
                command=["python", "pipeline.py"],
                returncode=1,
                stdout="",
                stderr="Failed",
            )
            args = argparse.Namespace(
                jobs_dir=jobs_dir,
                output_root=Path("outputs/batch"),
                ai=False,
                ai_review=False,
                strict_profile=False,
                stop_on_error=True,
            )

            with patch("sys.stdout", new_callable=io.StringIO):
                results = run_batch(args)

            self.assertEqual(len(results), 1)

    def test_batch_report_path_lives_in_output_root(self) -> None:
        self.assertEqual(
            batch_report_path(Path("outputs/batch")),
            Path("outputs/batch/batch_report.md"),
        )


if __name__ == "__main__":
    unittest.main()

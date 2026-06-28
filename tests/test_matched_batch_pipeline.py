import argparse
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from job_matcher import JobMatch
from matched_batch_pipeline import (
    MatchedBatchResult,
    build_matched_batch_report,
    eligible_matches,
    matched_batch_report_path,
    process_matched_job,
    run_matched_batch,
)


def make_match(
    score: int,
    company: str = "Example Ltd",
    position: str = "Junior Python Developer",
    recommendation: str = "strong",
) -> JobMatch:
    return JobMatch(
        company=company,
        position=position,
        url="https://example.com/job",
        job_file=Path(f"jobs/{company.lower().replace(' ', '-')}.txt"),
        role="developer",
        score=score,
        recommendation=recommendation,
        role_scores={"support": 0, "developer": 5, "cybersecurity": 0},
        matched_keywords=["python", "git"],
        positive_signals=["junior", "python"],
        risk_signals=[],
        requirement_lines=["Python", "Git"],
    )


class MatchedBatchPipelineTests(unittest.TestCase):
    def test_eligible_matches_filters_errors_and_low_scores(self) -> None:
        matches = [
            make_match(85, company="Strong Co"),
            make_match(60, company="Review Co", recommendation="review"),
            make_match(90, company="Error Co", recommendation="error"),
        ]

        selected = eligible_matches(matches, min_score=70)

        self.assertEqual([match.company for match in selected], ["Strong Co"])

    def test_eligible_matches_can_limit_result_count(self) -> None:
        matches = [make_match(90, company="A"), make_match(88, company="B")]

        selected = eligible_matches(matches, min_score=70, max_jobs=1)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].company, "A")

    @patch("matched_batch_pipeline.run_job_pipeline")
    def test_process_matched_job_runs_existing_pipeline_command(self, run_job_pipeline_mock) -> None:
        run_job_pipeline_mock.return_value = argparse.Namespace(
            returncode=0,
            stdout="Pipeline OK",
            stderr="",
        )

        result = process_matched_job(make_match(90), Path("outputs/matched"), ai=True)

        self.assertTrue(result.succeeded)
        self.assertIn("--ai", result.pipeline_result.command)
        self.assertEqual(result.pipeline_result.output_dir, Path("outputs/matched/example-ltd"))

    @patch("matched_batch_pipeline.process_matched_job")
    @patch("matched_batch_pipeline.match_saved_jobs")
    def test_run_matched_batch_processes_only_selected_matches(
        self,
        match_saved_jobs_mock,
        process_matched_job_mock,
    ) -> None:
        selected = make_match(90, company="Selected")
        skipped = make_match(30, company="Skipped", recommendation="low")
        match_saved_jobs_mock.return_value = [selected, skipped]
        process_matched_job_mock.return_value = MatchedBatchResult(
            match=selected,
            pipeline_result=argparse.Namespace(
                succeeded=True,
                output_dir=Path("outputs/matched/selected"),
            ),
        )
        args = argparse.Namespace(
            jobs_dir=Path("jobs"),
            output_root=Path("outputs/matched"),
            min_score=70,
            max_jobs=0,
            ai=False,
            ai_review=False,
            strict_profile=False,
            stop_on_error=False,
        )

        with patch("sys.stdout", new_callable=io.StringIO):
            results = run_matched_batch(args)

        self.assertEqual(len(results), 1)
        process_matched_job_mock.assert_called_once()

    @patch("matched_batch_pipeline.match_saved_jobs", return_value=[make_match(20)])
    def test_run_matched_batch_rejects_when_no_jobs_meet_score(self, _mock) -> None:
        args = argparse.Namespace(
            jobs_dir=Path("jobs"),
            output_root=Path("outputs/matched"),
            min_score=70,
            max_jobs=0,
            ai=False,
            ai_review=False,
            strict_profile=False,
            stop_on_error=False,
        )

        with self.assertRaises(ValueError):
            run_matched_batch(args)

    def test_build_matched_batch_report_summarizes_results(self) -> None:
        match = make_match(90)
        result = MatchedBatchResult(
            match=match,
            pipeline_result=argparse.Namespace(
                succeeded=True,
                job_path=match.job_file,
                output_dir=Path("outputs/matched/example-ltd"),
                command=["python", "pipeline.py"],
                stdout="OK",
                stderr="",
            ),
        )

        report = build_matched_batch_report([result], Path("outputs/matched"), 70)

        self.assertIn("Matched Batch Pipeline Report", report)
        self.assertIn("Minimum match score: 70", report)
        self.assertIn("Jobs processed: 1", report)

    def test_matched_batch_report_path_lives_in_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir)

            self.assertEqual(
                matched_batch_report_path(output_root),
                output_root / "matched_batch_report.md",
            )


if __name__ == "__main__":
    unittest.main()

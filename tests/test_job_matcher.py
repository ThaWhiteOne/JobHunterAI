import tempfile
import unittest
from pathlib import Path

from job_intake import save_job_description
from job_matcher import (
    build_match_report,
    calculate_match_score,
    find_signals,
    match_saved_jobs,
    recommendation_for_score,
    write_match_report,
)


class JobMatcherTests(unittest.TestCase):
    def test_find_signals_returns_matching_terms(self) -> None:
        signals = find_signals(
            "Junior Python Developer with SQL and Git",
            ["junior", "python", "soc"],
        )

        self.assertEqual(signals, ["junior", "python"])

    def test_calculate_match_score_rewards_matches_and_penalizes_risks(self) -> None:
        strong_score = calculate_match_score(
            {"support": 0, "developer": 5, "cybersecurity": 0},
            ["python", "git", "backend"],
            ["junior", "remote"],
            [],
        )
        risky_score = calculate_match_score(
            {"support": 0, "developer": 5, "cybersecurity": 0},
            ["python", "git", "backend"],
            ["junior", "remote"],
            ["senior", "5+ years"],
        )

        self.assertGreater(strong_score, risky_score)
        self.assertGreaterEqual(strong_score, 70)

    def test_recommendation_for_score_groups_matches(self) -> None:
        self.assertEqual(recommendation_for_score(80), "strong")
        self.assertEqual(recommendation_for_score(50), "review")
        self.assertEqual(recommendation_for_score(20), "low")

    def test_match_saved_jobs_ranks_saved_job_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            save_job_description(
                company="Example Dev",
                position="Junior Python Developer",
                url="https://example.com/dev",
                source="test",
                job_text=(
                    "Junior Python Developer\n"
                    "- Python\n- APIs\n- backend\n- Git\n- SQL\n"
                    "- Build web applications"
                ),
                jobs_dir=jobs_dir,
            )
            save_job_description(
                company="Example Senior",
                position="Senior Architect",
                url="https://example.com/senior",
                source="test",
                job_text="Senior architect manager role requiring 7+ years.",
                jobs_dir=jobs_dir,
            )

            matches = match_saved_jobs(jobs_dir)

            self.assertEqual(matches[0].company, "Example Dev")
            self.assertEqual(matches[0].role, "developer")
            self.assertEqual(matches[0].recommendation, "strong")
            self.assertGreater(matches[0].score, matches[1].score)

    def test_match_saved_jobs_records_missing_file_as_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            index_path = jobs_dir / "job_index.json"
            index_path.write_text(
                '{"jobs": [{"company": "Missing Co", "position": "Role", "job_file": "missing.txt"}]}',
                encoding="utf-8",
            )

            matches = match_saved_jobs(jobs_dir)

            self.assertEqual(matches[0].recommendation, "error")
            self.assertIn("Missing required file", matches[0].error)

    def test_build_match_report_includes_ranked_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            save_job_description(
                company="Secure Co",
                position="Junior SOC Analyst",
                job_text="Junior SOC Analyst with SIEM monitoring and incident response.",
                jobs_dir=jobs_dir,
            )

            report = build_match_report(match_saved_jobs(jobs_dir))

            self.assertIn("# Job Match Report", report)
            self.assertIn("Secure Co - Junior SOC Analyst", report)
            self.assertIn("Detected role: cybersecurity", report)

    def test_write_match_report_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            save_job_description(
                company="Support Co",
                position="Technical Support Engineer",
                job_text="Technical Support Engineer with SQL and troubleshooting.",
                jobs_dir=jobs_dir,
            )

            report_path = write_match_report(match_saved_jobs(jobs_dir), jobs_dir)

            self.assertTrue(report_path.exists())
            self.assertIn("Job Match Report", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

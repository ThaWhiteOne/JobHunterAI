import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from browser_review_session import (
    browser_review_session_path,
    build_browser_review_session_report,
    dry_run_job_url,
    open_dry_run_job_url,
    review_action_lines,
)
from page_inspector import inspection_json_path, inspection_markdown_path
from tests.test_page_inspector import sample_dry_run


class BrowserReviewSessionTests(unittest.TestCase):
    def test_dry_run_job_url_returns_blank_when_not_provided(self) -> None:
        dry_run = sample_dry_run()
        dry_run["job"]["job_url"] = "not provided"

        self.assertEqual(dry_run_job_url(dry_run), "")

    @patch("browser_review_session.webbrowser.open")
    def test_open_dry_run_job_url_uses_default_browser(self, browser_open_mock) -> None:
        browser_open_mock.return_value = True

        opened = open_dry_run_job_url(sample_dry_run())

        self.assertTrue(opened)
        browser_open_mock.assert_called_once_with("https://example.com/job")

    def test_open_dry_run_job_url_rejects_missing_url(self) -> None:
        dry_run = sample_dry_run()
        dry_run["job"]["job_url"] = ""

        with self.assertRaises(ValueError):
            open_dry_run_job_url(dry_run)

    def test_review_action_lines_lists_only_page_relevant_actions(self) -> None:
        lines = review_action_lines(sample_dry_run()["actions"])

        self.assertIn("fill_contact_field -> full_name", "\n".join(lines))
        self.assertIn("stop_before_submit -> final_submit_button", "\n".join(lines))

    def test_build_browser_review_session_report_keeps_submit_disabled(self) -> None:
        report = build_browser_review_session_report(
            sample_dry_run(),
            Path("outputs/example/browser_dry_run.json"),
            browser_opened=False,
            inspection_written=False,
            html_source="",
        )

        self.assertIn("Browser Review Session", report)
        self.assertIn("Status: Prepared, not submitted", report)
        self.assertIn("Submission allowed: False", report)
        self.assertIn("does not fill fields", report)

    def test_browser_review_session_path_lives_beside_dry_run(self) -> None:
        dry_run_path = Path("outputs/example/browser_dry_run.json")

        self.assertEqual(
            browser_review_session_path(dry_run_path),
            Path("outputs/example/browser_review_session.md"),
        )

    def test_page_inspection_paths_can_be_written_beside_dry_run(self) -> None:
        dry_run_path = Path("outputs/example/browser_dry_run.json")

        self.assertEqual(
            inspection_json_path(dry_run_path),
            Path("outputs/example/page_inspection.json"),
        )
        self.assertEqual(
            inspection_markdown_path(dry_run_path),
            Path("outputs/example/page_inspection.md"),
        )

    def test_dry_run_json_can_feed_review_session_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dry_run_path = Path(temp_dir) / "browser_dry_run.json"
            dry_run_path.write_text(json.dumps(sample_dry_run()), encoding="utf-8")
            dry_run = json.loads(dry_run_path.read_text(encoding="utf-8"))

            report = build_browser_review_session_report(
                dry_run,
                dry_run_path,
                browser_opened=True,
                inspection_written=True,
                html_source="sample.html",
            )

            self.assertIn("Browser opened: True", report)
            self.assertIn("Page inspection written: True", report)
            self.assertIn("sample.html", report)


if __name__ == "__main__":
    unittest.main()

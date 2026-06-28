import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from apply_assistant import (
    apply_session_path,
    build_apply_session_report,
    is_supported_url,
    job_url,
    open_job_url,
)
from submission_planner import load_packet
from tests.test_submission_planner import sample_packet


class ApplyAssistantTests(unittest.TestCase):
    def test_job_url_returns_blank_when_missing(self) -> None:
        packet = sample_packet()
        packet["job"]["job_url"] = "not provided"

        self.assertEqual(job_url(packet), "")

        packet["job"]["job_url"] = None

        self.assertEqual(job_url(packet), "")

    def test_is_supported_url_accepts_http_and_https_only(self) -> None:
        self.assertTrue(is_supported_url("https://example.com/job"))
        self.assertTrue(is_supported_url("http://example.com/job"))
        self.assertFalse(is_supported_url("mailto:jobs@example.com"))
        self.assertFalse(is_supported_url("example.com/job"))

    def test_build_apply_session_report_includes_stop_line_and_files(self) -> None:
        packet = sample_packet()

        report = build_apply_session_report(
            packet,
            Path("outputs/example/application_packet.json"),
            browser_opened=False,
        )

        self.assertIn("Apply Session", report)
        self.assertIn("Status: Prepared, not submitted", report)
        self.assertIn("outputs/example/resume.md", report)
        self.assertIn("Stop before any final submit button", report)

    @patch("apply_assistant.webbrowser.open")
    def test_open_job_url_uses_default_browser(self, browser_open_mock) -> None:
        browser_open_mock.return_value = True

        opened = open_job_url(sample_packet())

        self.assertTrue(opened)
        browser_open_mock.assert_called_once_with("https://example.com/job")

    def test_open_job_url_rejects_missing_url(self) -> None:
        packet = sample_packet()
        packet["job"]["job_url"] = ""

        with self.assertRaises(ValueError):
            open_job_url(packet)

    def test_apply_session_path_lives_beside_packet(self) -> None:
        self.assertEqual(
            apply_session_path(Path("outputs/example/application_packet.json")),
            Path("outputs/example/apply_session.md"),
        )

    def test_packet_can_feed_apply_session_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet_path = Path(temp_dir) / "application_packet.json"
            packet_path.write_text(json.dumps(sample_packet()), encoding="utf-8")

            packet = load_packet(packet_path)
            report = build_apply_session_report(packet, packet_path, browser_opened=True)

            self.assertIn("Browser opened: True", report)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from batch_job_url_importer import (
    UrlImportResult,
    build_import_report,
    import_url_batch,
    read_url_list,
    write_import_report,
)
from job_url_importer import ImportedJob


class BatchJobUrlImporterTests(unittest.TestCase):
    def test_read_url_list_ignores_blank_comments_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            urls_file = Path(temp_dir) / "urls.txt"
            urls_file.write_text(
                "\n# saved searches\nhttps://example.com/a\nhttps://example.com/a\n"
                "https://example.com/b\n",
                encoding="utf-8",
            )

            urls = read_url_list(urls_file)

            self.assertEqual(urls, ["https://example.com/a", "https://example.com/b"])

    def test_read_url_list_rejects_empty_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            urls_file = Path(temp_dir) / "urls.txt"
            urls_file.write_text("# no urls yet", encoding="utf-8")

            with self.assertRaises(ValueError):
                read_url_list(urls_file)

    def test_import_url_batch_records_success_with_detected_role(self) -> None:
        imported = ImportedJob(
            company="Example Ltd",
            position="Junior Python Developer",
            url="https://example.com/dev",
            description="Build backend APIs, web applications, Python code, SQL, and Git workflows.",
        )

        with patch("batch_job_url_importer.import_job_url", return_value=imported):
            results = import_url_batch(["https://example.com/dev"])

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].role, "developer")
        self.assertEqual(results[0].company, "Example Ltd")

    def test_import_url_batch_continues_after_failure_by_default(self) -> None:
        imported = ImportedJob(
            company="Secure Co",
            position="Junior SOC Analyst",
            url="https://example.com/soc",
            description="Monitor SIEM security events and support incident response.",
        )

        with patch(
            "batch_job_url_importer.import_job_url",
            side_effect=[ValueError("blocked"), imported],
        ):
            results = import_url_batch(["https://example.com/blocked", "https://example.com/soc"])

        self.assertEqual(len(results), 2)
        self.assertFalse(results[0].success)
        self.assertTrue(results[1].success)
        self.assertEqual(results[1].role, "cybersecurity")

    def test_import_url_batch_can_stop_after_failure(self) -> None:
        with patch("batch_job_url_importer.import_job_url", side_effect=ValueError("blocked")):
            results = import_url_batch(
                ["https://example.com/blocked", "https://example.com/next"],
                stop_on_error=True,
            )

        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)

    def test_build_import_report_includes_success_and_failure_details(self) -> None:
        report = build_import_report(
            [
                UrlImportResult(
                    url="https://example.com/dev",
                    success=True,
                    company="Example Ltd",
                    position="Junior Python Developer",
                    role="developer",
                    scores={"support": 0, "developer": 5, "cybersecurity": 0},
                ),
                UrlImportResult(
                    url="https://example.com/fail",
                    success=False,
                    error="blocked",
                ),
            ]
        )

        self.assertIn("Imported: 1", report)
        self.assertIn("Failed: 1", report)
        self.assertIn("Detected role: developer", report)
        self.assertIn("Error: blocked", report)

    def test_write_import_report_creates_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report_path = write_import_report(
                [UrlImportResult(url="https://example.com/dev", success=True, role="developer")],
                jobs_dir=Path(temp_dir),
            )

            self.assertTrue(report_path.exists())
            self.assertIn("Job URL Import Report", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

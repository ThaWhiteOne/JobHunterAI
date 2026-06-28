import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from job_intake import index_path, list_saved_jobs
from job_url_importer import (
    clean_multiline_text,
    extract_imported_job,
    fetch_url_text,
    import_job_url,
    validate_url,
)


JOB_POSTING_HTML = """
<!doctype html>
<html>
<head>
  <title>Fallback Title</title>
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    "title": "Junior Python Developer",
    "hiringOrganization": {"@type": "Organization", "name": "Example Ltd"},
    "description": "<p>Build backend APIs, maintain web applications, use Git and SQL.</p>"
  }
  </script>
</head>
<body>
  <h1>Junior Python Developer</h1>
  <p>Visible fallback description.</p>
</body>
</html>
"""


class JobUrlImporterTests(unittest.TestCase):
    def test_validate_url_rejects_non_http_urls(self) -> None:
        with self.assertRaises(ValueError):
            validate_url("file:///secret/job.html")

    def test_clean_multiline_text_normalizes_html_text(self) -> None:
        text = clean_multiline_text("  First line  \n\n Second   line ")

        self.assertEqual(text, "First line\nSecond line")

    def test_extract_imported_job_prefers_json_ld_job_posting(self) -> None:
        imported = extract_imported_job(JOB_POSTING_HTML, "https://example.com/jobs/1")

        self.assertEqual(imported.company, "Example Ltd")
        self.assertEqual(imported.position, "Junior Python Developer")
        self.assertIn("backend APIs", imported.description)
        self.assertEqual(imported.source, "url-import")

    def test_extract_imported_job_allows_company_and_position_overrides(self) -> None:
        imported = extract_imported_job(
            JOB_POSTING_HTML,
            "https://example.com/jobs/1",
            company_override="Override Co",
            position_override="Override Role",
        )

        self.assertEqual(imported.company, "Override Co")
        self.assertEqual(imported.position, "Override Role")

    def test_import_job_url_saves_to_local_job_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)

            with patch("job_url_importer.fetch_url_text", return_value=JOB_POSTING_HTML):
                imported = import_job_url("https://example.com/jobs/1", jobs_dir=jobs_dir)

            self.assertEqual(imported.company, "Example Ltd")
            self.assertTrue(index_path(jobs_dir).exists())
            jobs = list_saved_jobs(jobs_dir)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["source"], "url-import")
            saved_text = Path(jobs[0]["job_file"]).read_text(encoding="utf-8")
            self.assertIn("Junior Python Developer", saved_text)

    def test_fetch_url_text_rejects_non_html_response(self) -> None:
        class Headers(dict):
            def get_content_charset(self) -> str:
                return "utf-8"

        class Response:
            headers = Headers({"Content-Type": "application/json"})

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

            def read(self) -> bytes:
                return json.dumps({"ok": True}).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=Response()):
            with self.assertRaises(ValueError):
                fetch_url_text("https://example.com/jobs/1")


if __name__ == "__main__":
    unittest.main()

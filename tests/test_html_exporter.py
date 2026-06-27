import tempfile
import unittest
from pathlib import Path

from html_exporter import export_html_files, markdown_to_html_document


class HtmlExporterTests(unittest.TestCase):
    def test_markdown_to_html_document_converts_common_resume_markdown(self) -> None:
        html = markdown_to_html_document(
            "Resume",
            "# Nikola Titirinov\n\n## Skills\n\n- Python\n- SQL\n\n<script>",
        )

        self.assertIn("<h1>Nikola Titirinov</h1>", html)
        self.assertIn("<h2>Skills</h2>", html)
        self.assertIn("<li>Python</li>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_export_html_files_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            exported_paths = export_html_files(
                output_dir,
                "# Resume",
                "Dear Hiring Manager,",
                "Hello,",
            )

            self.assertEqual(
                exported_paths,
                [
                    output_dir / "resume.html",
                    output_dir / "cover_letter.html",
                    output_dir / "linkedin_message.html",
                ],
            )
            for path in exported_paths:
                self.assertTrue(path.exists())
                self.assertIn("<!doctype html>", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

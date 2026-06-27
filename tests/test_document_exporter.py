import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from document_exporter import (
    export_docx_files,
    export_pdf_files,
    markdown_to_lines,
    write_docx,
    write_pdf,
)


class DocumentExporterTests(unittest.TestCase):
    def test_markdown_to_lines_removes_markdown_markers(self) -> None:
        lines = markdown_to_lines("# Name\n\n## Skills\n\n- Python")

        self.assertEqual(lines, ["Name", "", "Skills", "", "- Python"])

    def test_write_docx_creates_valid_docx_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.docx"

            write_docx(path, "Resume", "# Nikola\n\n- Python")

            self.assertTrue(path.exists())
            with ZipFile(path) as docx:
                self.assertIn("word/document.xml", docx.namelist())
                document_xml = docx.read("word/document.xml").decode("utf-8")
            self.assertIn("Resume", document_xml)
            self.assertIn("Nikola", document_xml)

    def test_write_pdf_creates_pdf_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "resume.pdf"

            write_pdf(path, "Resume", "# Nikola\n\n- Python")

            self.assertTrue(path.exists())
            self.assertTrue(path.read_bytes().startswith(b"%PDF-1.4"))

    def test_export_docx_and_pdf_files_write_expected_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            docx_paths = export_docx_files(output_dir, "# Resume", "Cover", "Message")
            pdf_paths = export_pdf_files(output_dir, "# Resume", "Cover", "Message")

            self.assertEqual(
                docx_paths,
                [
                    output_dir / "resume.docx",
                    output_dir / "cover_letter.docx",
                    output_dir / "linkedin_message.docx",
                ],
            )
            self.assertEqual(
                pdf_paths,
                [
                    output_dir / "resume.pdf",
                    output_dir / "cover_letter.pdf",
                    output_dir / "linkedin_message.pdf",
                ],
            )
            for path in [*docx_paths, *pdf_paths]:
                self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()

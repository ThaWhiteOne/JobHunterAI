import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def run_command(arguments: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_main_generates_files_with_custom_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("JobHunterAI finished successfully.", result.stdout)
            self.assertTrue((output_dir / "resume.md").exists())
            self.assertTrue((output_dir / "cover_letter.md").exists())
            self.assertTrue((output_dir / "linkedin_message.txt").exists())

    def test_main_can_save_original_job_description(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--save-job-text",
                ]
            )

            job_description_path = output_dir / "job_description.txt"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(job_description_path), result.stdout)
            self.assertTrue(job_description_path.exists())
            self.assertIn("SQL", job_description_path.read_text(encoding="utf-8"))

    def test_main_can_export_html_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--export",
                    "html",
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(output_dir / "resume.html"), result.stdout)
            self.assertTrue((output_dir / "resume.html").exists())
            self.assertTrue((output_dir / "cover_letter.html").exists())
            self.assertTrue((output_dir / "linkedin_message.html").exists())

    def test_main_can_export_all_document_formats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--export",
                    "all",
                ]
            )

            expected_files = [
                "resume.html",
                "cover_letter.html",
                "linkedin_message.html",
                "resume.docx",
                "cover_letter.docx",
                "linkedin_message.docx",
                "resume.pdf",
                "cover_letter.pdf",
                "linkedin_message.pdf",
            ]

            self.assertEqual(result.returncode, 0, result.stderr)
            for filename in expected_files:
                path = output_dir / filename
                with self.subTest(filename=filename):
                    self.assertIn(str(path), result.stdout)
                    self.assertTrue(path.exists())

    def test_main_can_generate_application_review_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--review-notes",
                ]
            )

            review_notes_path = output_dir / "application_review.md"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(review_notes_path), result.stdout)
            self.assertTrue(review_notes_path.exists())
            self.assertIn(
                "Future Automation/AI Unit Notes",
                review_notes_path.read_text(encoding="utf-8"),
            )

    def test_main_can_generate_ai_brief(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--ai-brief",
                ]
            )

            ai_brief_path = output_dir / "ai_brief.md"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(ai_brief_path), result.stdout)
            self.assertTrue(ai_brief_path.exists())
            self.assertIn(
                "Do not invent employers",
                ai_brief_path.read_text(encoding="utf-8"),
            )

    def test_main_can_generate_application_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--manifest",
                ]
            )

            manifest_path = output_dir / "application_manifest.json"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(manifest_path), result.stdout)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["detected_role"], "support")
            self.assertIn(manifest_path.as_posix(), manifest["generated_files"])

    def test_main_can_generate_full_application_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--full-package",
                ]
            )

            expected_files = [
                "resume.md",
                "cover_letter.md",
                "linkedin_message.txt",
                "job_description.txt",
                "application_review.md",
                "ai_brief.md",
                "application_manifest.json",
                "resume.html",
                "cover_letter.html",
                "linkedin_message.html",
                "resume.docx",
                "cover_letter.docx",
                "linkedin_message.docx",
                "resume.pdf",
                "cover_letter.pdf",
                "linkedin_message.pdf",
            ]

            self.assertEqual(result.returncode, 0, result.stderr)
            for filename in expected_files:
                path = output_dir / filename
                with self.subTest(filename=filename):
                    self.assertIn(str(path), result.stdout)
                    self.assertTrue(path.exists())

    def test_automation_unit_can_check_generated_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--full-package",
                ]
            )
            check_result = run_command(
                [
                    "automation_unit.py",
                    "check",
                    str(output_dir / "application_manifest.json"),
                ]
            )

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(check_result.returncode, 0, check_result.stderr)
            self.assertIn("Automation Unit check complete.", check_result.stdout)
            self.assertIn("Detected role: support", check_result.stdout)
            self.assertIn("Missing generated files: none", check_result.stdout)
            self.assertIn("Do not submit applications automatically", check_result.stdout)

    def test_automation_unit_can_write_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--full-package",
                ]
            )
            check_result = run_command(
                [
                    "automation_unit.py",
                    "check",
                    str(output_dir / "application_manifest.json"),
                    "--write-report",
                ]
            )
            report_path = output_dir / "automation_report.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(check_result.returncode, 0, check_result.stderr)
            self.assertIn(str(report_path), check_result.stdout)
            self.assertTrue(report_path.exists())
            self.assertIn(
                "Automation Unit check complete.",
                report_path.read_text(encoding="utf-8"),
            )

    def test_tracker_cli_add_list_and_stats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"
            env = os.environ.copy()
            env["JOBHUNTERAI_DB_PATH"] = str(db_path)

            add_result = run_command(
                [
                    "tracker.py",
                    "add",
                    "--company",
                    "Example Ltd",
                    "--position",
                    "Support Engineer",
                    "--role",
                    "support",
                    "--status",
                    "applied",
                ],
                env=env,
            )
            list_result = run_command(
                ["tracker.py", "list", "--status", "applied", "--role", "support"],
                env=env,
            )
            stats_result = run_command(["tracker.py", "stats"], env=env)

            self.assertEqual(add_result.returncode, 0, add_result.stderr)
            self.assertEqual(list_result.returncode, 0, list_result.stderr)
            self.assertEqual(stats_result.returncode, 0, stats_result.stderr)
            self.assertIn("Added job #1.", add_result.stdout)
            self.assertIn("Example Ltd - Support Engineer [applied]", list_result.stdout)
            self.assertIn("Total jobs: 1", stats_result.stdout)
            self.assertIn("- applied: 1", stats_result.stdout)


if __name__ == "__main__":
    unittest.main()

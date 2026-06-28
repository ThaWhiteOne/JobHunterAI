import json
import tempfile
import unittest
from pathlib import Path

from readiness_checker import (
    build_readiness_report,
    check_readiness,
    missing_required_output_files,
    readiness_report_path,
    resolve_manifest_path,
)


def write_ready_package(output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = {
        "resume.md": "# Resume\n\n" + "Python SQL support troubleshooting customer. " * 30,
        "cover_letter.md": "Dear Hiring Manager,\n\n"
        + "I can support this technical support role with SQL and troubleshooting. " * 12,
        "linkedin_message.txt": "Hello, I am interested in this support role.",
        "automation_report.md": "Automation Unit check complete.",
        "recruiter_review.md": "Recruiter Review Agent Report",
        "pipeline_report.md": "Pipeline report",
    }
    for filename, content in files.items():
        (output_dir / filename).write_text(content, encoding="utf-8")

    manifest_path = output_dir / "application_manifest.json"
    manifest = {
        "detected_role": "support",
        "role_display_name": "Technical Support / Application Support",
        "generated_files": [
            (output_dir / "resume.md").as_posix(),
            (output_dir / "cover_letter.md").as_posix(),
            (output_dir / "linkedin_message.txt").as_posix(),
            manifest_path.as_posix(),
        ],
        "matched_keywords": ["SQL", "support", "troubleshooting"],
        "used_fallback_profile": False,
        "tracked_job_id": 1,
        "automation_guardrails": [
            "Do not submit applications automatically without user confirmation."
        ],
        "next_manual_step": "Review generated drafts before applying.",
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


class ReadinessCheckerTests(unittest.TestCase):
    def test_resolve_manifest_path_accepts_output_folder(self) -> None:
        self.assertEqual(
            resolve_manifest_path(Path("outputs/example")),
            Path("outputs/example/application_manifest.json"),
        )

    def test_missing_required_output_files_lists_absent_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "resume.md").write_text("Resume", encoding="utf-8")

            missing = missing_required_output_files(output_dir)

            self.assertIn("cover_letter.md", missing)
            self.assertIn("application_manifest.json", missing)

    def test_check_readiness_reports_ready_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = write_ready_package(Path(temp_dir))

            result = check_readiness(manifest_path)

            self.assertTrue(result.is_ready)
            self.assertEqual(result.errors, [])
            self.assertIn("Optional AI recruiter review was not found.", result.warnings)

    def test_check_readiness_reports_missing_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            manifest_path = write_ready_package(output_dir)
            (output_dir / "cover_letter.md").unlink()

            result = check_readiness(manifest_path)

            self.assertFalse(result.is_ready)
            self.assertTrue(any("cover_letter.md" in error for error in result.errors))

    def test_build_readiness_report_includes_status_and_final_action(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = check_readiness(write_ready_package(Path(temp_dir)))

            report = build_readiness_report(result)

            self.assertIn("Ready To Apply Report", report)
            self.assertIn("Status: Ready with warnings", report)
            self.assertIn("Package is ready", report)

    def test_readiness_report_path_lives_beside_manifest(self) -> None:
        self.assertEqual(
            readiness_report_path(Path("outputs/example/application_manifest.json")),
            Path("outputs/example/ready_to_apply_report.md"),
        )


if __name__ == "__main__":
    unittest.main()

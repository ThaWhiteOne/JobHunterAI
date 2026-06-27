import json
import tempfile
import unittest
from pathlib import Path

from automation_unit import (
    build_check_report,
    load_manifest,
    missing_required_keys,
    run_check,
)


class AutomationUnitTests(unittest.TestCase):
    def test_missing_required_keys_reports_absent_fields(self) -> None:
        missing_keys = missing_required_keys({"detected_role": "support"})

        self.assertIn("generated_files", missing_keys)
        self.assertIn("automation_guardrails", missing_keys)

    def test_run_check_reports_manifest_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            resume_path = temp_path / "resume.md"
            manifest_path = temp_path / "application_manifest.json"
            resume_path.write_text("# Resume", encoding="utf-8")
            manifest_path.write_text(
                json.dumps(
                    {
                        "detected_role": "support",
                        "role_display_name": "Technical Support / Application Support",
                        "generated_files": [resume_path.as_posix()],
                        "tracked_job_id": None,
                        "automation_guardrails": [
                            "Do not submit applications automatically without user confirmation."
                        ],
                        "next_manual_step": "Review generated drafts before applying.",
                    }
                ),
                encoding="utf-8",
            )

            report = run_check(manifest_path)

            self.assertIn("Automation Unit check complete.", report)
            self.assertIn("Detected role: support", report)
            self.assertIn("Missing generated files: none", report)
            self.assertIn("Do not submit applications automatically", report)

    def test_build_check_report_lists_missing_files(self) -> None:
        manifest = {
            "detected_role": "developer",
            "role_display_name": "Junior Python / Web Developer",
            "generated_files": ["missing.md"],
            "automation_guardrails": [],
            "next_manual_step": "Review generated drafts before applying.",
        }

        report = build_check_report(manifest, Path("application_manifest.json"))

        self.assertIn("Missing generated files: missing.md", report)

    def test_load_manifest_rejects_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            manifest_path = Path(temp_dir) / "application_manifest.json"
            manifest_path.write_text("{", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_manifest(manifest_path)


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from job_analyzer import JobAnalysis
from manifest_builder import generate_manifest


class ManifestBuilderTests(unittest.TestCase):
    def test_generate_manifest_returns_machine_readable_json(self) -> None:
        manifest_text = generate_manifest(
            job_path=Path("examples/sample_job.txt"),
            output_dir=Path("outputs/example-ltd-support-engineer"),
            role="support",
            role_display_name="Technical Support / Application Support",
            scores={"support": 3, "developer": 0, "cybersecurity": 0},
            profile_path=Path("profiles/support_cv.md"),
            used_fallback_profile=False,
            job_analysis=JobAnalysis(
                role="support",
                matched_keywords=["support", "sql"],
                requirement_lines=["SQL", "Troubleshooting"],
            ),
            generated_files=[Path("outputs/example/resume.md")],
            manifest_path=Path("outputs/example/application_manifest.json"),
            tracked_job_id=5,
        )

        manifest = json.loads(manifest_text)

        self.assertEqual(manifest["detected_role"], "support")
        self.assertEqual(manifest["tracked_job_id"], 5)
        self.assertIn("support", manifest["matched_keywords"])
        self.assertIn("outputs/example/resume.md", manifest["generated_files"])
        self.assertIn(
            "outputs/example/application_manifest.json",
            manifest["generated_files"],
        )
        self.assertIn(
            "Do not submit applications automatically without user confirmation.",
            manifest["automation_guardrails"],
        )


if __name__ == "__main__":
    unittest.main()

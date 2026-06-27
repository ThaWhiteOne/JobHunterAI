import json
import tempfile
import unittest
from pathlib import Path

from draft_reviewer import (
    build_recruiter_review_report,
    recruiter_review_path,
    review_drafts,
)


def write_manifest(temp_path: Path, generated_files: list[Path]) -> Path:
    manifest_path = temp_path / "application_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "detected_role": "support",
                "role_display_name": "Technical Support / Application Support",
                "matched_keywords": ["sql", "troubleshooting", "customer support"],
                "generated_files": [path.as_posix() for path in generated_files],
                "automation_guardrails": [
                    "Do not submit applications automatically without user confirmation."
                ],
                "next_manual_step": "Review generated drafts before applying.",
            }
        ),
        encoding="utf-8",
    )
    return manifest_path


class DraftReviewerTests(unittest.TestCase):
    def test_review_drafts_flags_placeholders_and_missing_keywords(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            resume_path = temp_path / "resume.md"
            cover_path = temp_path / "cover_letter.md"
            linkedin_path = temp_path / "linkedin_message.txt"
            resume_path.write_text("# Resume\n\nTODO [company]", encoding="utf-8")
            cover_path.write_text("Dear Hiring Manager,\n\nShort.", encoding="utf-8")
            linkedin_path.write_text("Hello.", encoding="utf-8")
            manifest_path = write_manifest(
                temp_path,
                [resume_path, cover_path, linkedin_path],
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            review = review_drafts(manifest, manifest_path)

            titles = [finding.title for finding in review.findings]
            self.assertIn("Placeholder text found", titles)
            self.assertIn("No matched job keywords appear in drafts", titles)
            self.assertLess(review.score, 100)

    def test_build_recruiter_review_report_includes_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            resume_path = temp_path / "resume.md"
            cover_path = temp_path / "cover_letter.md"
            linkedin_path = temp_path / "linkedin_message.txt"
            resume_path.write_text(
                "# Resume\n\nSQL troubleshooting customer support " * 30,
                encoding="utf-8",
            )
            cover_path.write_text(
                "Dear Hiring Manager,\n\nI can support SQL troubleshooting and customer support work. "
                * 10,
                encoding="utf-8",
            )
            linkedin_path.write_text(
                "Hello, I am interested in this support role.",
                encoding="utf-8",
            )
            manifest_path = write_manifest(
                temp_path,
                [resume_path, cover_path, linkedin_path],
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            report = build_recruiter_review_report(manifest, manifest_path)

            self.assertIn("# Recruiter Review Agent Report", report)
            self.assertIn("Score:", report)
            self.assertIn("Status:", report)
            self.assertIn("Automation guardrails are present", report)
            self.assertEqual(
                recruiter_review_path(manifest_path),
                temp_path / "recruiter_review.md",
            )


if __name__ == "__main__":
    unittest.main()

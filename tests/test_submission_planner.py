import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from submission_planner import (
    build_submission_plan,
    load_packet,
    packet_has_blockers,
    packet_has_warnings,
    resolve_packet_path,
    submission_plan_path,
)


def sample_packet() -> dict[str, Any]:
    return {
        "submission_status": "prepared_not_submitted",
        "automation_allowed": False,
        "readiness": {
            "status": "Ready with warnings",
            "score": 92,
            "is_ready": True,
            "errors": [],
            "warnings": ["Optional AI recruiter review was not found."],
        },
        "job": {
            "job_path": "jobs/example.txt",
            "job_url": "https://example.com/job",
            "detected_role": "support",
            "role_display_name": "Technical Support / Application Support",
        },
        "files": {
            "resume_markdown": "outputs/example/resume.md",
            "cover_letter_markdown": "outputs/example/cover_letter.md",
            "linkedin_message": "outputs/example/linkedin_message.txt",
            "ready_to_apply_report": "outputs/example/ready_to_apply_report.md",
            "recruiter_review": "outputs/example/recruiter_review.md",
            "automation_report": "outputs/example/automation_report.md",
        },
        "guardrails": [
            "Do not submit applications automatically without user confirmation."
        ],
    }


class SubmissionPlannerTests(unittest.TestCase):
    def test_resolve_packet_path_accepts_output_folder(self) -> None:
        self.assertEqual(
            resolve_packet_path(Path("outputs/example")),
            Path("outputs/example/application_packet.json"),
        )

    def test_load_packet_rejects_missing_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet_path = Path(temp_dir) / "application_packet.json"
            packet_path.write_text(json.dumps({"readiness": {}}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_packet(packet_path)

    def test_load_packet_reads_valid_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            packet_path = Path(temp_dir) / "application_packet.json"
            packet_path.write_text(json.dumps(sample_packet()), encoding="utf-8")

            packet = load_packet(Path(temp_dir))

            self.assertEqual(packet["job"]["detected_role"], "support")

    def test_build_submission_plan_includes_files_and_non_submit_boundary(self) -> None:
        packet_path = Path("outputs/example/application_packet.json")

        plan = build_submission_plan(sample_packet(), packet_path)

        self.assertIn("Submission Plan", plan)
        self.assertIn("https://example.com/job", plan)
        self.assertIn("outputs/example/resume.md", plan)
        self.assertIn("It does not submit applications", plan)
        self.assertIn("automation_allowed to false", plan)

    def test_packet_status_helpers_detect_blockers_and_warnings(self) -> None:
        packet = sample_packet()

        self.assertFalse(packet_has_blockers(packet))
        self.assertTrue(packet_has_warnings(packet))

        packet["readiness"]["errors"] = ["Missing resume."]

        self.assertTrue(packet_has_blockers(packet))

    def test_submission_plan_path_lives_beside_packet(self) -> None:
        self.assertEqual(
            submission_plan_path(Path("outputs/example/application_packet.json")),
            Path("outputs/example/submission_plan.md"),
        )


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

from form_fill_planner import (
    build_form_fill_plan,
    build_markdown_report,
    field_action,
    json_plan_path,
    markdown_plan_path,
    parse_profile_fields,
    select_document,
)
from tests.test_submission_planner import sample_packet


SAMPLE_PROFILE = """Name: Example Candidate

Location:
Plovdiv, Bulgaria

Age:
21

Email:
candidate@example.com

Phone:
+359123456789

GitHub:
https://github.com/example

LinkedIn:
(Later)
"""


class FormFillPlannerTests(unittest.TestCase):
    def test_parse_profile_fields_reads_contact_fields_and_ignores_age(self) -> None:
        fields = parse_profile_fields(SAMPLE_PROFILE)

        self.assertEqual(fields["full_name"], "Example Candidate")
        self.assertEqual(fields["location"], "Plovdiv, Bulgaria")
        self.assertEqual(fields["email"], "candidate@example.com")
        self.assertEqual(fields["phone"], "+359123456789")
        self.assertEqual(fields["github"], "https://github.com/example")
        self.assertNotIn("age", fields)

    def test_field_action_flags_unfinished_profile_values(self) -> None:
        self.assertEqual(field_action("(Later)"), "needs_profile_update")
        self.assertEqual(field_action(""), "needs_profile_update")
        self.assertEqual(field_action("candidate@example.com"), "fill")

    def test_select_document_prefers_first_available_choice(self) -> None:
        document = select_document(
            {
                "resume_markdown": "outputs/example/resume.md",
                "resume_docx": "outputs/example/resume.docx",
            },
            ["resume_docx", "resume_pdf", "resume_markdown"],
        )

        self.assertEqual(document["file_key"], "resume_docx")
        self.assertEqual(document["action"], "upload")

    def test_build_form_fill_plan_includes_safe_fields_and_guardrails(self) -> None:
        packet = sample_packet()
        packet["files"]["resume_docx"] = "outputs/example/resume.docx"
        profile_fields = parse_profile_fields(SAMPLE_PROFILE)

        plan = build_form_fill_plan(packet, profile_fields)

        field_names = [field["field"] for field in plan["contact_fields"]]
        self.assertIn("full_name", field_names)
        self.assertNotIn("age", field_names)
        self.assertFalse(plan["submission_allowed"])
        self.assertTrue(plan["stop_before_submit"])
        self.assertEqual(plan["document_uploads"]["resume"]["file_key"], "resume_docx")
        linkedin_field = next(
            field for field in plan["contact_fields"] if field["field"] == "linkedin"
        )
        self.assertEqual(linkedin_field["value"], "")
        self.assertEqual(linkedin_field["action"], "needs_profile_update")
        self.assertIn("Do not submit the application automatically.", plan["guardrails"])

    def test_build_markdown_report_describes_non_submitting_plan(self) -> None:
        packet = sample_packet()
        plan = build_form_fill_plan(packet, parse_profile_fields(SAMPLE_PROFILE))

        report = build_markdown_report(
            plan,
            Path("outputs/example/application_packet.json"),
        )

        self.assertIn("Form Fill Plan", report)
        self.assertIn("does not fill forms or submit applications", report)
        self.assertIn("linkedin: needs_profile_update", report)

    def test_plan_paths_live_beside_packet(self) -> None:
        packet_path = Path("outputs/example/application_packet.json")

        self.assertEqual(
            json_plan_path(packet_path),
            Path("outputs/example/form_fill_plan.json"),
        )
        self.assertEqual(
            markdown_plan_path(packet_path),
            Path("outputs/example/form_fill_plan.md"),
        )

    def test_plan_json_can_be_written_and_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "form_fill_plan.json"
            plan = build_form_fill_plan(
                sample_packet(),
                parse_profile_fields(SAMPLE_PROFILE),
            )
            path.write_text(json.dumps(plan), encoding="utf-8")

            loaded = json.loads(path.read_text(encoding="utf-8"))

            self.assertFalse(loaded["submission_allowed"])


if __name__ == "__main__":
    unittest.main()

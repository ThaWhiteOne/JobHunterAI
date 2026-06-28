import json
import tempfile
import unittest
from pathlib import Path

from apply_readiness_gate import (
    apply_readiness_report_path,
    build_apply_readiness_report,
    check_apply_readiness,
    load_form_fill_plan,
    resolve_form_fill_plan_path,
    validate_answers,
    validate_contact_fields,
    validate_documents,
    validate_guardrails,
)
from form_fill_planner import (
    build_form_fill_plan,
    parse_application_answers,
    parse_profile_fields,
)
from tests.test_form_fill_planner import SAMPLE_ANSWERS, SAMPLE_PROFILE
from tests.test_submission_planner import sample_packet


def ready_plan() -> dict:
    packet = sample_packet()
    packet["files"]["resume_docx"] = "outputs/example/resume.docx"
    packet["files"]["cover_letter_docx"] = "outputs/example/cover_letter.docx"
    return build_form_fill_plan(
        packet,
        parse_profile_fields(SAMPLE_PROFILE),
        parse_application_answers(SAMPLE_ANSWERS),
    )


class ApplyReadinessGateTests(unittest.TestCase):
    def test_resolve_form_fill_plan_path_accepts_output_folder(self) -> None:
        self.assertEqual(
            resolve_form_fill_plan_path(Path("outputs/example")),
            Path("outputs/example/form_fill_plan.json"),
        )

    def test_load_form_fill_plan_rejects_missing_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "form_fill_plan.json"
            plan_path.write_text(json.dumps({"contact_fields": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_form_fill_plan(plan_path)

    def test_validate_contact_fields_blocks_required_missing_values(self) -> None:
        plan = ready_plan()
        email = next(field for field in plan["contact_fields"] if field["field"] == "email")
        email["value"] = ""
        email["action"] = "needs_profile_update"

        errors, warnings = validate_contact_fields(plan)

        self.assertTrue(any("email" in error for error in errors))
        self.assertTrue(any("linkedin" in warning for warning in warnings))

    def test_validate_documents_blocks_missing_resume(self) -> None:
        plan = ready_plan()
        plan["document_uploads"]["resume"] = {
            "file_key": "",
            "path": "",
            "action": "missing",
        }

        errors = validate_documents(plan)

        self.assertTrue(any("resume" in error for error in errors))

    def test_validate_answers_blocks_missing_required_answers(self) -> None:
        plan = build_form_fill_plan(sample_packet(), parse_profile_fields(SAMPLE_PROFILE))

        errors, warnings = validate_answers(plan)

        self.assertTrue(any("work_authorization" in error for error in errors))
        self.assertTrue(any("salary_expectation" in warning for warning in warnings))

    def test_validate_guardrails_requires_stop_before_submit(self) -> None:
        plan = ready_plan()
        plan["stop_before_submit"] = False

        errors, _warnings = validate_guardrails(plan)

        self.assertTrue(any("stop_before_submit" in error for error in errors))

    def test_check_apply_readiness_reports_ready_plan_with_optional_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "form_fill_plan.json"
            plan_path.write_text(json.dumps(ready_plan()), encoding="utf-8")

            result = check_apply_readiness(plan_path)

            self.assertTrue(result.is_ready)
            self.assertEqual(result.status, "Ready with warnings")
            self.assertTrue(any("linkedin" in warning for warning in result.warnings))

    def test_build_apply_readiness_report_describes_non_submitting_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "form_fill_plan.json"
            plan_path.write_text(json.dumps(ready_plan()), encoding="utf-8")
            result = check_apply_readiness(plan_path)

            report = build_apply_readiness_report(result)

            self.assertIn("Apply Readiness Report", report)
            self.assertIn("does not fill forms", report)

    def test_apply_readiness_report_path_lives_beside_plan(self) -> None:
        self.assertEqual(
            apply_readiness_report_path(Path("outputs/example/form_fill_plan.json")),
            Path("outputs/example/apply_readiness_report.md"),
        )


if __name__ == "__main__":
    unittest.main()

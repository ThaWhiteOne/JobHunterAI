import json
import tempfile
import unittest
from pathlib import Path

from apply_readiness_gate import check_apply_readiness
from browser_dry_run import (
    browser_dry_run_json_path,
    browser_dry_run_markdown_path,
    build_browser_actions,
    build_browser_dry_run,
    build_markdown_report,
    plan_job_url,
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


class BrowserDryRunTests(unittest.TestCase):
    def test_plan_job_url_ignores_not_provided(self) -> None:
        plan = ready_plan()
        plan["job"]["job_url"] = "not provided"

        self.assertEqual(plan_job_url(plan), "")

    def test_build_browser_actions_keeps_submit_as_stop_action(self) -> None:
        actions = build_browser_actions(ready_plan())

        action_names = [item["action"] for item in actions]

        self.assertIn("open_job_page", action_names)
        self.assertIn("fill_contact_field", action_names)
        self.assertIn("upload_document", action_names)
        self.assertEqual(actions[-1]["action"], "stop_before_submit")
        self.assertEqual(actions[-1]["status"], "stop")

    def test_build_browser_dry_run_marks_ready_plan_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "form_fill_plan.json"
            plan = ready_plan()
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            readiness = check_apply_readiness(plan_path)

            dry_run = build_browser_dry_run(plan, readiness)

            self.assertEqual(dry_run["status"], "ready")
            self.assertFalse(dry_run["submission_allowed"])
            self.assertTrue(dry_run["stop_before_submit"])

    def test_build_browser_dry_run_marks_missing_answers_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "form_fill_plan.json"
            plan = build_form_fill_plan(sample_packet(), parse_profile_fields(SAMPLE_PROFILE))
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            readiness = check_apply_readiness(plan_path)

            dry_run = build_browser_dry_run(plan, readiness)

            self.assertEqual(dry_run["status"], "blocked")
            self.assertTrue(dry_run["readiness"]["errors"])

    def test_build_markdown_report_describes_non_submitting_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = Path(temp_dir) / "form_fill_plan.json"
            plan = ready_plan()
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            dry_run = build_browser_dry_run(plan, check_apply_readiness(plan_path))

            report = build_markdown_report(dry_run, plan_path)

            self.assertIn("Browser Automation Dry Run", report)
            self.assertIn("Status: Ready", report)
            self.assertIn("does not open browsers", report)
            self.assertIn("stop_before_submit", report)

    def test_dry_run_paths_live_beside_form_fill_plan(self) -> None:
        plan_path = Path("outputs/example/form_fill_plan.json")

        self.assertEqual(
            browser_dry_run_json_path(plan_path),
            Path("outputs/example/browser_dry_run.json"),
        )
        self.assertEqual(
            browser_dry_run_markdown_path(plan_path),
            Path("outputs/example/browser_dry_run.md"),
        )


if __name__ == "__main__":
    unittest.main()

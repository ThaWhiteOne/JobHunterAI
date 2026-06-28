import json
import tempfile
import unittest
from pathlib import Path

from page_action_plan import (
    action_plan_json_path,
    action_plan_markdown_path,
    build_markdown_report,
    build_page_action_plan,
    build_plan_step,
    resolve_page_inspection_path,
    selector_for_field,
)
from page_inspector import build_inspection
from tests.test_page_inspector import SAMPLE_HTML, sample_dry_run


def sample_inspection() -> dict:
    return build_inspection(sample_dry_run(), SAMPLE_HTML, "sample.html")


class PageActionPlanTests(unittest.TestCase):
    def test_resolve_page_inspection_path_accepts_output_folder(self) -> None:
        self.assertEqual(
            resolve_page_inspection_path(Path("outputs/example")),
            Path("outputs/example/page_inspection.json"),
        )

    def test_selector_for_field_prefers_id_then_name(self) -> None:
        self.assertEqual(
            selector_for_field({"id": "email", "name": "candidate_email"}),
            "#email",
        )
        self.assertEqual(
            selector_for_field({"id": "", "name": "candidate_email"}),
            "[name='candidate_email']",
        )

    def test_build_plan_step_marks_matched_action_ready(self) -> None:
        match = sample_inspection()["matches"][0]

        step = build_plan_step(match)

        self.assertEqual(step["status"], "ready")
        self.assertTrue(step["selector"])
        self.assertFalse(step["execute_automatically"])

    def test_build_plan_step_marks_submit_as_stop(self) -> None:
        submit_match = sample_inspection()["matches"][-1]

        step = build_plan_step(submit_match)

        self.assertEqual(step["status"], "stop")
        self.assertEqual(step["target"], "final_submit_button")

    def test_build_page_action_plan_keeps_submission_disabled(self) -> None:
        plan = build_page_action_plan(sample_inspection())

        self.assertEqual(plan["status"], "ready_for_review")
        self.assertFalse(plan["submission_allowed"])
        self.assertTrue(plan["stop_before_submit"])
        self.assertGreaterEqual(plan["ready_steps"], 4)

    def test_build_page_action_plan_reports_missing_selectors(self) -> None:
        inspection = sample_inspection()
        inspection["matches"][0]["status"] = "missing_on_page"
        inspection["matches"][0]["field_details"] = {}

        plan = build_page_action_plan(inspection)

        self.assertEqual(plan["status"], "needs_review")
        self.assertGreater(plan["needs_review_steps"], 0)

    def test_build_markdown_report_describes_non_executing_plan(self) -> None:
        report = build_markdown_report(build_page_action_plan(sample_inspection()))

        self.assertIn("Page Action Plan", report)
        self.assertIn("does not fill fields", report)
        self.assertIn("Execute automatically: False", report)

    def test_action_plan_paths_live_beside_page_inspection(self) -> None:
        inspection_path = Path("outputs/example/page_inspection.json")

        self.assertEqual(
            action_plan_json_path(inspection_path),
            Path("outputs/example/page_action_plan.json"),
        )
        self.assertEqual(
            action_plan_markdown_path(inspection_path),
            Path("outputs/example/page_action_plan.md"),
        )

    def test_page_inspection_json_can_feed_action_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            inspection_path = Path(temp_dir) / "page_inspection.json"
            inspection_path.write_text(
                json.dumps(sample_inspection()),
                encoding="utf-8",
            )
            loaded = json.loads(inspection_path.read_text(encoding="utf-8"))

            plan = build_page_action_plan(loaded)

            self.assertEqual(plan["source"], "sample.html")


if __name__ == "__main__":
    unittest.main()

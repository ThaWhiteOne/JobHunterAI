import json
import tempfile
import unittest
from pathlib import Path

from page_action_gate import (
    build_page_action_gate_report,
    check_page_action_plan,
    load_page_action_plan,
    page_action_gate_report_path,
    resolve_page_action_plan_path,
    validate_guardrails,
    validate_steps,
)
from tests.test_page_action_plan import sample_inspection
from page_action_plan import build_page_action_plan


def ready_action_plan() -> dict:
    return build_page_action_plan(sample_inspection())


class PageActionGateTests(unittest.TestCase):
    def test_resolve_page_action_plan_path_accepts_output_folder(self) -> None:
        self.assertEqual(
            resolve_page_action_plan_path(Path("outputs/example")),
            Path("outputs/example/page_action_plan.json"),
        )

    def test_load_page_action_plan_rejects_missing_required_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "page_action_plan.json"
            path.write_text(json.dumps({"steps": []}), encoding="utf-8")

            with self.assertRaises(ValueError):
                load_page_action_plan(path)

    def test_validate_guardrails_requires_non_executing_plan(self) -> None:
        plan = ready_action_plan()
        plan["execute_automatically"] = True

        errors, warnings = validate_guardrails(plan)

        self.assertIn("execute_automatically", "\n".join(errors))
        self.assertEqual(warnings, [])

    def test_validate_steps_requires_stop_step(self) -> None:
        plan = ready_action_plan()
        plan["steps"] = [
            step for step in plan["steps"] if step["status"] != "stop"
        ]

        errors, warnings = validate_steps(plan)

        self.assertIn("stop step", "\n".join(errors))
        self.assertEqual(warnings, [])

    def test_check_page_action_plan_marks_ready_plan_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "page_action_plan.json"
            path.write_text(json.dumps(ready_action_plan()), encoding="utf-8")

            result = check_page_action_plan(path)

            self.assertTrue(result.is_ready)
            self.assertEqual(result.status, "Ready")

    def test_check_page_action_plan_marks_needs_review_as_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = ready_action_plan()
            plan["steps"][0]["status"] = "needs_review"
            plan["needs_review_steps"] = 1
            path = Path(temp_dir) / "page_action_plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")

            result = check_page_action_plan(path)

            self.assertFalse(result.is_ready)
            self.assertEqual(result.status, "Not ready")

    def test_build_page_action_gate_report_includes_stop_line(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "page_action_plan.json"
            path.write_text(json.dumps(ready_action_plan()), encoding="utf-8")
            result = check_page_action_plan(path)

            report = build_page_action_gate_report(result)

            self.assertIn("Page Action Gate Report", report)
            self.assertIn("Status: Ready", report)
            self.assertIn("Do not execute browser actions yet", report)

    def test_page_action_gate_report_path_lives_beside_plan(self) -> None:
        self.assertEqual(
            page_action_gate_report_path(Path("outputs/example/page_action_plan.json")),
            Path("outputs/example/page_action_gate_report.md"),
        )


if __name__ == "__main__":
    unittest.main()

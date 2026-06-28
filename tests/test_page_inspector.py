import json
import tempfile
import unittest
from pathlib import Path

from page_inspector import (
    build_inspection,
    build_markdown_report,
    inspection_json_path,
    inspection_markdown_path,
    match_actions_to_fields,
    parse_html_fields,
    resolve_dry_run_path,
)


SAMPLE_HTML = """
<html>
  <body>
    <form>
      <label for="full-name">Full name</label>
      <input id="full-name" name="candidate_name" type="text">

      <label>Email address <input name="email" type="email"></label>

      <label for="phone">Phone</label>
      <input id="phone" name="phone" type="tel">

      <label for="resume">Upload CV or resume</label>
      <input id="resume" name="resume_file" type="file">

      <label for="authorization">Work authorization</label>
      <select id="authorization" name="work_auth"></select>

      <textarea name="cover_letter" aria-label="Cover letter"></textarea>
      <button type="submit">Submit application</button>
    </form>
  </body>
</html>
"""


def sample_dry_run() -> dict:
    return {
        "status": "ready",
        "submission_allowed": False,
        "stop_before_submit": True,
        "job": {"job_url": "https://example.com/job"},
        "readiness": {"status": "Ready", "errors": [], "warnings": []},
        "actions": [
            {
                "step": 1,
                "action": "fill_contact_field",
                "target": "full_name",
                "status": "ready",
                "value": "Example Candidate",
            },
            {
                "step": 2,
                "action": "fill_contact_field",
                "target": "email",
                "status": "ready",
                "value": "candidate@example.com",
            },
            {
                "step": 3,
                "action": "upload_document",
                "target": "resume",
                "status": "ready",
                "value": "outputs/example/resume.docx",
            },
            {
                "step": 4,
                "action": "fill_application_answer",
                "target": "Work authorization",
                "status": "ready",
                "value": "Eligible to work in Bulgaria",
            },
            {
                "step": 5,
                "action": "stop_before_submit",
                "target": "final_submit_button",
                "status": "stop",
                "value": "",
            },
        ],
        "guardrails": ["Do not submit applications automatically."],
    }


class PageInspectorTests(unittest.TestCase):
    def test_resolve_dry_run_path_accepts_output_folder(self) -> None:
        self.assertEqual(
            resolve_dry_run_path(Path("outputs/example")),
            Path("outputs/example/browser_dry_run.json"),
        )

    def test_parse_html_fields_reads_form_fields_and_submit_buttons(self) -> None:
        fields = parse_html_fields(SAMPLE_HTML)
        labels = [field.label for field in fields]

        self.assertIn("Full name", labels)
        self.assertIn("Email address", labels)
        self.assertIn("Upload CV or resume", labels)
        self.assertIn("Submit application", labels)

    def test_match_actions_to_fields_matches_safe_actions(self) -> None:
        fields = parse_html_fields(SAMPLE_HTML)
        matches = match_actions_to_fields(sample_dry_run()["actions"], fields)
        statuses = {match["target"]: match["status"] for match in matches}

        self.assertEqual(statuses["full_name"], "matched")
        self.assertEqual(statuses["email"], "matched")
        self.assertEqual(statuses["resume"], "matched")
        self.assertEqual(statuses["Work authorization"], "matched")
        self.assertEqual(statuses["final_submit_button"], "stop_detected")

    def test_build_inspection_keeps_submission_disabled(self) -> None:
        inspection = build_inspection(sample_dry_run(), SAMPLE_HTML, "sample.html")

        self.assertEqual(inspection["status"], "ready_for_manual_review")
        self.assertFalse(inspection["submission_allowed"])
        self.assertTrue(inspection["stop_before_submit"])
        self.assertGreaterEqual(inspection["matched_actions"], 4)

    def test_build_inspection_reports_missing_fields(self) -> None:
        inspection = build_inspection(sample_dry_run(), "<form></form>", "blank.html")

        self.assertEqual(inspection["status"], "needs_review")
        self.assertGreater(inspection["missing_actions"], 0)

    def test_build_markdown_report_describes_non_filling_inspection(self) -> None:
        inspection = build_inspection(sample_dry_run(), SAMPLE_HTML, "sample.html")

        report = build_markdown_report(inspection)

        self.assertIn("Page Inspection Report", report)
        self.assertIn("does not fill fields", report)
        self.assertIn("final_submit_button", report)

    def test_inspection_paths_live_beside_dry_run(self) -> None:
        dry_run_path = Path("outputs/example/browser_dry_run.json")

        self.assertEqual(
            inspection_json_path(dry_run_path),
            Path("outputs/example/page_inspection.json"),
        )
        self.assertEqual(
            inspection_markdown_path(dry_run_path),
            Path("outputs/example/page_inspection.md"),
        )

    def test_dry_run_json_can_feed_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            dry_run_path = Path(temp_dir) / "browser_dry_run.json"
            dry_run_path.write_text(json.dumps(sample_dry_run()), encoding="utf-8")

            loaded = json.loads(dry_run_path.read_text(encoding="utf-8"))
            inspection = build_inspection(loaded, SAMPLE_HTML, "sample.html")

            self.assertEqual(inspection["detected_fields"], 7)


if __name__ == "__main__":
    unittest.main()

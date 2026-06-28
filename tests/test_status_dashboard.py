import json
import tempfile
import unittest
from pathlib import Path

from status_dashboard import (
    build_status_dashboard,
    dashboard_path,
    discover_output_dirs,
    first_status_line,
    read_json,
    summarize_output_dir,
)


def write_output_dir(path: Path, role: str = "support", apply_status: str = "Ready") -> None:
    path.mkdir(parents=True, exist_ok=True)
    manifest = {
        "detected_role": role,
        "role_display_name": "Technical Support / Application Support",
    }
    (path / "application_manifest.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )
    (path / "resume.md").write_text("Resume", encoding="utf-8")
    (path / "cover_letter.md").write_text("Cover", encoding="utf-8")
    (path / "linkedin_message.txt").write_text("Message", encoding="utf-8")
    (path / "application_packet.json").write_text("{}", encoding="utf-8")
    (path / "browser_dry_run.json").write_text("{}", encoding="utf-8")
    (path / "browser_dry_run.md").write_text(
        "# Browser Automation Dry Run\n\nStatus: Ready\n",
        encoding="utf-8",
    )
    (path / "browser_review_session.md").write_text(
        "# Browser Review Session\n\nStatus: Prepared, not submitted\n",
        encoding="utf-8",
    )
    (path / "page_inspection.json").write_text("{}", encoding="utf-8")
    (path / "page_inspection.md").write_text(
        "# Page Inspection Report\n\nStatus: Ready for manual review\n",
        encoding="utf-8",
    )
    (path / "page_action_plan.json").write_text("{}", encoding="utf-8")
    (path / "page_action_plan.md").write_text(
        "# Page Action Plan\n\nStatus: Ready for review\n",
        encoding="utf-8",
    )
    (path / "page_action_gate_report.md").write_text(
        "# Page Action Gate Report\n\nStatus: Ready\n",
        encoding="utf-8",
    )
    (path / "apply_readiness_report.md").write_text(
        f"# Apply Readiness Report\n\nStatus: {apply_status}\n",
        encoding="utf-8",
    )
    (path / "pipeline_report.md").write_text(
        "# Pipeline Report\n\nStatus: Complete\n",
        encoding="utf-8",
    )


class StatusDashboardTests(unittest.TestCase):
    def test_first_status_line_reads_status_from_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "report.md"
            path.write_text("# Report\n\nStatus: Ready\n", encoding="utf-8")

            self.assertEqual(first_status_line(path), "Ready")

    def test_read_json_returns_empty_dict_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "bad.json"
            path.write_text("{bad", encoding="utf-8")

            self.assertEqual(read_json(path), {})

    def test_summarize_output_dir_reports_role_statuses_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "support"
            write_output_dir(output_dir)

            summary = summarize_output_dir(output_dir)

            self.assertEqual(summary.detected_role, "support")
            self.assertEqual(summary.statuses["apply_readiness"], "Ready")
            self.assertEqual(summary.statuses["browser_dry_run"], "Ready")
            self.assertEqual(
                summary.statuses["browser_review_session"],
                "Prepared, not submitted",
            )
            self.assertEqual(
                summary.statuses["page_inspection"],
                "Ready for manual review",
            )
            self.assertEqual(
                summary.statuses["page_action_plan"],
                "Ready for review",
            )
            self.assertEqual(summary.statuses["page_action_gate"], "Ready")
            self.assertTrue(summary.key_files["resume"])
            self.assertTrue(summary.key_files["browser_dry_run"])
            self.assertTrue(summary.key_files["browser_review_session"])
            self.assertTrue(summary.key_files["page_inspection"])
            self.assertTrue(summary.key_files["page_action_plan"])
            self.assertTrue(summary.key_files["page_action_gate"])
            self.assertEqual(summary.overall_status, "Ready")

    def test_summarize_output_dir_marks_not_ready_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "support"
            write_output_dir(output_dir, apply_status="Not ready")

            summary = summarize_output_dir(output_dir)

            self.assertEqual(summary.overall_status, "Blocked")

    def test_summarize_output_dir_marks_page_review_as_attention_needed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "support"
            write_output_dir(output_dir)
            (output_dir / "page_inspection.md").write_text(
                "# Page Inspection Report\n\nStatus: Needs review\n",
                encoding="utf-8",
            )

            summary = summarize_output_dir(output_dir)

            self.assertEqual(summary.overall_status, "Attention needed")

    def test_discover_output_dirs_finds_batch_children(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_output_dir(root / "a-job")
            write_output_dir(root / "b-job")

            output_dirs = discover_output_dirs(root)

            self.assertEqual([path.name for path in output_dirs], ["a-job", "b-job"])

    def test_build_status_dashboard_summarizes_multiple_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_output_dir(root / "ready-job")
            write_output_dir(root / "blocked-job", apply_status="Not ready")

            dashboard = build_status_dashboard(root)

            self.assertIn("JobHunterAI Status Dashboard", dashboard)
            self.assertIn("Output folders: 2", dashboard)
            self.assertIn("Ready: 1", dashboard)
            self.assertIn("Blocked: 1", dashboard)

    def test_dashboard_path_lives_in_selected_folder(self) -> None:
        self.assertEqual(
            dashboard_path(Path("outputs/batch")),
            Path("outputs/batch/status_dashboard.md"),
        )


if __name__ == "__main__":
    unittest.main()

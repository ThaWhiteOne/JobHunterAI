import json
import tempfile
import unittest
from pathlib import Path

from application_packet import (
    build_application_packet,
    existing_file_map,
    extract_job_url,
    packet_path,
    read_first_line_value,
)
from tests.test_readiness_checker import write_ready_package


class ApplicationPacketTests(unittest.TestCase):
    def test_existing_file_map_returns_present_files_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "resume.md").write_text("Resume", encoding="utf-8")

            files = existing_file_map(
                output_dir,
                {
                    "resume": "resume.md",
                    "missing": "missing.md",
                },
            )

            self.assertIn("resume", files)
            self.assertNotIn("missing", files)

    def test_read_first_line_value_reads_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "job.txt"
            path.write_text("URL: https://example.com/job\nBody", encoding="utf-8")

            value = read_first_line_value(path, "URL")

            self.assertEqual(value, "https://example.com/job")

    def test_extract_job_url_prefers_saved_output_job_description(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            manifest_path = write_ready_package(output_dir)
            (output_dir / "job_description.txt").write_text(
                "URL: https://example.com/job\n\nJob Description:\nSupport",
                encoding="utf-8",
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

            url = extract_job_url(manifest, manifest_path)

            self.assertEqual(url, "https://example.com/job")

    def test_build_application_packet_includes_readiness_job_files_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            manifest_path = write_ready_package(output_dir)

            packet = build_application_packet(manifest_path)

            self.assertEqual(packet["submission_status"], "prepared_not_submitted")
            self.assertFalse(packet["automation_allowed"])
            self.assertTrue(packet["readiness"]["is_ready"])
            self.assertEqual(packet["job"]["detected_role"], "support")
            self.assertIn("resume_markdown", packet["files"])
            self.assertIn("Do not submit applications automatically", packet["guardrails"][0])

    def test_packet_path_lives_beside_manifest(self) -> None:
        self.assertEqual(
            packet_path(Path("outputs/example/application_manifest.json")),
            Path("outputs/example/application_packet.json"),
        )


if __name__ == "__main__":
    unittest.main()

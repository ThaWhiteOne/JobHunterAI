import json
import tempfile
import unittest
from pathlib import Path

from job_intake import (
    build_job_file_content,
    format_job_line,
    index_path,
    list_saved_jobs,
    read_job_text,
    save_job_description,
    slugify,
    unique_job_path,
)


class JobIntakeTests(unittest.TestCase):
    def test_slugify_creates_safe_filename_parts(self) -> None:
        self.assertEqual(slugify("Example Ltd / Support Engineer"), "example-ltd-support-engineer")

    def test_unique_job_path_adds_counter_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            existing = jobs_dir / "example-ltd-support-engineer.txt"
            existing.write_text("existing", encoding="utf-8")

            path = unique_job_path(jobs_dir, "Example Ltd", "Support Engineer")

            self.assertEqual(path.name, "example-ltd-support-engineer-2.txt")

    def test_build_job_file_content_includes_metadata_and_description(self) -> None:
        content = build_job_file_content(
            "Example Ltd",
            "Support Engineer",
            "https://example.com/job",
            "manual",
            "2026-01-01T00:00:00+00:00",
            "Technical Support Engineer with SQL",
        )

        self.assertIn("Company: Example Ltd", content)
        self.assertIn("Position: Support Engineer", content)
        self.assertIn("Technical Support Engineer with SQL", content)

    def test_read_job_text_rejects_text_and_file_together(self) -> None:
        with self.assertRaises(ValueError):
            read_job_text("Job text", Path("job.txt"))

    def test_read_job_text_reads_from_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            job_path = Path(temp_dir) / "job.txt"
            job_path.write_text("Junior Python Developer", encoding="utf-8")

            text = read_job_text("", job_path)

            self.assertEqual(text, "Junior Python Developer")

    def test_save_job_description_writes_job_file_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)

            saved_job = save_job_description(
                company="Example Ltd",
                position="Support Engineer",
                url="https://example.com/job",
                source="manual",
                job_text="Technical Support Engineer, SQL, troubleshooting",
                jobs_dir=jobs_dir,
            )

            self.assertTrue(saved_job.job_file.exists())
            self.assertTrue(index_path(jobs_dir).exists())
            self.assertIn(
                "Technical Support Engineer",
                saved_job.job_file.read_text(encoding="utf-8"),
            )
            index = json.loads(index_path(jobs_dir).read_text(encoding="utf-8"))
            self.assertEqual(index["jobs"][0]["company"], "Example Ltd")

    def test_list_saved_jobs_reads_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir)
            save_job_description(
                company="Example Ltd",
                position="Support Engineer",
                job_text="Technical Support Engineer",
                jobs_dir=jobs_dir,
            )

            jobs = list_saved_jobs(jobs_dir)

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["position"], "Support Engineer")

    def test_format_job_line_is_human_readable(self) -> None:
        line = format_job_line(
            1,
            {
                "company": "Example Ltd",
                "position": "Support Engineer",
                "job_file": "jobs/example-ltd-support-engineer.txt",
            },
        )

        self.assertEqual(
            line,
            "1. Example Ltd - Support Engineer -> jobs/example-ltd-support-engineer.txt",
        )


if __name__ == "__main__":
    unittest.main()

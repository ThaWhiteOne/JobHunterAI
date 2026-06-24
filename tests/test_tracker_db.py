import tempfile
import unittest
from pathlib import Path

from tracker_db import add_job, list_jobs, update_job_status


class TrackerDatabaseTests(unittest.TestCase):
    def test_adds_and_lists_job(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"

            job_id = add_job(
                db_path,
                company="Example Ltd",
                position="Support Engineer",
                url="https://example.com/job",
                role="support",
                notes="Remote role",
            )
            jobs = list_jobs(db_path)

            self.assertEqual(job_id, 1)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["company"], "Example Ltd")
            self.assertEqual(jobs[0]["position"], "Support Engineer")
            self.assertEqual(jobs[0]["status"], "saved")

    def test_updates_job_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"
            job_id = add_job(db_path, company="Example Ltd", position="SOC Analyst")

            update_job_status(db_path, job_id, "applied")
            jobs = list_jobs(db_path)

            self.assertEqual(jobs[0]["status"], "applied")

    def test_rejects_invalid_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"

            with self.assertRaises(ValueError):
                add_job(
                    db_path,
                    company="Example Ltd",
                    position="Developer",
                    status="waiting",
                )

    def test_update_missing_job_raises_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"

            with self.assertRaises(ValueError):
                update_job_status(db_path, 99, "applied")


if __name__ == "__main__":
    unittest.main()

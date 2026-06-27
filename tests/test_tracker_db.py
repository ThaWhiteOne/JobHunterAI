import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path

from tracker_db import add_job, initialize_database, list_jobs, update_job_status


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
                output_dir="outputs/example-ltd-support-engineer",
            )
            jobs = list_jobs(db_path)

            self.assertEqual(job_id, 1)
            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["company"], "Example Ltd")
            self.assertEqual(jobs[0]["position"], "Support Engineer")
            self.assertEqual(jobs[0]["status"], "saved")
            self.assertEqual(
                jobs[0]["output_dir"],
                "outputs/example-ltd-support-engineer",
            )

    def test_updates_job_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"
            job_id = add_job(db_path, company="Example Ltd", position="SOC Analyst")

            update_job_status(db_path, job_id, "applied")
            jobs = list_jobs(db_path)

            self.assertEqual(jobs[0]["status"], "applied")

    def test_lists_jobs_by_status(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"
            add_job(
                db_path,
                company="Example Ltd",
                position="Support Engineer",
                status="saved",
            )
            add_job(
                db_path,
                company="Second Ltd",
                position="Python Developer",
                status="applied",
            )

            jobs = list_jobs(db_path, status_filter="applied")

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["company"], "Second Ltd")
            self.assertEqual(jobs[0]["status"], "applied")

    def test_lists_jobs_by_role(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"
            add_job(
                db_path,
                company="Example Ltd",
                position="Support Engineer",
                role="support",
            )
            add_job(
                db_path,
                company="Second Ltd",
                position="Python Developer",
                role="developer",
            )

            jobs = list_jobs(db_path, role_filter="developer")

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["company"], "Second Ltd")
            self.assertEqual(jobs[0]["role"], "developer")

    def test_lists_jobs_by_status_and_role(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"
            add_job(
                db_path,
                company="Example Ltd",
                position="Support Engineer",
                role="support",
                status="applied",
            )
            add_job(
                db_path,
                company="Second Ltd",
                position="Python Developer",
                role="developer",
                status="saved",
            )
            add_job(
                db_path,
                company="Third Ltd",
                position="Backend Developer",
                role="developer",
                status="applied",
            )

            jobs = list_jobs(
                db_path,
                status_filter="applied",
                role_filter="developer",
            )

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0]["company"], "Third Ltd")
            self.assertEqual(jobs[0]["status"], "applied")
            self.assertEqual(jobs[0]["role"], "developer")

    def test_rejects_invalid_list_status_filter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"

            with self.assertRaises(ValueError):
                list_jobs(db_path, status_filter="waiting")

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

    def test_initialize_database_adds_output_dir_to_existing_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"
            with closing(sqlite3.connect(db_path)) as connection:
                with connection:
                    connection.execute(
                        """
                        CREATE TABLE jobs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            company TEXT NOT NULL,
                            position TEXT NOT NULL,
                            url TEXT,
                            role TEXT,
                            status TEXT NOT NULL,
                            notes TEXT,
                            created_at TEXT NOT NULL
                        )
                        """
                    )

            initialize_database(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(jobs)").fetchall()
                }

            self.assertIn("output_dir", columns)


if __name__ == "__main__":
    unittest.main()

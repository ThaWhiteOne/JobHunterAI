import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def run_command(arguments: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *arguments],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_main_generates_files_with_custom_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("JobHunterAI finished successfully.", result.stdout)
            self.assertTrue((output_dir / "resume.md").exists())
            self.assertTrue((output_dir / "cover_letter.md").exists())
            self.assertTrue((output_dir / "linkedin_message.txt").exists())

    def test_main_can_save_original_job_description(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--save-job-text",
                ]
            )

            job_description_path = output_dir / "job_description.txt"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(job_description_path), result.stdout)
            self.assertTrue(job_description_path.exists())
            self.assertIn("SQL", job_description_path.read_text(encoding="utf-8"))

    def test_main_can_export_html_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--export",
                    "html",
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(output_dir / "resume.html"), result.stdout)
            self.assertTrue((output_dir / "resume.html").exists())
            self.assertTrue((output_dir / "cover_letter.html").exists())
            self.assertTrue((output_dir / "linkedin_message.html").exists())

    def test_main_can_export_all_document_formats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--export",
                    "all",
                ]
            )

            expected_files = [
                "resume.html",
                "cover_letter.html",
                "linkedin_message.html",
                "resume.docx",
                "cover_letter.docx",
                "resume.pdf",
                "cover_letter.pdf",
            ]

            self.assertEqual(result.returncode, 0, result.stderr)
            for filename in expected_files:
                path = output_dir / filename
                with self.subTest(filename=filename):
                    self.assertIn(str(path), result.stdout)
                    self.assertTrue(path.exists())
            self.assertFalse((output_dir / "linkedin_message.docx").exists())
            self.assertFalse((output_dir / "linkedin_message.pdf").exists())

    def test_main_can_generate_application_review_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--review-notes",
                ]
            )

            review_notes_path = output_dir / "application_review.md"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(review_notes_path), result.stdout)
            self.assertTrue(review_notes_path.exists())
            self.assertIn(
                "Future Automation/AI Unit Notes",
                review_notes_path.read_text(encoding="utf-8"),
            )

    def test_main_can_generate_ai_brief(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--ai-brief",
                ]
            )

            ai_brief_path = output_dir / "ai_brief.md"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(ai_brief_path), result.stdout)
            self.assertTrue(ai_brief_path.exists())
            self.assertIn(
                "Do not invent employers",
                ai_brief_path.read_text(encoding="utf-8"),
            )

    def test_main_can_generate_application_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--manifest",
                ]
            )

            manifest_path = output_dir / "application_manifest.json"

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(manifest_path), result.stdout)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["detected_role"], "support")
            self.assertIn(manifest_path.as_posix(), manifest["generated_files"])

    def test_main_can_generate_full_application_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--full-package",
                ]
            )

            expected_files = [
                "resume.md",
                "cover_letter.md",
                "linkedin_message.txt",
                "job_description.txt",
                "application_review.md",
                "ai_brief.md",
                "application_manifest.json",
                "resume.html",
                "cover_letter.html",
                "linkedin_message.html",
                "resume.docx",
                "cover_letter.docx",
                "resume.pdf",
                "cover_letter.pdf",
            ]

            self.assertEqual(result.returncode, 0, result.stderr)
            for filename in expected_files:
                path = output_dir / filename
                with self.subTest(filename=filename):
                    self.assertIn(str(path), result.stdout)
                    self.assertTrue(path.exists())

    def test_automation_unit_can_check_generated_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--full-package",
                ]
            )
            check_result = run_command(
                [
                    "automation_unit.py",
                    "check",
                    str(output_dir / "application_manifest.json"),
                ]
            )

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(check_result.returncode, 0, check_result.stderr)
            self.assertIn("Automation Unit check complete.", check_result.stdout)
            self.assertIn("Detected role: support", check_result.stdout)
            self.assertIn("Missing generated files: none", check_result.stdout)
            self.assertIn("Do not submit applications automatically", check_result.stdout)

    def test_automation_unit_can_write_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--full-package",
                ]
            )
            check_result = run_command(
                [
                    "automation_unit.py",
                    "check",
                    str(output_dir / "application_manifest.json"),
                    "--write-report",
                ]
            )
            report_path = output_dir / "automation_report.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(check_result.returncode, 0, check_result.stderr)
            self.assertIn(str(report_path), check_result.stdout)
            self.assertTrue(report_path.exists())
            self.assertIn(
                "Automation Unit check complete.",
                report_path.read_text(encoding="utf-8"),
            )

    def test_automation_unit_can_review_generated_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--full-package",
                ]
            )
            review_result = run_command(
                [
                    "automation_unit.py",
                    "review",
                    str(output_dir / "application_manifest.json"),
                ]
            )

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(review_result.returncode, 0, review_result.stderr)
            self.assertIn("Recruiter Review Agent Report", review_result.stdout)
            self.assertIn("Score:", review_result.stdout)
            self.assertIn("Status:", review_result.stdout)

    def test_automation_unit_can_write_recruiter_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "main.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--full-package",
                ]
            )
            review_result = run_command(
                [
                    "automation_unit.py",
                    "review",
                    str(output_dir / "application_manifest.json"),
                    "--write-report",
                ]
            )
            review_path = output_dir / "recruiter_review.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(review_result.returncode, 0, review_result.stderr)
            self.assertIn(str(review_path), review_result.stdout)
            self.assertTrue(review_path.exists())
            self.assertIn(
                "Recruiter Review Agent Report",
                review_path.read_text(encoding="utf-8"),
            )

    def test_readiness_checker_cli_writes_ready_to_apply_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )
            readiness_result = run_command(
                [
                    "readiness_checker.py",
                    str(output_dir / "application_manifest.json"),
                    "--write-report",
                ]
            )
            report_path = output_dir / "ready_to_apply_report.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(readiness_result.returncode, 0, readiness_result.stderr)
            self.assertIn("Ready To Apply Report", readiness_result.stdout)
            self.assertTrue(report_path.exists())
            self.assertIn("Ready To Apply Report", report_path.read_text(encoding="utf-8"))

    def test_application_packet_cli_writes_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )
            packet_result = run_command(
                [
                    "application_packet.py",
                    str(output_dir / "application_manifest.json"),
                    "--write",
                ]
            )
            packet_path = output_dir / "application_packet.json"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(packet_result.returncode, 0, packet_result.stderr)
            self.assertIn("prepared_not_submitted", packet_result.stdout)
            self.assertTrue(packet_path.exists())
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertFalse(packet["automation_allowed"])

    def test_submission_planner_cli_writes_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )
            plan_result = run_command(
                [
                    "submission_planner.py",
                    str(output_dir),
                    "--write",
                ]
            )
            plan_path = output_dir / "submission_plan.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(plan_result.returncode, 0, plan_result.stderr)
            self.assertIn("Submission Plan", plan_result.stdout)
            self.assertIn("does not submit applications", plan_result.stdout)
            self.assertTrue(plan_path.exists())
            self.assertIn(
                "Submit only after explicit user approval",
                plan_path.read_text(encoding="utf-8"),
            )

    def test_apply_assistant_cli_writes_apply_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )
            apply_result = run_command(
                [
                    "apply_assistant.py",
                    str(output_dir),
                    "--write",
                ]
            )
            apply_session_path = output_dir / "apply_session.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(apply_result.returncode, 0, apply_result.stderr)
            self.assertIn("Apply Session", apply_result.stdout)
            self.assertIn("does not fill forms", apply_result.stdout)
            self.assertTrue(apply_session_path.exists())

    def test_form_fill_planner_cli_writes_json_and_markdown_plans(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )
            plan_result = run_command(
                [
                    "form_fill_planner.py",
                    str(output_dir),
                    "--write",
                ]
            )
            json_path = output_dir / "form_fill_plan.json"
            markdown_path = output_dir / "form_fill_plan.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(plan_result.returncode, 0, plan_result.stderr)
            self.assertIn("Form Fill Plan", plan_result.stdout)
            self.assertTrue(json_path.exists())
            self.assertTrue(markdown_path.exists())
            plan = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertFalse(plan["submission_allowed"])

    def test_apply_readiness_gate_cli_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_dir = temp_path / "generated"
            answers_path = temp_path / "application_answers.md"
            answers_path.write_text(
                "Work authorization:\nEligible to work in Bulgaria\n\n"
                "Visa sponsorship:\nNo sponsorship required\n\n"
                "Notice period / start date:\nAvailable after two weeks notice\n\n"
                "Salary expectation:\nOpen to market range\n",
                encoding="utf-8",
            )

            generate_result = run_command(
                [
                    "pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )
            form_plan_result = run_command(
                [
                    "form_fill_planner.py",
                    str(output_dir),
                    "--answers",
                    str(answers_path),
                    "--write",
                ]
            )
            readiness_result = run_command(
                [
                    "apply_readiness_gate.py",
                    str(output_dir),
                    "--write-report",
                ]
            )
            report_path = output_dir / "apply_readiness_report.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(form_plan_result.returncode, 0, form_plan_result.stderr)
            self.assertEqual(readiness_result.returncode, 0, readiness_result.stderr)
            self.assertIn("Apply Readiness Report", readiness_result.stdout)
            self.assertTrue(report_path.exists())

    def test_apply_prep_pipeline_cli_runs_safe_apply_prep_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_dir = temp_path / "apply-prep-output"
            answers_path = temp_path / "application_answers.md"
            answers_path.write_text(
                "Work authorization:\nEligible to work in Bulgaria\n\n"
                "Visa sponsorship:\nNo sponsorship required\n\n"
                "Notice period / start date:\nAvailable after two weeks notice\n\n"
                "Salary expectation:\nOpen to market range\n",
                encoding="utf-8",
            )

            result = run_command(
                [
                    "apply_prep_pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                    "--answers",
                    str(answers_path),
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Application package pipeline: OK", result.stdout)
            self.assertIn("Form-fill plan: OK", result.stdout)
            self.assertIn("Apply readiness gate: OK", result.stdout)
            self.assertIn("Controlled apply session: OK", result.stdout)
            self.assertTrue((output_dir / "apply_prep_report.md").exists())
            self.assertTrue((output_dir / "apply_readiness_report.md").exists())
            self.assertTrue((output_dir / "apply_session.md").exists())

    def test_batch_apply_prep_pipeline_cli_runs_multiple_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jobs_dir = temp_path / "jobs"
            output_root = temp_path / "batch-apply-prep"
            answers_path = temp_path / "application_answers.md"
            jobs_dir.mkdir()
            (jobs_dir / "support-job.txt").write_text(
                "Technical Support Engineer, SQL, troubleshooting, customer support",
                encoding="utf-8",
            )
            (jobs_dir / "developer-job.txt").write_text(
                "Junior Python Developer, APIs, backend, Git, web applications",
                encoding="utf-8",
            )
            answers_path.write_text(
                "Work authorization:\nEligible to work in Bulgaria\n\n"
                "Visa sponsorship:\nNo sponsorship required\n\n"
                "Notice period / start date:\nAvailable after two weeks notice\n\n"
                "Salary expectation:\nOpen to market range\n",
                encoding="utf-8",
            )

            result = run_command(
                [
                    "batch_apply_prep_pipeline.py",
                    "--jobs-dir",
                    str(jobs_dir),
                    "--output-root",
                    str(output_root),
                    "--answers",
                    str(answers_path),
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("support-job.txt: OK", result.stdout)
            self.assertIn("developer-job.txt: OK", result.stdout)
            self.assertTrue((output_root / "support-job" / "apply_prep_report.md").exists())
            self.assertTrue((output_root / "developer-job" / "apply_prep_report.md").exists())
            self.assertTrue((output_root / "batch_apply_prep_report.md").exists())

    def test_status_dashboard_cli_writes_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "generated"

            generate_result = run_command(
                [
                    "pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )
            dashboard_result = run_command(
                [
                    "status_dashboard.py",
                    str(output_dir),
                    "--write",
                ]
            )
            dashboard_file = output_dir / "status_dashboard.md"

            self.assertEqual(generate_result.returncode, 0, generate_result.stderr)
            self.assertEqual(dashboard_result.returncode, 0, dashboard_result.stderr)
            self.assertIn("JobHunterAI Status Dashboard", dashboard_result.stdout)
            self.assertTrue(dashboard_file.exists())

    def test_tracker_cli_add_list_and_stats(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "jobs.db"
            env = os.environ.copy()
            env["JOBHUNTERAI_DB_PATH"] = str(db_path)

            add_result = run_command(
                [
                    "tracker.py",
                    "add",
                    "--company",
                    "Example Ltd",
                    "--position",
                    "Support Engineer",
                    "--role",
                    "support",
                    "--status",
                    "applied",
                ],
                env=env,
            )
            list_result = run_command(
                ["tracker.py", "list", "--status", "applied", "--role", "support"],
                env=env,
            )
            stats_result = run_command(["tracker.py", "stats"], env=env)

            self.assertEqual(add_result.returncode, 0, add_result.stderr)
            self.assertEqual(list_result.returncode, 0, list_result.stderr)
            self.assertEqual(stats_result.returncode, 0, stats_result.stderr)
            self.assertIn("Added job #1.", add_result.stdout)
            self.assertIn("Example Ltd - Support Engineer [applied]", list_result.stdout)
            self.assertIn("Total jobs: 1", stats_result.stdout)
            self.assertIn("- applied: 1", stats_result.stdout)

    def test_profile_validator_cli_writes_report(self) -> None:
        result = run_command(["profile_validator.py", "--write-report"])
        report_path = BASE_DIR / "outputs" / "profile_validation_report.md"

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Profile Validation Report", result.stdout)
        self.assertIn(str(report_path), result.stdout)
        self.assertTrue(report_path.exists())
        self.assertIn(
            "Profile Validation Report",
            report_path.read_text(encoding="utf-8"),
        )

    def test_profile_validator_cli_writes_improvement_guide(self) -> None:
        result = run_command(["profile_validator.py", "--write-guide"])
        guide_path = BASE_DIR / "outputs" / "profile_improvement_guide.md"

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(guide_path), result.stdout)
        self.assertTrue(guide_path.exists())
        self.assertIn(
            "Profile Improvement Guide",
            guide_path.read_text(encoding="utf-8"),
        )

    def test_pipeline_cli_runs_offline_package_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "pipeline-output"

            result = run_command(
                [
                    "pipeline.py",
                    "--job",
                    "examples/sample_job.txt",
                    "--output-dir",
                    str(output_dir),
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Profile validation: OK", result.stdout)
            self.assertIn("Application package generation: OK", result.stdout)
            self.assertIn("Automation Unit check: OK", result.stdout)
            self.assertIn("Recruiter review: OK", result.stdout)
            self.assertIn("Readiness check: OK", result.stdout)
            self.assertIn("Application packet: OK", result.stdout)
            self.assertIn("Submission plan: OK", result.stdout)
            self.assertTrue((output_dir / "application_manifest.json").exists())
            self.assertTrue((output_dir / "automation_report.md").exists())
            self.assertTrue((output_dir / "recruiter_review.md").exists())
            self.assertTrue((output_dir / "ready_to_apply_report.md").exists())
            self.assertTrue((output_dir / "application_packet.json").exists())
            self.assertTrue((output_dir / "submission_plan.md").exists())
            self.assertTrue((output_dir / "pipeline_report.md").exists())

    def test_batch_pipeline_cli_runs_multiple_offline_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jobs_dir = temp_path / "jobs"
            output_root = temp_path / "batch-output"
            jobs_dir.mkdir()
            (jobs_dir / "support-job.txt").write_text(
                "Technical Support Engineer, SQL, troubleshooting, customer support",
                encoding="utf-8",
            )
            (jobs_dir / "developer-job.txt").write_text(
                "Junior Python Developer, APIs, backend, Git, web applications",
                encoding="utf-8",
            )

            result = run_command(
                [
                    "batch_pipeline.py",
                    "--jobs-dir",
                    str(jobs_dir),
                    "--output-root",
                    str(output_root),
                ]
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("support-job.txt: OK", result.stdout)
            self.assertIn("developer-job.txt: OK", result.stdout)
            self.assertTrue((output_root / "support-job" / "pipeline_report.md").exists())
            self.assertTrue((output_root / "developer-job" / "pipeline_report.md").exists())
            self.assertTrue((output_root / "batch_report.md").exists())

    def test_job_intake_cli_saves_and_lists_job(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            jobs_dir = Path(temp_dir) / "jobs"

            add_result = run_command(
                [
                    "job_intake.py",
                    "add",
                    "--jobs-dir",
                    str(jobs_dir),
                    "--company",
                    "Example Ltd",
                    "--position",
                    "Support Engineer",
                    "--url",
                    "https://example.com/job",
                    "--text",
                    "Technical Support Engineer, SQL, troubleshooting",
                ]
            )
            list_result = run_command(
                [
                    "job_intake.py",
                    "list",
                    "--jobs-dir",
                    str(jobs_dir),
                ]
            )

            self.assertEqual(add_result.returncode, 0, add_result.stderr)
            self.assertEqual(list_result.returncode, 0, list_result.stderr)
            self.assertIn("Saved job description.", add_result.stdout)
            self.assertTrue((jobs_dir / "example-ltd-support-engineer.txt").exists())
            self.assertTrue((jobs_dir / "job_index.json").exists())
            self.assertIn("Example Ltd - Support Engineer", list_result.stdout)

    def test_intake_saved_job_can_feed_batch_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jobs_dir = temp_path / "jobs"
            output_root = temp_path / "batch-output"

            add_result = run_command(
                [
                    "job_intake.py",
                    "add",
                    "--jobs-dir",
                    str(jobs_dir),
                    "--company",
                    "Example Ltd",
                    "--position",
                    "Support Engineer",
                    "--text",
                    "Technical Support Engineer, SQL, troubleshooting, customer support",
                ]
            )
            batch_result = run_command(
                [
                    "batch_pipeline.py",
                    "--jobs-dir",
                    str(jobs_dir),
                    "--output-root",
                    str(output_root),
                ]
            )

            self.assertEqual(add_result.returncode, 0, add_result.stderr)
            self.assertEqual(batch_result.returncode, 0, batch_result.stderr)
            self.assertIn("example-ltd-support-engineer.txt: OK", batch_result.stdout)
            self.assertTrue(
                (output_root / "example-ltd-support-engineer" / "pipeline_report.md").exists()
            )


if __name__ == "__main__":
    unittest.main()

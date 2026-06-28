import tempfile
import unittest
from pathlib import Path

from profile_validator import (
    build_profile_improvement_guide,
    build_profile_validation_report,
    improvement_guide_path,
    report_path,
    validate_profiles,
)


VALID_MASTER_PROFILE = """Name: Test Candidate

Location:
Test City

Email:
test@example.com

Phone:
123

GitHub:
https://github.com/test

Languages:
English - Fluent

Experience:
2024 - Technical Support

Projects:
JobHunterAI
"""

VALID_ROLE_PROFILE = """# Support Profile

## Professional Summary

Support candidate.

## Technical Skills

- SQL

## Experience

### Technical Support - 2024

- Helped customers.

## Projects

- JobHunterAI
"""

VALID_TEMPLATE = """# Test

{contact_block}
{target_role}
{professional_summary}
{core_skills}
{relevant_experience}
{selected_projects}
"""


class ProfileValidatorTests(unittest.TestCase):
    def test_validate_profiles_accepts_complete_source_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            master_path = temp_path / "master_profile.md"
            role_path = temp_path / "support_cv.md"
            template_path = temp_path / "resume_template.md"
            master_path.write_text(VALID_MASTER_PROFILE, encoding="utf-8")
            role_path.write_text(VALID_ROLE_PROFILE, encoding="utf-8")
            template_path.write_text(VALID_TEMPLATE, encoding="utf-8")

            validation = validate_profiles(master_path, [role_path], template_path)

            self.assertTrue(validation.is_ready)
            self.assertEqual(validation.errors, [])
            self.assertEqual(validation.warnings, [])

    def test_validate_profiles_warns_about_placeholders_and_missing_dates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            master_path = temp_path / "master_profile.md"
            role_path = temp_path / "support_cv.md"
            template_path = temp_path / "resume_template.md"
            master_path.write_text(
                VALID_MASTER_PROFILE.replace("2024", "Later"),
                encoding="utf-8",
            )
            role_path.write_text(
                VALID_ROLE_PROFILE.replace("2024", "TBD"),
                encoding="utf-8",
            )
            template_path.write_text(VALID_TEMPLATE, encoding="utf-8")

            validation = validate_profiles(master_path, [role_path], template_path)

            self.assertTrue(validation.is_ready)
            self.assertEqual(validation.errors, [])
            self.assertGreaterEqual(len(validation.warnings), 2)

    def test_validate_profiles_errors_when_required_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            master_path = temp_path / "missing_master.md"
            role_path = temp_path / "support_cv.md"
            template_path = temp_path / "resume_template.md"
            role_path.write_text(VALID_ROLE_PROFILE, encoding="utf-8")
            template_path.write_text(VALID_TEMPLATE, encoding="utf-8")

            validation = validate_profiles(master_path, [role_path], template_path)

            self.assertFalse(validation.is_ready)
            self.assertIn("Required source file is missing", validation.errors[0].message)

    def test_validate_profiles_errors_when_template_placeholder_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            master_path = temp_path / "master_profile.md"
            role_path = temp_path / "support_cv.md"
            template_path = temp_path / "resume_template.md"
            master_path.write_text(VALID_MASTER_PROFILE, encoding="utf-8")
            role_path.write_text(VALID_ROLE_PROFILE, encoding="utf-8")
            template_path.write_text(
                VALID_TEMPLATE.replace("{selected_projects}", ""),
                encoding="utf-8",
            )

            validation = validate_profiles(master_path, [role_path], template_path)

            self.assertFalse(validation.is_ready)
            self.assertIn("Missing template placeholders", validation.errors[0].message)

    def test_build_profile_validation_report_includes_status_and_issues(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            validation = validate_profiles(
                temp_path / "missing.md",
                [],
                temp_path / "missing_template.md",
            )

            report = build_profile_validation_report(validation)

            self.assertIn("Profile Validation Report", report)
            self.assertIn("Status: Blocked", report)
            self.assertIn("Required source file is missing", report)

    def test_build_profile_improvement_guide_includes_safe_profile_advice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            master_path = temp_path / "master_profile.md"
            role_path = temp_path / "support_cv.md"
            template_path = temp_path / "resume_template.md"
            master_path.write_text(
                VALID_MASTER_PROFILE.replace("2024", "Later"),
                encoding="utf-8",
            )
            role_path.write_text(VALID_ROLE_PROFILE, encoding="utf-8")
            template_path.write_text(VALID_TEMPLATE, encoding="utf-8")
            validation = validate_profiles(master_path, [role_path], template_path)

            guide = build_profile_improvement_guide(validation)

            self.assertIn("Profile Improvement Guide", guide)
            self.assertIn("Do not add anything unless it is truthful", guide)
            self.assertIn("Community project", guide)
            self.assertIn("Current Validation Warnings", guide)

    def test_report_path_uses_outputs_folder(self) -> None:
        self.assertEqual(report_path().name, "profile_validation_report.md")

    def test_improvement_guide_path_uses_outputs_folder(self) -> None:
        self.assertEqual(improvement_guide_path().name, "profile_improvement_guide.md")


if __name__ == "__main__":
    unittest.main()

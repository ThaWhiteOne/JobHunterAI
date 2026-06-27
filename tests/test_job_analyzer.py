import unittest

from job_analyzer import (
    analyze_job,
    extract_requirement_lines,
    generate_application_review,
)


class JobAnalyzerTests(unittest.TestCase):
    def test_extract_requirement_lines_keeps_relevant_short_lines(self) -> None:
        job_description = """Junior SOC Analyst

Requirements:
- SIEM monitoring
- Incident response
- Vulnerability analysis
- This line is unrelated
"""

        requirements = extract_requirement_lines(job_description)

        self.assertIn("SIEM monitoring", requirements)
        self.assertIn("Incident response", requirements)
        self.assertIn("Vulnerability analysis", requirements)
        self.assertNotIn("This line is unrelated", requirements)

    def test_analyze_job_returns_matched_keywords_and_requirements(self) -> None:
        analysis = analyze_job(
            "Junior Python Developer\n- Python\n- APIs\n- backend\n- Git",
            "developer",
        )

        self.assertEqual(analysis.role, "developer")
        self.assertIn("python", analysis.matched_keywords)
        self.assertIn("git", analysis.matched_keywords)
        self.assertIn("Python", analysis.requirement_lines)

    def test_generate_application_review_includes_ai_unit_notes(self) -> None:
        review = generate_application_review(
            "support",
            "Technical Support / Application Support",
            "Technical Support Engineer\n- SQL\n- troubleshooting",
            {"support": 3, "developer": 1, "cybersecurity": 0},
        )

        self.assertIn("# Application Review Notes", review)
        self.assertIn("support: 3", review)
        self.assertIn("sql", review)
        self.assertIn("Future Automation/AI Unit Notes", review)


if __name__ == "__main__":
    unittest.main()

import unittest

from config import ROLE_DISPLAY_NAMES
from generators import (
    generate_cover_letter,
    generate_linkedin_message,
    generate_resume,
)


class GeneratorTests(unittest.TestCase):
    def test_each_role_generates_application_documents(self) -> None:
        job_description = "Python SQL troubleshooting security support"
        profile = "Sample profile content"

        for role, role_display_name in ROLE_DISPLAY_NAMES.items():
            with self.subTest(role=role):
                resume = generate_resume(
                    role,
                    role_display_name,
                    profile,
                    job_description,
                )
                cover_letter = generate_cover_letter(
                    role,
                    role_display_name,
                    profile,
                    job_description,
                )
                linkedin_message = generate_linkedin_message(role, role_display_name)

                self.assertIn(role_display_name, resume)
                self.assertIn(role_display_name, cover_letter)
                self.assertIn(role_display_name, linkedin_message)
                self.assertGreater(len(resume.strip()), 200)
                self.assertGreater(len(cover_letter.strip()), 100)
                self.assertGreater(len(linkedin_message.strip()), 80)

    def test_resume_does_not_include_debug_sections(self) -> None:
        resume = generate_resume(
            "support",
            ROLE_DISPLAY_NAMES["support"],
            "Sample profile content",
            "Technical Support Engineer SQL troubleshooting customer support",
        )

        self.assertNotIn("Matched Job Keywords", resume)
        self.assertNotIn("Role scores", resume)


if __name__ == "__main__":
    unittest.main()

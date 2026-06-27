import unittest

from ai_prompt_builder import generate_ai_brief


class AiPromptBuilderTests(unittest.TestCase):
    def test_generate_ai_brief_includes_guardrails_and_sources(self) -> None:
        brief = generate_ai_brief(
            role="developer",
            role_display_name="Junior Python / Web Developer",
            profile="Profile source truth",
            job_description="Junior Python Developer\n- APIs\n- Git",
            scores={"support": 0, "developer": 4, "cybersecurity": 0},
            resume="# Resume Draft",
            cover_letter="Dear Hiring Manager,",
            linkedin_message="Hello,",
        )

        self.assertIn("# AI Brief For Future Tailoring", brief)
        self.assertIn("does not call any AI API", brief)
        self.assertIn("Do not invent employers", brief)
        self.assertIn("Profile source truth", brief)
        self.assertIn("Junior Python Developer", brief)
        self.assertIn("# Resume Draft", brief)
        self.assertIn("unsupported job requirements", brief)


if __name__ == "__main__":
    unittest.main()

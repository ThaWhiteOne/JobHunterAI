import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_draft_generator import (
    build_ai_draft_prompt,
    parse_ai_drafts,
    run_ai_draft_generation,
)
from ai_reviewer import AIReviewNotConfiguredError


class AIDraftGeneratorTests(unittest.TestCase):
    def test_build_ai_draft_prompt_includes_profile_template_and_job(self) -> None:
        prompt = build_ai_draft_prompt(
            "Junior Python / Web Developer",
            "Profile source of truth",
            "Job asks for Python and APIs",
            "Resume template guidance",
        )

        self.assertIn("Junior Python / Web Developer", prompt)
        self.assertIn("Profile source of truth", prompt)
        self.assertIn("Job asks for Python and APIs", prompt)
        self.assertIn("Resume template guidance", prompt)
        self.assertIn("Do not include unsupported dates", prompt)
        self.assertIn("Do not imply paid or professional work", prompt)
        self.assertIn("Use plain ASCII punctuation", prompt)

    def test_parse_ai_drafts_reads_required_json_keys(self) -> None:
        drafts = parse_ai_drafts(
            json.dumps(
                {
                    "resume_md": "# Resume",
                    "cover_letter_md": "Dear Hiring Manager",
                    "linkedin_message_txt": "Hello",
                }
            )
        )

        self.assertEqual(drafts["resume_md"], "# Resume")
        self.assertEqual(drafts["cover_letter_md"], "Dear Hiring Manager")
        self.assertEqual(drafts["linkedin_message_txt"], "Hello")

    def test_parse_ai_drafts_accepts_json_code_fence(self) -> None:
        drafts = parse_ai_drafts(
            """```json
{"resume_md": "# Resume", "cover_letter_md": "Letter", "linkedin_message_txt": "Message"}
```"""
        )

        self.assertEqual(drafts["resume_md"], "# Resume")

    def test_parse_ai_drafts_rejects_missing_keys(self) -> None:
        with self.assertRaises(ValueError):
            parse_ai_drafts('{"resume_md": "# Resume"}')

    def test_run_ai_draft_generation_requires_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            with patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(AIReviewNotConfiguredError):
                    run_ai_draft_generation(
                        "Support",
                        "Profile",
                        "Job",
                        "Template",
                        env_path,
                    )

    @patch("ai_draft_generator.request_openai_text")
    def test_run_ai_draft_generation_returns_parsed_ai_output(self, request_mock) -> None:
        request_mock.return_value = json.dumps(
            {
                "resume_md": "# Resume",
                "cover_letter_md": "Letter",
                "linkedin_message_txt": "Message",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")

            with patch.dict("os.environ", {}, clear=True):
                drafts = run_ai_draft_generation(
                    "Support",
                    "Profile",
                    "Job",
                    "Template",
                    env_path,
                )

        self.assertEqual(drafts["cover_letter_md"], "Letter")
        request_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()

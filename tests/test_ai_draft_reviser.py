import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_draft_reviser import (
    build_ai_revision_prompt,
    parse_ai_revision,
    run_ai_draft_revision,
)
from ai_reviewer import AIReviewNotConfiguredError


class AIDraftReviserTests(unittest.TestCase):
    def test_build_ai_revision_prompt_includes_drafts_and_rules(self) -> None:
        prompt = build_ai_revision_prompt(
            "Technical Support / Application Support",
            "Profile source of truth",
            "Job asks for SQL troubleshooting",
            "Resume draft",
            "Cover letter draft",
            "LinkedIn message draft",
        )

        self.assertIn("Technical Support / Application Support", prompt)
        self.assertIn("Profile source of truth", prompt)
        self.assertIn("Job asks for SQL troubleshooting", prompt)
        self.assertIn("Resume draft", prompt)
        self.assertIn("Remove or soften unsupported claims", prompt)
        self.assertIn("Use plain ASCII punctuation", prompt)

    def test_parse_ai_revision_reads_required_json_keys(self) -> None:
        revision = parse_ai_revision(
            json.dumps(
                {
                    "resume_md": "# Resume",
                    "cover_letter_md": "Letter",
                    "linkedin_message_txt": "Message",
                    "revision_notes_md": "# Notes",
                }
            )
        )

        self.assertEqual(revision["resume_md"], "# Resume")
        self.assertEqual(revision["revision_notes_md"], "# Notes")

    def test_parse_ai_revision_accepts_json_code_fence(self) -> None:
        revision = parse_ai_revision(
            """```json
{"resume_md": "# Resume", "cover_letter_md": "Letter", "linkedin_message_txt": "Message", "revision_notes_md": "# Notes"}
```"""
        )

        self.assertEqual(revision["cover_letter_md"], "Letter")

    def test_parse_ai_revision_rejects_missing_notes(self) -> None:
        with self.assertRaises(ValueError):
            parse_ai_revision(
                json.dumps(
                    {
                        "resume_md": "# Resume",
                        "cover_letter_md": "Letter",
                        "linkedin_message_txt": "Message",
                    }
                )
            )

    def test_run_ai_draft_revision_requires_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            with patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(AIReviewNotConfiguredError):
                    run_ai_draft_revision(
                        "Support",
                        "Profile",
                        "Job",
                        "Resume",
                        "Letter",
                        "Message",
                        env_path,
                    )

    @patch("ai_draft_reviser.request_openai_text")
    def test_run_ai_draft_revision_returns_parsed_output(self, request_mock) -> None:
        request_mock.return_value = json.dumps(
            {
                "resume_md": "# Final Resume",
                "cover_letter_md": "Final letter",
                "linkedin_message_txt": "Final message",
                "revision_notes_md": "Improved tailoring.",
            }
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")

            with patch.dict("os.environ", {}, clear=True):
                revision = run_ai_draft_revision(
                    "Support",
                    "Profile",
                    "Job",
                    "Resume",
                    "Letter",
                    "Message",
                    env_path,
                )

        self.assertEqual(revision["resume_md"], "# Final Resume")
        self.assertEqual(revision["revision_notes_md"], "Improved tailoring.")
        request_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()

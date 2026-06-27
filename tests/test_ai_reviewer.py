import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_reviewer import (
    AIReviewNotConfiguredError,
    build_ai_review_prompt,
    extract_response_text,
    load_env_file,
    request_openai_review,
    run_ai_review,
)


class FakeResponse:
    def __init__(self, data: dict[str, object]) -> None:
        self.data = json.dumps(data).encode("utf-8")

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self.data


class AIReviewerTests(unittest.TestCase):
    def test_load_env_file_reads_simple_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "# local secrets",
                        "OPENAI_API_KEY='test-key'",
                        'OPENAI_MODEL="test-model"',
                    ]
                ),
                encoding="utf-8",
            )

            values = load_env_file(env_path)

            self.assertEqual(values["OPENAI_API_KEY"], "test-key")
            self.assertEqual(values["OPENAI_MODEL"], "test-model")

    def test_run_ai_review_requires_api_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            with self.assertRaises(AIReviewNotConfiguredError):
                run_ai_review({}, Path(temp_dir) / "application_manifest.json", "", env_path)

    def test_build_ai_review_prompt_includes_drafts_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manifest_path = temp_path / "application_manifest.json"
            resume_path = temp_path / "resume.md"
            cover_letter_path = temp_path / "cover_letter.md"
            linkedin_path = temp_path / "linkedin_message.txt"
            job_path = temp_path / "job.txt"
            resume_path.write_text("Python support resume", encoding="utf-8")
            cover_letter_path.write_text("Support cover letter", encoding="utf-8")
            linkedin_path.write_text("Short recruiter message", encoding="utf-8")
            job_path.write_text("Technical Support Engineer with SQL", encoding="utf-8")
            manifest = {
                "role_display_name": "Technical Support / Application Support",
                "job_path": job_path.as_posix(),
                "generated_files": [
                    resume_path.as_posix(),
                    cover_letter_path.as_posix(),
                    linkedin_path.as_posix(),
                ],
                "matched_keywords": ["SQL", "support"],
                "automation_guardrails": ["Do not invent experience."],
            }

            prompt = build_ai_review_prompt(manifest, manifest_path, "Offline report")

            self.assertIn("Technical Support / Application Support", prompt)
            self.assertIn("Python support resume", prompt)
            self.assertIn("Technical Support Engineer with SQL", prompt)
            self.assertIn("Do not invent experience.", prompt)
            self.assertIn("Offline report", prompt)

    def test_extract_response_text_supports_output_text(self) -> None:
        text = extract_response_text({"output_text": "Looks ready."})

        self.assertEqual(text, "Looks ready.")

    def test_extract_response_text_supports_output_items(self) -> None:
        text = extract_response_text(
            {
                "output": [
                    {
                        "content": [
                            {
                                "type": "output_text",
                                "text": "Check unsupported claims.",
                            }
                        ]
                    }
                ]
            }
        )

        self.assertEqual(text, "Check unsupported claims.")

    @patch("urllib.request.urlopen")
    def test_request_openai_review_sends_expected_payload(self, urlopen_mock) -> None:
        urlopen_mock.return_value = FakeResponse({"output_text": "AI feedback"})

        result = request_openai_review(
            "Review this application.",
            "test-key",
            "test-model",
            timeout_seconds=5,
        )

        request = urlopen_mock.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(result, "AI feedback")
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["input"], "Review this application.")
        self.assertFalse(payload["store"])
        self.assertIn("Bearer test-key", request.headers["Authorization"])


if __name__ == "__main__":
    unittest.main()

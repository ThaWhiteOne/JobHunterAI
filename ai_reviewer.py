import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from draft_reviewer import read_generated_file, resolve_path


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_OPENAI_MODEL = "gpt-4.1"
DEFAULT_ENV_PATH = Path(__file__).resolve().parent / ".env"

AI_REVIEW_INSTRUCTIONS = (
    "You are a careful recruiter-style reviewer for JobHunterAI drafts. "
    "Review the resume, cover letter, and LinkedIn message before the user applies. "
    "Do not rewrite the entire application. Do not invent experience, employers, "
    "certifications, education, dates, or skills. Flag anything that needs manual "
    "verification. Keep the feedback practical, professional, and ATS-aware."
)


class AIReviewNotConfiguredError(ValueError):
    """Raised when AI review is requested without an API key."""


def load_env_file(path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    if not path.is_file():
        raise ValueError(f"Expected .env file but found something else: {path}")

    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned.startswith("#") or "=" not in cleaned:
            continue
        if cleaned.startswith("export "):
            cleaned = cleaned.removeprefix("export ").strip()
        key, value = cleaned.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value

    return values


def get_setting(name: str, env_path: Path = DEFAULT_ENV_PATH) -> str:
    environment_value = os.getenv(name, "").strip()
    if environment_value:
        return environment_value

    return load_env_file(env_path).get(name, "").strip()


def get_openai_api_key(env_path: Path = DEFAULT_ENV_PATH) -> str:
    return get_setting("OPENAI_API_KEY", env_path)


def get_openai_model(env_path: Path = DEFAULT_ENV_PATH) -> str:
    return get_setting("OPENAI_MODEL", env_path) or DEFAULT_OPENAI_MODEL


def read_job_description(manifest: dict[str, Any], manifest_path: Path) -> str:
    job_path_text = manifest.get("job_path")
    if not job_path_text:
        return ""

    job_path = resolve_path(str(job_path_text), manifest_path)
    if not job_path.exists() or not job_path.is_file():
        return ""

    return job_path.read_text(encoding="utf-8").strip()


def build_ai_review_prompt(
    manifest: dict[str, Any],
    manifest_path: Path,
    offline_report: str,
) -> str:
    resume = read_generated_file(manifest, manifest_path, "resume.md")
    cover_letter = read_generated_file(manifest, manifest_path, "cover_letter.md")
    linkedin_message = read_generated_file(manifest, manifest_path, "linkedin_message.txt")
    job_description = read_job_description(manifest, manifest_path)
    guardrails = manifest.get("automation_guardrails", [])

    return "\n".join(
        [
            "# JobHunterAI AI Recruiter Review Request",
            "",
            "Review the drafts as if you are a recruiter screening this application.",
            "Return concise Markdown with these sections:",
            "- Overall readiness",
            "- Strong points",
            "- Risks or weak spots",
            "- Unsupported or unverifiable claims",
            "- Suggested edits before applying",
            "",
            "Do not submit anything. This is only a review step.",
            "",
            "## Role",
            "",
            str(manifest.get("role_display_name", "unknown")),
            "",
            "## Matched Keywords",
            "",
            ", ".join(str(keyword) for keyword in manifest.get("matched_keywords", []))
            or "None listed.",
            "",
            "## Guardrails",
            "",
            "\n".join(f"- {guardrail}" for guardrail in guardrails) or "- None listed.",
            "",
            "## Job Description",
            "",
            job_description or "Job description was not available from the manifest.",
            "",
            "## Resume Draft",
            "",
            resume or "resume.md was not available.",
            "",
            "## Cover Letter Draft",
            "",
            cover_letter or "cover_letter.md was not available.",
            "",
            "## LinkedIn Message Draft",
            "",
            linkedin_message or "linkedin_message.txt was not available.",
            "",
            "## Offline Rule-Based Review",
            "",
            offline_report,
        ]
    )


def extract_response_text(response_data: dict[str, Any]) -> str:
    output_text = response_data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    parts = []
    for item in response_data.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())

    if parts:
        return "\n\n".join(parts)

    raise ValueError("OpenAI response did not include text output.")


def request_openai_text(
    prompt: str,
    api_key: str,
    model: str,
    instructions: str,
    timeout_seconds: int = 60,
) -> str:
    payload = {
        "model": model,
        "instructions": instructions,
        "input": prompt,
        "store": False,
    }
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenAI API request failed with HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise ValueError(f"OpenAI API request failed: {error.reason}") from error
    except json.JSONDecodeError as error:
        raise ValueError("OpenAI API returned invalid JSON.") from error

    if not isinstance(response_data, dict):
        raise ValueError("OpenAI API returned an unexpected response.")

    return extract_response_text(response_data)


def request_openai_review(
    prompt: str,
    api_key: str,
    model: str,
    timeout_seconds: int = 60,
) -> str:
    return request_openai_text(
        prompt,
        api_key,
        model,
        AI_REVIEW_INSTRUCTIONS,
        timeout_seconds,
    )


def build_ai_review_report(review_text: str, model: str) -> str:
    return "\n".join(
        [
            "# AI Recruiter Review",
            "",
            f"Model: {model}",
            "",
            "This optional AI review does not submit applications. Review all suggestions manually.",
            "",
            review_text.strip(),
        ]
    )


def ai_recruiter_review_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "ai_recruiter_review.md"


def run_ai_review(
    manifest: dict[str, Any],
    manifest_path: Path,
    offline_report: str,
    env_path: Path = DEFAULT_ENV_PATH,
) -> str:
    api_key = get_openai_api_key(env_path)
    if not api_key:
        raise AIReviewNotConfiguredError(
            "OPENAI_API_KEY was not found in the environment or local .env file."
        )

    model = get_openai_model(env_path)
    prompt = build_ai_review_prompt(manifest, manifest_path, offline_report)
    review_text = request_openai_review(prompt, api_key, model)
    return build_ai_review_report(review_text, model)

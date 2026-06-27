import json
from pathlib import Path
from typing import Any

from ai_reviewer import (
    DEFAULT_ENV_PATH,
    AIReviewNotConfiguredError,
    get_openai_api_key,
    get_openai_model,
    request_openai_text,
)


AI_DRAFT_INSTRUCTIONS = (
    "You generate tailored job application drafts for JobHunterAI. "
    "Use only the candidate profile and template guidance provided by the user. "
    "Do not invent experience, dates, employers, certifications, education, metrics, "
    "or tools. If a detail is missing, omit it instead of guessing. "
    "Return only valid JSON with the requested keys."
)

REQUIRED_DRAFT_KEYS = [
    "resume_md",
    "cover_letter_md",
    "linkedin_message_txt",
]


def build_ai_draft_prompt(
    role_display_name: str,
    profile: str,
    job_description: str,
    resume_template: str,
) -> str:
    return "\n".join(
        [
            "# JobHunterAI Draft Generation Request",
            "",
            "Create application drafts for this target role.",
            "",
            "Return only JSON with these string keys:",
            "- resume_md",
            "- cover_letter_md",
            "- linkedin_message_txt",
            "",
            "Rules:",
            "- Use the candidate profile as the source of truth.",
            "- Keep the resume ATS-friendly Markdown.",
            "- Tailor naturally to the job description.",
            "- Do not include unsupported dates, metrics, employers, certifications, or education.",
            "- Keep the LinkedIn message short and recruiter-friendly.",
            "",
            "## Target Role",
            "",
            role_display_name,
            "",
            "## Candidate Profile",
            "",
            profile,
            "",
            "## Resume Template Guidance",
            "",
            resume_template,
            "",
            "## Job Description",
            "",
            job_description,
        ]
    )


def strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_ai_drafts(text: str) -> dict[str, str]:
    try:
        parsed = json.loads(strip_json_fence(text))
    except json.JSONDecodeError as error:
        raise ValueError("AI draft response was not valid JSON.") from error

    if not isinstance(parsed, dict):
        raise ValueError("AI draft response must be a JSON object.")

    drafts = {}
    for key in REQUIRED_DRAFT_KEYS:
        value = parsed.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI draft response is missing required text: {key}")
        drafts[key] = value.strip()

    return drafts


def run_ai_draft_generation(
    role_display_name: str,
    profile: str,
    job_description: str,
    resume_template: str,
    env_path: Path = DEFAULT_ENV_PATH,
) -> dict[str, str]:
    api_key = get_openai_api_key(env_path)
    if not api_key:
        raise AIReviewNotConfiguredError(
            "OPENAI_API_KEY was not found in the environment or local .env file."
        )

    model = get_openai_model(env_path)
    prompt = build_ai_draft_prompt(
        role_display_name,
        profile,
        job_description,
        resume_template,
    )
    response_text = request_openai_text(
        prompt,
        api_key,
        model,
        AI_DRAFT_INSTRUCTIONS,
    )
    return parse_ai_drafts(response_text)

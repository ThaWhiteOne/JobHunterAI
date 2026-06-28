import json
from pathlib import Path

from ai_draft_generator import REQUIRED_DRAFT_KEYS, strip_json_fence
from ai_reviewer import (
    DEFAULT_ENV_PATH,
    AIReviewNotConfiguredError,
    get_openai_api_key,
    get_openai_model,
    request_openai_text,
)


AI_REVISION_INSTRUCTIONS = (
    "You are a recruiter-minded editor for JobHunterAI. "
    "Revise application drafts so they are stronger, clearer, and better tailored. "
    "Use only the supplied candidate profile as the source of truth. "
    "Do not invent experience, dates, employers, certifications, education, metrics, "
    "tools, or achievements. If a detail is missing, omit it. "
    "Prefer concrete evidence from the profile over generic claims. "
    "Use plain ASCII punctuation. "
    "Return only valid JSON with the requested keys."
)

REVISION_NOTES_KEY = "revision_notes_md"


def build_ai_revision_prompt(
    role_display_name: str,
    profile: str,
    job_description: str,
    resume: str,
    cover_letter: str,
    linkedin_message: str,
) -> str:
    return "\n".join(
        [
            "# JobHunterAI Automated Draft Revision",
            "",
            "Review these drafts like a recruiter, then return revised final drafts.",
            "",
            "Return only JSON with these string keys:",
            "- resume_md",
            "- cover_letter_md",
            "- linkedin_message_txt",
            "- revision_notes_md",
            "",
            "Revision rules:",
            "- Improve clarity, relevance, and ATS keyword alignment.",
            "- Keep all claims supported by the candidate profile.",
            "- Remove or soften unsupported claims instead of asking the user to edit them.",
            "- Do not add dates, numbers, or achievements unless they appear in the profile.",
            "- Do not imply paid or professional work unless the profile says it was paid or professional.",
            "- Replace vague claims with specific profile-backed evidence where possible.",
            "- Remove generic phrases like passionate, dynamic, proven track record, or fast-paced environment.",
            "- Keep the LinkedIn message short.",
            "- Use plain ASCII punctuation.",
            "",
            "## Target Role",
            "",
            role_display_name,
            "",
            "## Candidate Profile",
            "",
            profile,
            "",
            "## Job Description",
            "",
            job_description,
            "",
            "## Current Resume Draft",
            "",
            resume,
            "",
            "## Current Cover Letter Draft",
            "",
            cover_letter,
            "",
            "## Current LinkedIn Message Draft",
            "",
            linkedin_message,
        ]
    )


def parse_ai_revision(text: str) -> dict[str, str]:
    try:
        parsed = json.loads(strip_json_fence(text))
    except json.JSONDecodeError as error:
        raise ValueError("AI revision response was not valid JSON.") from error

    if not isinstance(parsed, dict):
        raise ValueError("AI revision response must be a JSON object.")

    required_keys = [*REQUIRED_DRAFT_KEYS, REVISION_NOTES_KEY]
    revision = {}
    for key in required_keys:
        value = parsed.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"AI revision response is missing required text: {key}")
        revision[key] = value.strip()

    return revision


def run_ai_draft_revision(
    role_display_name: str,
    profile: str,
    job_description: str,
    resume: str,
    cover_letter: str,
    linkedin_message: str,
    env_path: Path = DEFAULT_ENV_PATH,
) -> dict[str, str]:
    api_key = get_openai_api_key(env_path)
    if not api_key:
        raise AIReviewNotConfiguredError(
            "OPENAI_API_KEY was not found in the environment or local .env file."
        )

    model = get_openai_model(env_path)
    prompt = build_ai_revision_prompt(
        role_display_name,
        profile,
        job_description,
        resume,
        cover_letter,
        linkedin_message,
    )
    response_text = request_openai_text(
        prompt,
        api_key,
        model,
        AI_REVISION_INSTRUCTIONS,
    )
    return parse_ai_revision(response_text)

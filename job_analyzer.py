import re
from dataclasses import dataclass

from role_detector import matched_keywords


REQUIREMENT_HINTS = [
    "api",
    "backend",
    "customer",
    "developer",
    "git",
    "incident",
    "linux",
    "monitoring",
    "python",
    "security",
    "siem",
    "soc",
    "sql",
    "support",
    "troubleshooting",
    "vulnerability",
    "web",
]


@dataclass(frozen=True)
class JobAnalysis:
    role: str
    matched_keywords: list[str]
    requirement_lines: list[str]


def clean_requirement_line(line: str) -> str:
    cleaned = re.sub(r"^\s*[-*]+\s*", "", line.strip())
    cleaned = re.sub(r"^\s*\d+[.)]\s*", "", cleaned)
    return cleaned.strip()


def looks_like_requirement(line: str) -> bool:
    lower_line = line.lower()
    return any(hint in lower_line for hint in REQUIREMENT_HINTS)


def extract_requirement_lines(job_description: str, limit: int = 8) -> list[str]:
    requirements = []

    for raw_line in job_description.splitlines():
        line = clean_requirement_line(raw_line)
        if not line or line.endswith(":"):
            continue
        if len(line) > 180:
            continue
        if looks_like_requirement(line) and line not in requirements:
            requirements.append(line)
        if len(requirements) == limit:
            break

    if requirements:
        return requirements

    sentence_candidates = re.split(r"[.;]\s+", job_description)
    for sentence in sentence_candidates:
        line = clean_requirement_line(sentence)
        if line and looks_like_requirement(line) and line not in requirements:
            requirements.append(line)
        if len(requirements) == limit:
            break

    return requirements


def analyze_job(job_description: str, role: str) -> JobAnalysis:
    return JobAnalysis(
        role=role,
        matched_keywords=matched_keywords(job_description, role),
        requirement_lines=extract_requirement_lines(job_description),
    )


def bullet_list(items: list[str], fallback: str) -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}" for item in values)


def generate_application_review(
    role: str,
    role_display_name: str,
    job_description: str,
    scores: dict[str, int],
) -> str:
    analysis = analyze_job(job_description, role)

    return f"""# Application Review Notes

## Detected Role

{role} ({role_display_name})

## Role Scores

{bullet_list([f"{name}: {score}" for name, score in scores.items()], "No role scores available.")}

## Matched Keywords

{bullet_list(analysis.matched_keywords, "No role keywords matched. Review the job description manually.")}

## Job Lines To Review

{bullet_list(analysis.requirement_lines, "No concise requirement lines were extracted. Review the full job post manually.")}

## Before Applying Checklist

- Confirm every resume bullet is true and based on the profile files.
- Remove or soften anything that feels too strong for the actual experience.
- Check the company name, role title, and job URL before sending.
- Keep the generated files as drafts, not final applications.

## Future Automation/AI Unit Notes

- Use the profile files as the source of truth.
- Use the matched keywords as guidance, not as invented experience.
- Keep offline generation working even when AI mode is unavailable.
"""

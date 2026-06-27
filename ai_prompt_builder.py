from job_analyzer import analyze_job, bullet_list


AI_GUARDRAILS = [
    "Use only the candidate profile and generated drafts as source material.",
    "Do not invent employers, dates, certifications, education, or achievements.",
    "Preserve the candidate's real level as junior/entry-level where appropriate.",
    "Tailor wording to the job description without claiming false experience.",
    "Keep the final documents professional, concise, and ATS-friendly.",
    "If a job requirement is not supported by the profile, mark it as a gap.",
]


def generate_ai_brief(
    role: str,
    role_display_name: str,
    profile: str,
    job_description: str,
    scores: dict[str, int],
    resume: str,
    cover_letter: str,
    linkedin_message: str,
) -> str:
    analysis = analyze_job(job_description, role)

    return f"""# AI Brief For Future Tailoring

This file is an offline preparation brief. It does not call any AI API.

## Goal

Improve the generated application documents for this specific job while keeping all claims truthful and based on the candidate profile.

## Detected Role

{role} ({role_display_name})

## Role Scores

{bullet_list([f"{name}: {score}" for name, score in scores.items()], "No role scores available.")}

## Matched Keywords

{bullet_list(analysis.matched_keywords, "No role keywords matched. Review manually.")}

## Requirement Lines To Consider

{bullet_list(analysis.requirement_lines, "No concise requirement lines were extracted. Review manually.")}

## Strict Guardrails

{bullet_list(AI_GUARDRAILS, "No guardrails configured.")}

## Candidate Profile Source

```markdown
{profile.strip()}
```

## Job Description

```text
{job_description.strip()}
```

## Current Resume Draft

```markdown
{resume.strip()}
```

## Current Cover Letter Draft

```markdown
{cover_letter.strip()}
```

## Current LinkedIn Message Draft

```text
{linkedin_message.strip()}
```

## Expected AI Output Later

- Improved resume in Markdown.
- Improved cover letter in Markdown.
- Improved LinkedIn message in plain text.
- Short list of unsupported job requirements, if any.
"""

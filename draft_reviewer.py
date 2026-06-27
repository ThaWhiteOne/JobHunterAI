from dataclasses import dataclass
from pathlib import Path
from typing import Any


PLACEHOLDER_TERMS = [
    "todo",
    "tbd",
    "lorem ipsum",
    "[company]",
    "[role]",
    "insert company",
    "insert role",
]

VERIFY_TERMS = [
    "certified",
    "certification",
    "degree",
    "years of experience",
    "expert",
    "senior",
]


@dataclass(frozen=True)
class ReviewFinding:
    severity: str
    title: str
    detail: str


@dataclass(frozen=True)
class DraftReview:
    score: int
    readiness: str
    findings: list[ReviewFinding]
    strengths: list[str]
    next_actions: list[str]


def resolve_path(path_text: str, manifest_path: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path

    candidates = [
        Path.cwd() / path,
        manifest_path.parent / path,
        manifest_path.parent.parent / path,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


def find_generated_file(
    manifest: dict[str, Any],
    manifest_path: Path,
    filename: str,
) -> Path | None:
    for path_text in manifest.get("generated_files", []):
        path = resolve_path(str(path_text), manifest_path)
        if path.name == filename:
            return path
    return None


def read_generated_file(
    manifest: dict[str, Any],
    manifest_path: Path,
    filename: str,
) -> str:
    path = find_generated_file(manifest, manifest_path, filename)
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def word_count(text: str) -> int:
    return len([word for word in text.replace("\n", " ").split(" ") if word.strip()])


def contains_term(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def missing_keywords(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if not contains_term(text, keyword)]


def readiness_from_score(score: int) -> str:
    if score >= 85:
        return "Ready after final human check"
    if score >= 70:
        return "Needs small edits before applying"
    return "Needs revision before applying"


def score_findings(findings: list[ReviewFinding]) -> int:
    score = 100
    for finding in findings:
        if finding.severity == "high":
            score -= 20
        elif finding.severity == "medium":
            score -= 10
        else:
            score -= 5
    return max(score, 0)


def review_drafts(manifest: dict[str, Any], manifest_path: Path) -> DraftReview:
    resume = read_generated_file(manifest, manifest_path, "resume.md")
    cover_letter = read_generated_file(manifest, manifest_path, "cover_letter.md")
    linkedin_message = read_generated_file(manifest, manifest_path, "linkedin_message.txt")
    combined_text = "\n".join([resume, cover_letter, linkedin_message])
    findings = []

    if not resume:
        findings.append(
            ReviewFinding("high", "Missing resume draft", "resume.md was not found.")
        )
    elif word_count(resume) < 120:
        findings.append(
            ReviewFinding(
                "high",
                "Resume may be too short",
                "A recruiter may not see enough evidence of skills and projects.",
            )
        )

    if not cover_letter:
        findings.append(
            ReviewFinding(
                "high",
                "Missing cover letter draft",
                "cover_letter.md was not found.",
            )
        )
    elif word_count(cover_letter) < 70:
        findings.append(
            ReviewFinding(
                "medium",
                "Cover letter may be too short",
                "Add one or two concrete lines connecting experience to the job.",
            )
        )

    if not linkedin_message:
        findings.append(
            ReviewFinding(
                "medium",
                "Missing LinkedIn message",
                "linkedin_message.txt was not found.",
            )
        )
    elif word_count(linkedin_message) > 120:
        findings.append(
            ReviewFinding(
                "low",
                "LinkedIn message may be too long",
                "Recruiter messages usually work best when they are short.",
            )
        )

    placeholder_hits = [
        term for term in PLACEHOLDER_TERMS if contains_term(combined_text, term)
    ]
    if placeholder_hits:
        findings.append(
            ReviewFinding(
                "high",
                "Placeholder text found",
                f"Remove or replace: {', '.join(placeholder_hits)}.",
            )
        )

    verify_hits = [term for term in VERIFY_TERMS if contains_term(combined_text, term)]
    if verify_hits:
        findings.append(
            ReviewFinding(
                "medium",
                "Claims need manual verification",
                f"Check that these claims are true and profile-backed: {', '.join(verify_hits)}.",
            )
        )

    keywords = manifest.get("matched_keywords", [])
    missing = missing_keywords(combined_text, keywords)
    if keywords and len(missing) == len(keywords):
        findings.append(
            ReviewFinding(
                "high",
                "No matched job keywords appear in drafts",
                "The generated application may not look tailored to the job.",
            )
        )
    elif len(missing) > max(2, len(keywords) // 2):
        findings.append(
            ReviewFinding(
                "medium",
                "Several matched job keywords are missing",
                f"Consider naturally adding relevant terms: {', '.join(missing[:6])}.",
            )
        )

    strengths = []
    if resume:
        strengths.append("Resume draft exists and can be reviewed.")
    if cover_letter:
        strengths.append("Cover letter draft exists and can be reviewed.")
    if keywords and len(missing) < len(keywords):
        strengths.append("Drafts include at least some matched job keywords.")
    if "Do not submit applications automatically without user confirmation." in manifest.get(
        "automation_guardrails", []
    ):
        strengths.append("Automation guardrails are present.")

    next_actions = [
        "Read the resume and cover letter as if you are the recruiter.",
        "Confirm every claim is true and supported by the profile files.",
        "Edit weak or generic lines before sending.",
        "Apply manually only after review.",
    ]

    score = score_findings(findings)
    return DraftReview(
        score=score,
        readiness=readiness_from_score(score),
        findings=findings,
        strengths=strengths,
        next_actions=next_actions,
    )


def finding_lines(findings: list[ReviewFinding]) -> list[str]:
    if not findings:
        return ["- No major issues found by the offline reviewer."]
    return [
        f"- [{finding.severity.upper()}] {finding.title}: {finding.detail}"
        for finding in findings
    ]


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items] or ["- None."]


def build_recruiter_review_report(
    manifest: dict[str, Any],
    manifest_path: Path,
) -> str:
    review = review_drafts(manifest, manifest_path)
    lines = [
        "# Recruiter Review Agent Report",
        "",
        "This is an offline rule-based review. It does not submit applications or call an AI API.",
        "",
        "## Readiness",
        "",
        f"Score: {review.score}/100",
        f"Status: {review.readiness}",
        "",
        "## Findings",
        "",
        *finding_lines(review.findings),
        "",
        "## Strengths",
        "",
        *bullet_lines(review.strengths),
        "",
        "## Next Actions",
        "",
        *bullet_lines(review.next_actions),
    ]
    return "\n".join(lines)


def recruiter_review_path(manifest_path: Path) -> Path:
    return manifest_path.parent / "recruiter_review.md"

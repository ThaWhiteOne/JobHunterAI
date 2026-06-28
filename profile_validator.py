import argparse
import re
from dataclasses import dataclass
from pathlib import Path

from config import (
    MASTER_PROFILE_PATH,
    OUTPUTS_DIR,
    RESUME_TEMPLATE_PATH,
    ROLE_PROFILE_MAP,
)
from file_utils import write_text_file


PLACEHOLDER_TERMS = [
    "todo",
    "tbd",
    "later",
    "your ",
    "[",
    "]",
]

MASTER_REQUIRED_TERMS = [
    "Name:",
    "Location:",
    "Email:",
    "Phone:",
    "GitHub:",
    "Languages:",
    "Experience:",
    "Projects:",
]

ROLE_SECTION_GROUPS = [
    ["Professional Summary"],
    ["Technical Skills", "Core Skills"],
    ["Experience", "Relevant Experience"],
    ["Projects", "Selected Projects"],
]

TEMPLATE_FIELDS = [
    "{contact_block}",
    "{target_role}",
    "{professional_summary}",
    "{core_skills}",
    "{relevant_experience}",
    "{selected_projects}",
]


@dataclass(frozen=True)
class ProfileIssue:
    severity: str
    path: Path
    message: str


@dataclass(frozen=True)
class ProfileValidation:
    checked_files: list[Path]
    errors: list[ProfileIssue]
    warnings: list[ProfileIssue]

    @property
    def is_ready(self) -> bool:
        return not self.errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate JobHunterAI profile and template source files."
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write outputs/profile_validation_report.md.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures.",
    )
    return parser.parse_args()


def read_optional(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


def has_any_term(text: str, terms: list[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def has_year_or_date(text: str) -> bool:
    return bool(re.search(r"\b(19|20)\d{2}\b", text))


def missing_terms(text: str, terms: list[str]) -> list[str]:
    return [term for term in terms if term.lower() not in text.lower()]


def placeholder_hits(text: str) -> list[str]:
    lowered = text.lower()
    return [term for term in PLACEHOLDER_TERMS if term in lowered]


def validate_file_exists(path: Path, errors: list[ProfileIssue]) -> bool:
    if not path.exists():
        errors.append(ProfileIssue("error", path, "Required source file is missing."))
        return False
    if not path.is_file():
        errors.append(ProfileIssue("error", path, "Expected a file but found something else."))
        return False
    return True


def validate_master_profile(
    path: Path,
    errors: list[ProfileIssue],
    warnings: list[ProfileIssue],
) -> None:
    if not validate_file_exists(path, errors):
        return

    text = read_optional(path)
    if not text:
        errors.append(ProfileIssue("error", path, "Master profile is empty."))
        return

    missing = missing_terms(text, MASTER_REQUIRED_TERMS)
    if missing:
        errors.append(
            ProfileIssue(
                "error",
                path,
                f"Missing required master profile fields: {', '.join(missing)}.",
            )
        )

    placeholders = placeholder_hits(text)
    if placeholders:
        warnings.append(
            ProfileIssue(
                "warning",
                path,
                f"Placeholder-style text found: {', '.join(placeholders)}.",
            )
        )

    if not has_year_or_date(text):
        warnings.append(
            ProfileIssue(
                "warning",
                path,
                "No years/dates found. Add truthful dates once so AI can use them safely.",
            )
        )


def validate_role_profile(
    path: Path,
    errors: list[ProfileIssue],
    warnings: list[ProfileIssue],
) -> None:
    if not validate_file_exists(path, errors):
        return

    text = read_optional(path)
    if not text:
        errors.append(ProfileIssue("error", path, "Role profile is empty."))
        return

    for section_group in ROLE_SECTION_GROUPS:
        if not has_any_term(text, section_group):
            errors.append(
                ProfileIssue(
                    "error",
                    path,
                    f"Missing section like: {' or '.join(section_group)}.",
                )
            )

    placeholders = placeholder_hits(text)
    if placeholders:
        warnings.append(
            ProfileIssue(
                "warning",
                path,
                f"Placeholder-style text found: {', '.join(placeholders)}.",
            )
        )

    if not has_year_or_date(text):
        warnings.append(
            ProfileIssue(
                "warning",
                path,
                "No years/dates found. Add truthful dates once so AI can use them safely.",
            )
        )


def validate_resume_template(
    path: Path,
    errors: list[ProfileIssue],
) -> None:
    if not validate_file_exists(path, errors):
        return

    text = read_optional(path)
    if not text:
        errors.append(ProfileIssue("error", path, "Resume template is empty."))
        return

    missing = missing_terms(text, TEMPLATE_FIELDS)
    if missing:
        errors.append(
            ProfileIssue(
                "error",
                path,
                f"Missing template placeholders: {', '.join(missing)}.",
            )
        )


def validate_profiles(
    master_profile_path: Path = MASTER_PROFILE_PATH,
    role_profile_paths: list[Path] | None = None,
    resume_template_path: Path = RESUME_TEMPLATE_PATH,
) -> ProfileValidation:
    role_paths = role_profile_paths or list(ROLE_PROFILE_MAP.values())
    checked_files = [master_profile_path, *role_paths, resume_template_path]
    errors: list[ProfileIssue] = []
    warnings: list[ProfileIssue] = []

    validate_master_profile(master_profile_path, errors, warnings)
    for role_path in role_paths:
        validate_role_profile(role_path, errors, warnings)
    validate_resume_template(resume_template_path, errors)

    return ProfileValidation(checked_files, errors, warnings)


def issue_lines(issues: list[ProfileIssue]) -> list[str]:
    if not issues:
        return ["- None."]
    return [
        f"- [{issue.severity.upper()}] {issue.path}: {issue.message}"
        for issue in issues
    ]


def build_profile_validation_report(validation: ProfileValidation) -> str:
    if validation.errors:
        status = "Blocked"
    elif validation.warnings:
        status = "Ready with warnings"
    else:
        status = "Ready"

    lines = [
        "# Profile Validation Report",
        "",
        f"Status: {status}",
        "",
        "## Files Checked",
        "",
        *[f"- {path}" for path in validation.checked_files],
        "",
        "## Errors",
        "",
        *issue_lines(validation.errors),
        "",
        "## Warnings",
        "",
        *issue_lines(validation.warnings),
        "",
        "## Next Step",
        "",
        "Update profile files once, then reuse them for automated job-specific drafts.",
    ]
    return "\n".join(lines)


def report_path() -> Path:
    return OUTPUTS_DIR / "profile_validation_report.md"


def main() -> None:
    args = parse_args()
    validation = validate_profiles()
    report = build_profile_validation_report(validation)
    print(report)

    if args.write_report:
        path = report_path()
        write_text_file(path, report)
        print("")
        print(f"Profile validation report written: {path}")

    if validation.errors or (args.strict and validation.warnings):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

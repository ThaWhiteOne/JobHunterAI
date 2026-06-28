import argparse
from dataclasses import dataclass
from pathlib import Path

from config import ROLE_DISPLAY_NAMES
from file_utils import read_text_file, write_text_file
from job_analyzer import extract_requirement_lines
from job_intake import DEFAULT_JOBS_DIR, list_saved_jobs
from role_detector import detect_role, matched_keywords, score_roles


DEFAULT_MATCH_REPORT_NAME = "job_match_report.md"

POSITIVE_SIGNALS = [
    "junior",
    "entry level",
    "graduate",
    "trainee",
    "remote",
    "hybrid",
    "python",
    "sql",
    "linux",
    "git",
    "support",
    "troubleshooting",
    "soc",
    "siem",
]

RISK_SIGNALS = [
    "senior",
    "lead ",
    "principal",
    "manager",
    "architect",
    "7+ years",
    "5+ years",
    "minimum 5 years",
    "expert",
]


@dataclass(frozen=True)
class JobMatch:
    company: str
    position: str
    url: str
    job_file: Path
    role: str
    score: int
    recommendation: str
    role_scores: dict[str, int]
    matched_keywords: list[str]
    positive_signals: list[str]
    risk_signals: list[str]
    requirement_lines: list[str]
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Score saved jobs before generating application packages."
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=DEFAULT_JOBS_DIR,
        help="Folder containing saved job descriptions and job_index.json.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Only print jobs with this score or higher.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write a Markdown match report into the jobs folder.",
    )
    return parser.parse_args()


def find_signals(text: str, signals: list[str]) -> list[str]:
    lower_text = text.lower()
    return sorted(signal for signal in signals if signal in lower_text)


def recommendation_for_score(score: int) -> str:
    if score >= 70:
        return "strong"
    if score >= 45:
        return "review"
    return "low"


def calculate_match_score(
    role_scores: dict[str, int],
    keyword_matches: list[str],
    positive_signals: list[str],
    risk_signals: list[str],
) -> int:
    best_role_score = max(role_scores.values(), default=0)
    role_points = min(best_role_score * 8, 40)
    keyword_points = min(len(keyword_matches) * 5, 30)
    positive_points = min(len(positive_signals) * 4, 20)
    risk_penalty = min(len(risk_signals) * 8, 30)
    score = role_points + keyword_points + positive_points + 10 - risk_penalty
    return max(0, min(100, score))


def resolve_job_file(job_file: str, jobs_dir: Path) -> Path:
    path = Path(job_file)
    if path.is_absolute() or path.exists():
        return path
    fallback = jobs_dir / path.name
    return fallback


def match_saved_job(job: dict[str, str], jobs_dir: Path = DEFAULT_JOBS_DIR) -> JobMatch:
    company = job.get("company", "unknown company")
    position = job.get("position", "unknown position")
    url = job.get("url", "")
    job_file = resolve_job_file(job.get("job_file", ""), jobs_dir)

    try:
        job_text = read_text_file(job_file, required=True)
        role_scores = score_roles(job_text)
        role = detect_role(job_text)
        keyword_matches = matched_keywords(job_text, role)
        positive = find_signals(job_text, POSITIVE_SIGNALS)
        risks = find_signals(job_text, RISK_SIGNALS)
        score = calculate_match_score(role_scores, keyword_matches, positive, risks)
        recommendation = recommendation_for_score(score)
        requirements = extract_requirement_lines(job_text, limit=6)
        return JobMatch(
            company=company,
            position=position,
            url=url,
            job_file=job_file,
            role=role,
            score=score,
            recommendation=recommendation,
            role_scores=role_scores,
            matched_keywords=keyword_matches,
            positive_signals=positive,
            risk_signals=risks,
            requirement_lines=requirements,
        )
    except (FileNotFoundError, ValueError) as error:
        return JobMatch(
            company=company,
            position=position,
            url=url,
            job_file=job_file,
            role="unknown",
            score=0,
            recommendation="error",
            role_scores={},
            matched_keywords=[],
            positive_signals=[],
            risk_signals=[],
            requirement_lines=[],
            error=str(error),
        )


def match_saved_jobs(jobs_dir: Path = DEFAULT_JOBS_DIR) -> list[JobMatch]:
    matches = [match_saved_job(job, jobs_dir) for job in list_saved_jobs(jobs_dir)]
    return sorted(matches, key=lambda match: match.score, reverse=True)


def format_scores(scores: dict[str, int]) -> str:
    if not scores:
        return "not available"
    return ", ".join(f"{role}: {score}" for role, score in scores.items())


def bullet_list(items: list[str], fallback: str) -> str:
    values = items or [fallback]
    return "\n".join(f"- {item}" for item in values)


def build_match_report(matches: list[JobMatch]) -> str:
    strong_count = sum(1 for match in matches if match.recommendation == "strong")
    review_count = sum(1 for match in matches if match.recommendation == "review")
    low_count = sum(1 for match in matches if match.recommendation == "low")
    error_count = sum(1 for match in matches if match.recommendation == "error")
    lines = [
        "# Job Match Report",
        "",
        f"Strong matches: {strong_count}",
        f"Review matches: {review_count}",
        f"Low matches: {low_count}",
        f"Errors: {error_count}",
        "",
        "## Ranked Jobs",
        "",
    ]
    for index, match in enumerate(matches, start=1):
        role_label = ROLE_DISPLAY_NAMES.get(match.role, match.role.title())
        lines.extend(
            [
                f"### {index}. {match.company} - {match.position}",
                "",
                f"Score: {match.score}/100",
                f"Recommendation: {match.recommendation}",
                f"Detected role: {match.role} ({role_label})",
                f"Job file: {match.job_file}",
            ]
        )
        if match.url:
            lines.append(f"URL: {match.url}")
        if match.error:
            lines.extend(["", f"Error: {match.error}", ""])
            continue
        lines.extend(
            [
                f"Role scores: {format_scores(match.role_scores)}",
                "",
                "Matched keywords:",
                bullet_list(match.matched_keywords, "No role keywords matched."),
                "",
                "Positive signals:",
                bullet_list(match.positive_signals, "No positive signals found."),
                "",
                "Risk signals:",
                bullet_list(match.risk_signals, "No obvious risk signals found."),
                "",
                "Requirement lines to review:",
                bullet_list(match.requirement_lines, "No concise requirement lines extracted."),
                "",
            ]
        )
    return "\n".join(lines)


def write_match_report(
    matches: list[JobMatch],
    jobs_dir: Path = DEFAULT_JOBS_DIR,
    report_name: str = DEFAULT_MATCH_REPORT_NAME,
) -> Path:
    report_path = jobs_dir / report_name
    write_text_file(report_path, build_match_report(matches))
    return report_path


def print_matches(matches: list[JobMatch], min_score: int = 0) -> None:
    visible_matches = [match for match in matches if match.score >= min_score]
    if not visible_matches:
        print("No saved jobs matched the selected score filter.")
        return
    for match in visible_matches:
        print(
            f"{match.score:3d} [{match.recommendation}] "
            f"{match.company} - {match.position} ({match.role})"
        )


def main() -> None:
    args = parse_args()
    try:
        matches = match_saved_jobs(args.jobs_dir)
        print_matches(matches, args.min_score)
        if args.write_report:
            report_path = write_match_report(matches, args.jobs_dir)
            print(f"Report file: {report_path}")
    except ValueError as error:
        raise SystemExit(f"Job matching failed.\nError: {error}") from error


if __name__ == "__main__":
    main()

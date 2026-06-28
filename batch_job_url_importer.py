import argparse
from dataclasses import dataclass
from pathlib import Path

from config import ROLE_DISPLAY_NAMES
from file_utils import read_text_file, write_text_file
from job_intake import DEFAULT_JOBS_DIR
from job_url_importer import DEFAULT_TIMEOUT_SECONDS, ImportedJob, import_job_url
from role_detector import detect_role, score_roles


DEFAULT_REPORT_NAME = "url_import_report.md"


@dataclass(frozen=True)
class UrlImportResult:
    url: str
    success: bool
    company: str = ""
    position: str = ""
    role: str = ""
    scores: dict[str, int] | None = None
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import multiple public job posting URLs into the local job inbox."
    )
    parser.add_argument(
        "--urls-file",
        type=Path,
        required=True,
        help="Text file containing one job posting URL per line.",
    )
    parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=DEFAULT_JOBS_DIR,
        help="Folder where imported job descriptions are saved.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Fetch timeout per URL in seconds.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write a Markdown import report into the jobs folder.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop importing after the first failed URL.",
    )
    return parser.parse_args()


def read_url_list(path: Path) -> list[str]:
    text = read_text_file(path, required=True)
    urls: list[str] = []
    seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line not in seen:
            urls.append(line)
            seen.add(line)
    if not urls:
        raise ValueError(f"No URLs found in: {path}")
    return urls


def detect_imported_role(imported_job: ImportedJob) -> tuple[str, dict[str, int]]:
    text = "\n".join([imported_job.position, imported_job.description])
    scores = score_roles(text)
    try:
        role = detect_role(text)
    except ValueError:
        role = "unknown"
    return role, scores


def import_url_batch(
    urls: list[str],
    jobs_dir: Path = DEFAULT_JOBS_DIR,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    stop_on_error: bool = False,
) -> list[UrlImportResult]:
    results: list[UrlImportResult] = []
    for url in urls:
        try:
            imported = import_job_url(url=url, jobs_dir=jobs_dir, timeout=timeout)
            role, scores = detect_imported_role(imported)
            results.append(
                UrlImportResult(
                    url=url,
                    success=True,
                    company=imported.company,
                    position=imported.position,
                    role=role,
                    scores=scores,
                )
            )
        except (ConnectionError, OSError, ValueError) as error:
            results.append(UrlImportResult(url=url, success=False, error=str(error)))
            if stop_on_error:
                break
    return results


def format_scores(scores: dict[str, int] | None) -> str:
    if not scores:
        return "not available"
    return ", ".join(f"{role}: {score}" for role, score in scores.items())


def build_import_report(results: list[UrlImportResult]) -> str:
    imported_count = sum(1 for result in results if result.success)
    failed_count = len(results) - imported_count
    lines = [
        "# Job URL Import Report",
        "",
        f"Imported: {imported_count}",
        f"Failed: {failed_count}",
        "",
        "## Results",
        "",
    ]
    for index, result in enumerate(results, start=1):
        lines.append(f"### {index}. {result.url}")
        if not result.success:
            lines.extend(["", "Status: failed", f"Error: {result.error}", ""])
            continue
        role_label = ROLE_DISPLAY_NAMES.get(result.role, result.role.title())
        lines.extend(
            [
                "",
                "Status: imported",
                f"Company: {result.company}",
                f"Position: {result.position}",
                f"Detected role: {result.role} ({role_label})",
                f"Role scores: {format_scores(result.scores)}",
                "",
            ]
        )
    return "\n".join(lines)


def write_import_report(
    results: list[UrlImportResult],
    jobs_dir: Path = DEFAULT_JOBS_DIR,
    report_name: str = DEFAULT_REPORT_NAME,
) -> Path:
    report_path = jobs_dir / report_name
    write_text_file(report_path, build_import_report(results))
    return report_path


def print_summary(results: list[UrlImportResult]) -> None:
    imported_count = sum(1 for result in results if result.success)
    failed_count = len(results) - imported_count
    print(f"Imported {imported_count} job URL(s).")
    print(f"Failed {failed_count} job URL(s).")
    for result in results:
        if result.success:
            print(f"- OK: {result.company} - {result.position} [{result.role}]")
        else:
            print(f"- FAILED: {result.url} -> {result.error}")


def main() -> None:
    args = parse_args()
    try:
        urls = read_url_list(args.urls_file)
        results = import_url_batch(
            urls=urls,
            jobs_dir=args.jobs_dir,
            timeout=args.timeout,
            stop_on_error=args.stop_on_error,
        )
        print_summary(results)
        if args.write_report:
            report_path = write_import_report(results, args.jobs_dir)
            print(f"Report file: {report_path}")
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Batch job URL import failed.\nError: {error}") from error


if __name__ == "__main__":
    main()

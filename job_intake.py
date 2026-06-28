import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from file_utils import read_text_file, write_text_file


DEFAULT_JOBS_DIR = Path("jobs")
JOB_INDEX_NAME = "job_index.json"


@dataclass(frozen=True)
class SavedJob:
    company: str
    position: str
    url: str
    source: str
    saved_at: str
    job_file: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save job descriptions into the local JobHunterAI job inbox."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser(
        "add",
        help="Save one job description as a .txt file.",
    )
    add_parser.add_argument("--company", required=True, help="Company name.")
    add_parser.add_argument("--position", required=True, help="Job title.")
    add_parser.add_argument("--url", default="", help="Original job post URL.")
    add_parser.add_argument("--source", default="manual", help="Where the job came from.")
    add_parser.add_argument("--text", default="", help="Job description text.")
    add_parser.add_argument(
        "--from-file",
        type=Path,
        help="Read job description text from an existing file.",
    )
    add_parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=DEFAULT_JOBS_DIR,
        help="Folder where job descriptions are saved.",
    )

    list_parser = subparsers.add_parser(
        "list",
        help="List saved job descriptions.",
    )
    list_parser.add_argument(
        "--jobs-dir",
        type=Path,
        default=DEFAULT_JOBS_DIR,
        help="Folder where job descriptions are saved.",
    )

    return parser.parse_args()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "job"


def index_path(jobs_dir: Path) -> Path:
    return jobs_dir / JOB_INDEX_NAME


def load_index(jobs_dir: Path) -> dict[str, Any]:
    path = index_path(jobs_dir)
    if not path.exists():
        return {"jobs": []}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid job index JSON: {path}") from error

    if not isinstance(data, dict):
        raise ValueError("Job index must contain a JSON object.")
    if not isinstance(data.get("jobs"), list):
        raise ValueError("Job index must contain a jobs list.")

    return data


def save_index(jobs_dir: Path, index: dict[str, Any]) -> Path:
    path = index_path(jobs_dir)
    write_text_file(path, json.dumps(index, indent=2))
    return path


def unique_job_path(jobs_dir: Path, company: str, position: str) -> Path:
    base_name = f"{slugify(company)}-{slugify(position)}"
    candidate = jobs_dir / f"{base_name}.txt"
    counter = 2
    while candidate.exists():
        candidate = jobs_dir / f"{base_name}-{counter}.txt"
        counter += 1
    return candidate


def read_job_text(text: str, from_file: Path | None) -> str:
    if text.strip() and from_file is not None:
        raise ValueError("Use either --text or --from-file, not both.")
    if from_file is not None:
        return read_text_file(from_file, required=True)
    if text.strip():
        return text.strip()
    raise ValueError("Job description text is required. Use --text or --from-file.")


def build_job_file_content(
    company: str,
    position: str,
    url: str,
    source: str,
    saved_at: str,
    job_text: str,
) -> str:
    return "\n".join(
        [
            f"Company: {company}",
            f"Position: {position}",
            f"URL: {url or 'not provided'}",
            f"Source: {source}",
            f"Saved at: {saved_at}",
            "",
            "Job Description:",
            "",
            job_text.strip(),
        ]
    )


def saved_job_to_index_item(saved_job: SavedJob) -> dict[str, str]:
    return {
        "company": saved_job.company,
        "position": saved_job.position,
        "url": saved_job.url,
        "source": saved_job.source,
        "saved_at": saved_job.saved_at,
        "job_file": saved_job.job_file.as_posix(),
    }


def save_job_description(
    company: str,
    position: str,
    job_text: str,
    jobs_dir: Path = DEFAULT_JOBS_DIR,
    url: str = "",
    source: str = "manual",
) -> SavedJob:
    if not company.strip():
        raise ValueError("Company is required.")
    if not position.strip():
        raise ValueError("Position is required.")
    if not job_text.strip():
        raise ValueError("Job description text is required.")

    saved_at = datetime.now(timezone.utc).isoformat()
    job_path = unique_job_path(jobs_dir, company, position)
    content = build_job_file_content(
        company.strip(),
        position.strip(),
        url.strip(),
        source.strip() or "manual",
        saved_at,
        job_text,
    )
    write_text_file(job_path, content)

    saved_job = SavedJob(
        company=company.strip(),
        position=position.strip(),
        url=url.strip(),
        source=source.strip() or "manual",
        saved_at=saved_at,
        job_file=job_path,
    )
    index = load_index(jobs_dir)
    index["jobs"].append(saved_job_to_index_item(saved_job))
    save_index(jobs_dir, index)
    return saved_job


def list_saved_jobs(jobs_dir: Path = DEFAULT_JOBS_DIR) -> list[dict[str, str]]:
    index = load_index(jobs_dir)
    jobs = index.get("jobs", [])
    return [job for job in jobs if isinstance(job, dict)]


def format_job_line(index: int, job: dict[str, str]) -> str:
    company = job.get("company", "unknown company")
    position = job.get("position", "unknown position")
    job_file = job.get("job_file", "missing file")
    return f"{index}. {company} - {position} -> {job_file}"


def print_saved_jobs(jobs: list[dict[str, str]]) -> None:
    if not jobs:
        print("No saved jobs found.")
        return

    for index, job in enumerate(jobs, start=1):
        print(format_job_line(index, job))


def main() -> None:
    args = parse_args()

    try:
        if args.command == "add":
            job_text = read_job_text(args.text, args.from_file)
            saved_job = save_job_description(
                company=args.company,
                position=args.position,
                url=args.url,
                source=args.source,
                job_text=job_text,
                jobs_dir=args.jobs_dir,
            )
            print("Saved job description.")
            print(f"Job file: {saved_job.job_file}")
            print(f"Index file: {index_path(args.jobs_dir)}")
        elif args.command == "list":
            print_saved_jobs(list_saved_jobs(args.jobs_dir))
    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Job intake failed.\nError: {error}") from error


if __name__ == "__main__":
    main()

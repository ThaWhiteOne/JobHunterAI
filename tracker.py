import argparse

from config import JOB_TRACKER_DB_PATH
from tracker_db import (
    VALID_STATUSES,
    add_job,
    get_job_stats,
    list_jobs,
    update_job_status,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Track job applications.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a job application.")
    add_parser.add_argument("--company", required=True, help="Company name.")
    add_parser.add_argument("--position", required=True, help="Job title.")
    add_parser.add_argument("--url", default="", help="Job post URL.")
    add_parser.add_argument("--role", default="", help="Detected or chosen role.")
    add_parser.add_argument("--output-dir", default="", help="Generated files folder.")
    add_parser.add_argument(
        "--status",
        default="saved",
        choices=VALID_STATUSES,
        help="Application status.",
    )
    add_parser.add_argument("--notes", default="", help="Optional notes.")

    list_parser = subparsers.add_parser("list", help="List tracked jobs.")
    list_parser.add_argument(
        "--status",
        choices=VALID_STATUSES,
        default="",
        help="Only list jobs with this status.",
    )
    list_parser.add_argument(
        "--role",
        default="",
        help="Only list jobs with this role.",
    )

    subparsers.add_parser("stats", help="Show job tracker summary counts.")

    update_parser = subparsers.add_parser("update", help="Update a job status.")
    update_parser.add_argument("--id", type=int, required=True, help="Job id.")
    update_parser.add_argument(
        "--status",
        required=True,
        choices=VALID_STATUSES,
        help="New application status.",
    )

    return parser.parse_args()


def print_jobs(jobs: list[dict[str, str | int]]) -> None:
    if not jobs:
        print("No tracked jobs yet.")
        return

    for job in jobs:
        print(
            f"{job['id']}. {job['company']} - {job['position']} "
            f"[{job['status']}]"
        )
        if job["role"]:
            print(f"   Role: {job['role']}")
        if job["url"]:
            print(f"   URL: {job['url']}")
        if job["notes"]:
            print(f"   Notes: {job['notes']}")
        if job["output_dir"]:
            print(f"   Output: {job['output_dir']}")
        print(f"   Created: {job['created_at']}")


def print_stats(stats: dict[str, int | dict[str, int]]) -> None:
    print(f"Total jobs: {stats['total']}")

    print("By status:")
    for status, count in stats["by_status"].items():
        print(f"- {status}: {count}")

    print("By role:")
    if not stats["by_role"]:
        print("- none: 0")
        return
    for role, count in stats["by_role"].items():
        print(f"- {role}: {count}")


def main() -> None:
    args = parse_args()

    try:
        if args.command == "add":
            job_id = add_job(
                JOB_TRACKER_DB_PATH,
                company=args.company,
                position=args.position,
                url=args.url,
                role=args.role,
                status=args.status,
                notes=args.notes,
                output_dir=args.output_dir,
            )
            print(f"Added job #{job_id}.")
            return

        if args.command == "list":
            print_jobs(
                list_jobs(
                    JOB_TRACKER_DB_PATH,
                    status_filter=args.status,
                    role_filter=args.role,
                )
            )
            return

        if args.command == "stats":
            print_stats(get_job_stats(JOB_TRACKER_DB_PATH))
            return

        if args.command == "update":
            update_job_status(JOB_TRACKER_DB_PATH, args.id, args.status)
            print(f"Updated job #{args.id} to {args.status}.")
            return

    except ValueError as error:
        raise SystemExit(f"Job tracker failed.\nError: {error}") from error


if __name__ == "__main__":
    main()

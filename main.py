import argparse
from pathlib import Path

from config import (
    JOB_TRACKER_DB_PATH,
    OUTPUTS_DIR,
    ROLE_DISPLAY_NAMES,
    SAMPLE_JOB_PATH,
)
from file_utils import read_text_file, write_text_file
from generators import (
    generate_cover_letter,
    generate_linkedin_message,
    generate_resume,
)
from profile_selector import select_profile
from role_detector import detect_role, score_roles
from tracker_db import add_job


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate tailored job application files from a job description."
    )
    parser.add_argument(
        "job_file",
        nargs="?",
        type=Path,
        help="Optional path to a job description file.",
    )
    parser.add_argument(
        "--job",
        dest="job_option",
        type=Path,
        help="Optional path to a job description file.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print role scores and profile selection details.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Folder where generated files should be written.",
    )
    parser.add_argument(
        "--track",
        action="store_true",
        help="Save this generated application to the local job tracker.",
    )
    parser.add_argument(
        "--company",
        default="",
        help="Company name for --track.",
    )
    parser.add_argument(
        "--position",
        default="",
        help="Job title for --track.",
    )
    parser.add_argument(
        "--url",
        default="",
        help="Job post URL for --track.",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes for --track.",
    )
    return parser.parse_args()


def get_job_path(args: argparse.Namespace) -> Path:
    return args.job_option or args.job_file or SAMPLE_JOB_PATH


def get_output_dir(args: argparse.Namespace) -> Path:
    return args.output_dir or OUTPUTS_DIR


def validate_tracking_args(args: argparse.Namespace) -> None:
    if not args.track:
        return
    if not args.company.strip():
        raise ValueError("--company is required when using --track.")
    if not args.position.strip():
        raise ValueError("--position is required when using --track.")


def track_generated_application(args: argparse.Namespace, role: str) -> int | None:
    if not args.track:
        return None

    validate_tracking_args(args)
    return add_job(
        JOB_TRACKER_DB_PATH,
        company=args.company,
        position=args.position,
        url=args.url,
        role=role,
        status="generated",
        notes=args.notes,
    )


def main() -> None:
    args = parse_args()

    try:
        validate_tracking_args(args)
        job_path = get_job_path(args)
        job_description = read_text_file(job_path, required=True)
        role = detect_role(job_description)
        scores = score_roles(job_description)
        role_display_name = ROLE_DISPLAY_NAMES.get(role, role.title())

        profile, profile_path, used_fallback = select_profile(role)

        resume = generate_resume(role, role_display_name, profile, job_description)
        cover_letter = generate_cover_letter(
            role,
            role_display_name,
            profile,
            job_description,
        )
        linkedin_message = generate_linkedin_message(role, role_display_name)

        output_dir = get_output_dir(args)
        resume_path = output_dir / "resume.md"
        cover_letter_path = output_dir / "cover_letter.md"
        linkedin_message_path = output_dir / "linkedin_message.txt"

        write_text_file(resume_path, resume)
        write_text_file(cover_letter_path, cover_letter)
        write_text_file(linkedin_message_path, linkedin_message)
        tracked_job_id = track_generated_application(args, role)

        print("JobHunterAI finished successfully.")
        print(f"Detected role: {role} ({role_display_name})")
        if args.debug:
            print(f"Job file: {job_path}")
            print(f"Output directory: {output_dir}")
            print(f"Role scores: {scores}")
            print(f"Profile used: {profile_path}")
            if used_fallback:
                print(
                    "Note: role-specific profile was missing/empty. "
                    "Used master profile instead."
                )
        print("Generated files:")
        print(f"- {resume_path}")
        print(f"- {cover_letter_path}")
        print(f"- {linkedin_message_path}")
        if tracked_job_id is not None:
            print(f"Tracked job: #{tracked_job_id}")

    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"JobHunterAI failed.\nError: {error}") from error


if __name__ == "__main__":
    main()

import argparse
from pathlib import Path

from config import OUTPUTS_DIR, ROLE_DISPLAY_NAMES, SAMPLE_JOB_PATH
from file_utils import read_text_file, write_text_file
from generators import (
    generate_cover_letter,
    generate_linkedin_message,
    generate_resume,
)
from profile_selector import select_profile
from role_detector import detect_role, score_roles


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
    return parser.parse_args()


def get_job_path(args: argparse.Namespace) -> Path:
    return args.job_option or args.job_file or SAMPLE_JOB_PATH


def main() -> None:
    args = parse_args()

    try:
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

        resume_path = OUTPUTS_DIR / "resume.md"
        cover_letter_path = OUTPUTS_DIR / "cover_letter.md"
        linkedin_message_path = OUTPUTS_DIR / "linkedin_message.txt"

        write_text_file(resume_path, resume)
        write_text_file(cover_letter_path, cover_letter)
        write_text_file(linkedin_message_path, linkedin_message)

        print("JobHunterAI finished successfully.")
        print(f"Detected role: {role} ({role_display_name})")
        if args.debug:
            print(f"Job file: {job_path}")
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

    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"JobHunterAI failed.\nError: {error}") from error


if __name__ == "__main__":
    main()

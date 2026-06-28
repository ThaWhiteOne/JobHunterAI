from dataclasses import dataclass
from pathlib import Path

from config import OUTPUTS_DIR, SAMPLE_JOB_PATH


DEFAULT_OUTPUT_DIR = OUTPUTS_DIR / "desktop-run"
DEFAULT_ANSWERS_PATH = Path("profiles/application_answers.md")


@dataclass(frozen=True)
class DesktopSettings:
    job_path: Path = SAMPLE_JOB_PATH
    output_dir: Path = DEFAULT_OUTPUT_DIR
    answers_path: Path = DEFAULT_ANSWERS_PATH
    use_ai: bool = False
    use_ai_review: bool = False
    open_browser: bool = False


@dataclass(frozen=True)
class DesktopAction:
    key: str
    label: str
    description: str
    command: list[str]
    category: str
    safe_to_run: bool = True


def command_text(command: list[str]) -> str:
    return " ".join(command)


def pipeline_command(settings: DesktopSettings) -> list[str]:
    command = [
        "pipeline.py",
        "--job",
        str(settings.job_path),
        "--output-dir",
        str(settings.output_dir),
    ]
    if settings.use_ai:
        command.append("--ai")
    if settings.use_ai_review:
        command.append("--ai-review")
    return command


def apply_prep_command(settings: DesktopSettings) -> list[str]:
    command = [
        "apply_prep_pipeline.py",
        "--job",
        str(settings.job_path),
        "--output-dir",
        str(settings.output_dir),
        "--answers",
        str(settings.answers_path),
    ]
    if settings.use_ai:
        command.append("--ai")
    if settings.use_ai_review:
        command.append("--ai-review")
    if settings.open_browser:
        command.append("--open-browser")
    return command


def browser_review_command(settings: DesktopSettings) -> list[str]:
    command = ["browser_review_session.py", str(settings.output_dir), "--write"]
    if settings.open_browser:
        command.append("--open-browser")
    return command


def desktop_actions(settings: DesktopSettings) -> list[DesktopAction]:
    return [
        DesktopAction(
            key="validate_profile",
            label="Validate Profile",
            description="Check profile and template readiness.",
            command=["profile_validator.py", "--write-report"],
            category="Profile",
        ),
        DesktopAction(
            key="package_pipeline",
            label="Generate Package",
            description="Generate and review a complete application package.",
            command=pipeline_command(settings),
            category="Pipeline",
        ),
        DesktopAction(
            key="apply_prep",
            label="Run Apply Prep",
            description="Build the safe apply-prep package and gates.",
            command=apply_prep_command(settings),
            category="Automation",
        ),
        DesktopAction(
            key="browser_review",
            label="Browser Review",
            description="Prepare or open a controlled browser review session.",
            command=browser_review_command(settings),
            category="Automation",
        ),
        DesktopAction(
            key="status_dashboard",
            label="Refresh Status",
            description="Summarize generated package and automation reports.",
            command=["status_dashboard.py", str(settings.output_dir), "--write"],
            category="Dashboard",
        ),
        DesktopAction(
            key="tracker_stats",
            label="Tracker Stats",
            description="Show local job tracker summary counts.",
            command=["tracker.py", "stats"],
            category="Jobs",
        ),
    ]


def actions_by_category(settings: DesktopSettings) -> dict[str, list[DesktopAction]]:
    grouped: dict[str, list[DesktopAction]] = {}
    for action in desktop_actions(settings):
        grouped.setdefault(action.category, []).append(action)
    return grouped

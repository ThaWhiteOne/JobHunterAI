from dataclasses import dataclass
from pathlib import Path

from config import OUTPUTS_DIR, SAMPLE_JOB_PATH


DEFAULT_OUTPUT_DIR = OUTPUTS_DIR / "desktop-run"
DEFAULT_ANSWERS_PATH = Path("profiles/application_answers.md")
PREVIEW_LIMIT = 4000

OUTPUT_ARTIFACTS = [
    ("resume", "Resume", "resume.md"),
    ("cover_letter", "Cover Letter", "cover_letter.md"),
    ("linkedin_message", "LinkedIn Message", "linkedin_message.txt"),
    ("ready_report", "Ready Report", "ready_to_apply_report.md"),
    ("application_packet", "Packet JSON", "application_packet.json"),
    ("submission_plan", "Submission Plan", "submission_plan.md"),
    ("form_fill_plan", "Form Fill Plan", "form_fill_plan.md"),
    ("readiness_report", "Readiness Report", "apply_readiness_report.md"),
    ("browser_dry_run", "Browser Dry Run", "browser_dry_run.md"),
    ("browser_review", "Browser Review", "browser_review_session.md"),
    ("page_inspection", "Page Inspection", "page_inspection.md"),
    ("page_action_plan", "Page Action Plan", "page_action_plan.md"),
    ("page_action_gate", "Action Gate", "page_action_gate_report.md"),
    ("apply_prep", "Apply Prep", "apply_prep_report.md"),
    ("pipeline_report", "Pipeline Report", "pipeline_report.md"),
    ("status_dashboard", "Status Dashboard", "status_dashboard.md"),
]


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


@dataclass(frozen=True)
class OutputArtifactStatus:
    key: str
    label: str
    filename: str
    path: Path
    exists: bool
    modified_at: float | None = None


@dataclass(frozen=True)
class OutputSnapshot:
    output_dir: Path
    artifacts: list[OutputArtifactStatus]
    latest_path: Path | None

    @property
    def generated_count(self) -> int:
        return sum(1 for artifact in self.artifacts if artifact.exists)

    @property
    def total_count(self) -> int:
        return len(self.artifacts)


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


def tracked_output_artifacts(output_dir: Path) -> list[OutputArtifactStatus]:
    artifacts: list[OutputArtifactStatus] = []
    for key, label, filename in OUTPUT_ARTIFACTS:
        path = output_dir / filename
        try:
            stat = path.stat()
        except FileNotFoundError:
            artifacts.append(
                OutputArtifactStatus(
                    key=key,
                    label=label,
                    filename=filename,
                    path=path,
                    exists=False,
                )
            )
        else:
            artifacts.append(
                OutputArtifactStatus(
                    key=key,
                    label=label,
                    filename=filename,
                    path=path,
                    exists=True,
                    modified_at=stat.st_mtime,
                )
            )
    return artifacts


def latest_existing_artifact(artifacts: list[OutputArtifactStatus]) -> Path | None:
    existing = [artifact for artifact in artifacts if artifact.exists]
    if not existing:
        return None
    latest = max(existing, key=lambda artifact: artifact.modified_at or 0)
    return latest.path


def build_output_snapshot(output_dir: Path) -> OutputSnapshot:
    artifacts = tracked_output_artifacts(output_dir)
    return OutputSnapshot(
        output_dir=output_dir,
        artifacts=artifacts,
        latest_path=latest_existing_artifact(artifacts),
    )


def read_preview_text(path: Path | None, max_chars: int = PREVIEW_LIMIT) -> str:
    if path is None:
        return "No generated files yet. Run a workflow to see output here."
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Preview unavailable. File was not found: {path}"
    except OSError as error:
        return f"Preview unavailable: {error}"
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n\n[Preview truncated]"

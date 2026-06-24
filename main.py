from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
JOB_DESCRIPTION_PATH = BASE_DIR / "examples" / "sample_job.txt"
MASTER_PROFILE_PATH = BASE_DIR / "profiles" / "master_profile.md"
TEMPLATE_PATH = BASE_DIR / "templates" / "resume_template.md"
OUTPUT_DIR = BASE_DIR / "outputs"

ROLE_TITLES = {
    "support": "Technical Support / Application Support",
    "developer": "Junior Developer / Python / Web Developer",
    "cybersecurity": "Cybersecurity / SOC Analyst",
}

ROLE_PROFILE_PATHS = {
    "support": BASE_DIR / "profiles" / "support_cv.md",
    "developer": BASE_DIR / "profiles" / "developer_cv.md",
    "cybersecurity": BASE_DIR / "profiles" / "cyber_cv.md",
}

ROLE_KEYWORDS = {
    "support": [
        "technical support",
        "application support",
        "customer support",
        "helpdesk",
        "troubleshooting",
        "ticket",
        "sql",
        "linux",
        "windows",
        "customer",
        "support",
    ],
    "developer": [
        "junior python developer",
        "python developer",
        "web developer",
        "developer",
        "python",
        "api",
        "apis",
        "backend",
        "frontend",
        "web application",
        "web applications",
        "git",
        "github",
        "html",
        "css",
        "javascript",
    ],
    "cybersecurity": [
        "soc analyst",
        "cybersecurity",
        "security events",
        "incident response",
        "siem",
        "vulnerability",
        "security",
        "incident",
        "soc",
        "kali",
        "threat",
    ],
}

ROLE_SUMMARIES = {
    "support": (
        "The job description is closest to technical support because it emphasizes "
        "customer support, troubleshooting, SQL, and technical issue resolution."
    ),
    "developer": (
        "The job description is closest to junior development because it emphasizes "
        "Python, APIs, backend work, Git, and web applications."
    ),
    "cybersecurity": (
        "The job description is closest to cybersecurity because it emphasizes "
        "SOC work, SIEM, incident response, vulnerabilities, and security events."
    ),
}

ROLE_FOCUS = {
    "support": "customer support, troubleshooting, SQL, Linux, Windows, and clear technical communication",
    "developer": "Python, APIs, backend work, Git, web applications, SQL, and automation",
    "cybersecurity": "Linux, networking fundamentals, troubleshooting, Python, virtual machines, and security-focused technical work",
}


def read_required_file(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required file is missing: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Expected a file but found something else: {path}")
    return path.read_text(encoding="utf-8")


def clean_text(text: str) -> str:
    return text.strip()


def remove_duplicate_heading(profile_text: str) -> str:
    lines = profile_text.splitlines()
    if lines and lines[0].strip().startswith("# "):
        return "\n".join(lines[1:]).strip()
    return profile_text


def detect_role(job_description: str) -> tuple[str, dict[str, int], list[str]]:
    text = job_description.lower()
    scores = {}
    matched_keywords = []

    for role, keywords in ROLE_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += text.count(keyword)
                matched_keywords.append(keyword)
        scores[role] = score

    best_role = max(scores, key=scores.get)
    if scores[best_role] == 0:
        raise ValueError(
            "Could not detect a role from the job description. "
            "Add more role-specific keywords to examples/sample_job.txt."
        )

    return best_role, scores, sorted(set(matched_keywords))


def get_profile_text(role: str, master_profile: str) -> tuple[str, Path, bool]:
    profile_path = ROLE_PROFILE_PATHS[role]
    role_profile = clean_text(read_required_file(profile_path))

    if role_profile:
        return role_profile, profile_path, False

    return clean_text(master_profile), MASTER_PROFILE_PATH, True


def render_resume(
    template: str,
    role: str,
    profile_text: str,
    matched_keywords: list[str],
) -> str:
    keyword_text = ", ".join(matched_keywords) if matched_keywords else "Not listed"

    return template.format(
        target_role=ROLE_TITLES[role],
        profile_content=remove_duplicate_heading(profile_text),
        role_summary=ROLE_SUMMARIES[role],
        matched_keywords=keyword_text,
    ).strip() + "\n"


def render_cover_letter(role: str) -> str:
    return f"""Dear Hiring Manager,

I am applying for the {ROLE_TITLES[role]} role. Your job description matches my background in {ROLE_FOCUS[role]}.

My profile includes technical support experience with Sky UK customers, SQL database work, server administration, troubleshooting, Python, Linux, Windows, Git, and AI-assisted automation projects. I am fluent in English and comfortable explaining technical issues clearly to users.

I would welcome the opportunity to discuss how my practical technical background can support your team.

Kind regards,
Nikola Titirinov
"""


def render_linkedin_message(role: str) -> str:
    return f"""Hello,

I saw your {ROLE_TITLES[role]} opportunity and would be glad to connect. My background includes technical support, SQL, Python, troubleshooting, Linux, Windows, and AI-assisted project work.

Best regards,
Nikola Titirinov
"""


def write_output_file(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def main() -> None:
    try:
        job_description = read_required_file(JOB_DESCRIPTION_PATH)
        master_profile = read_required_file(MASTER_PROFILE_PATH)
        resume_template = read_required_file(TEMPLATE_PATH)

        role, scores, matched_keywords = detect_role(job_description)
        profile_text, profile_path, used_fallback = get_profile_text(role, master_profile)

        OUTPUT_DIR.mkdir(exist_ok=True)

        generated_files = [
            write_output_file(
                OUTPUT_DIR / "resume.md",
                render_resume(resume_template, role, profile_text, matched_keywords),
            ),
            write_output_file(
                OUTPUT_DIR / "cover_letter.md",
                render_cover_letter(role),
            ),
            write_output_file(
                OUTPUT_DIR / "linkedin_message.txt",
                render_linkedin_message(role),
            ),
        ]

        print(f"Detected role: {role}")
        print(f"Role scores: {scores}")
        print(f"Selected profile: {profile_path.relative_to(BASE_DIR)}")
        if used_fallback:
            print("Note: selected role profile is empty, so master_profile.md was used.")
        print("Generated files:")
        for path in generated_files:
            print(f"- {path}")

    except (FileNotFoundError, ValueError) as error:
        raise SystemExit(f"Error: {error}") from error


if __name__ == "__main__":
    main()

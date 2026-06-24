from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

EXAMPLES_DIR = BASE_DIR / "examples"
PROFILES_DIR = BASE_DIR / "profiles"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUTS_DIR = BASE_DIR / "outputs"

SAMPLE_JOB_PATH = EXAMPLES_DIR / "sample_job.txt"
MASTER_PROFILE_PATH = PROFILES_DIR / "master_profile.md"
RESUME_TEMPLATE_PATH = TEMPLATES_DIR / "resume_template.md"

ROLE_PROFILE_MAP = {
    "support": PROFILES_DIR / "support_cv.md",
    "developer": PROFILES_DIR / "developer_cv.md",
    "cybersecurity": PROFILES_DIR / "cyber_cv.md",
}

ROLE_DISPLAY_NAMES = {
    "support": "Technical Support / Application Support",
    "developer": "Junior Python / Web Developer",
    "cybersecurity": "Junior Cybersecurity / SOC Analyst",
}

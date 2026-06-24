ROLE_KEYWORDS = {
    "support": [
        "technical support",
        "application support",
        "customer support",
        "service desk",
        "helpdesk",
        "troubleshooting",
        "resolve issues",
        "diagnose",
        "ticket",
        "sql support",
        "support",
        "customer",
        "sql",
    ],
    "developer": [
        "junior python developer",
        "python developer",
        "web developer",
        "developer",
        "python",
        "javascript",
        "html",
        "css",
        "api",
        "apis",
        "backend",
        "frontend",
        "web application",
        "web applications",
        "software",
        "git",
        "code",
        "programming",
    ],
    "cybersecurity": [
        "soc analyst",
        "incident response",
        "security events",
        "cybersecurity",
        "cyber",
        "security",
        "soc",
        "siem",
        "vulnerability",
        "threat",
        "logs",
        "monitoring",
        "malware",
        "phishing",
    ],
}


def score_roles(job_description: str) -> dict[str, int]:
    text = job_description.lower()
    scores = {}

    for role, keywords in ROLE_KEYWORDS.items():
        scores[role] = sum(text.count(keyword) for keyword in keywords)

    return scores


def matched_keywords(job_description: str, role: str) -> list[str]:
    text = job_description.lower()
    return sorted(
        keyword for keyword in ROLE_KEYWORDS.get(role, []) if keyword in text
    )


def detect_role(job_description: str) -> str:
    scores = score_roles(job_description)
    role = max(scores, key=scores.get)

    if scores[role] == 0:
        raise ValueError(
            "Could not detect a role from the job description. "
            "Add more role-specific keywords to examples/sample_job.txt."
        )

    return role

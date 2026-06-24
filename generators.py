from config import RESUME_TEMPLATE_PATH
from file_utils import read_text_file
CONTACT_BLOCK = """Plovdiv, Bulgaria
Email: nikolatitirinov@gmail.com
Phone: +359878555734
GitHub: https://github.com/ThaWhiteOne"""

ROLE_SUMMARIES = {
    "support": (
        "Technical support candidate with experience in customer support, "
        "troubleshooting, SQL databases, Linux/Windows systems, server "
        "administration, and Python automation."
    ),
    "developer": (
        "Junior developer with practical experience in Python, SQL, HTML, CSS, "
        "Git, Linux, automation, database-backed projects, and AI-assisted "
        "development workflows."
    ),
    "cybersecurity": (
        "Junior cybersecurity candidate with practical experience in Linux, "
        "networking fundamentals, Python scripting, SQL, virtual machines, "
        "troubleshooting, and server administration."
    ),
}

ROLE_SKILLS = {
    "support": [
        "Technical Support",
        "Application Support",
        "Troubleshooting",
        "SQL",
        "Linux",
        "Windows",
        "Customer Support",
        "Networking Fundamentals",
        "Server Administration",
        "English Communication",
    ],
    "developer": [
        "Python",
        "SQL",
        "HTML",
        "CSS",
        "Git",
        "GitHub",
        "Linux",
        "Docker",
        "API Integration",
        "Automation",
        "Database Management",
    ],
    "cybersecurity": [
        "Cybersecurity Fundamentals",
        "Linux",
        "Kali Linux",
        "Networking Fundamentals",
        "Python",
        "SQL",
        "Virtual Machines",
        "Troubleshooting",
        "Log Analysis Basics",
        "Server Administration",
    ],
}

ROLE_EXPERIENCE = {
    "support": [
        (
            "Technical Support Representative - Sky UK",
            [
                "Provided technical support to UK customers in English.",
                "Diagnosed broadband, connectivity, and TV service issues.",
                "Guided customers through step-by-step troubleshooting.",
                "Communicated technical solutions clearly to non-technical users.",
            ],
        ),
        (
            "Community Server Administrator",
            [
                "Managed server databases and player information.",
                "Configured and maintained plugins.",
                "Performed server troubleshooting and technical maintenance.",
                "Worked with SQL databases and server-side systems.",
            ],
        ),
    ],
    "developer": [
        (
            "Community Server Administrator / Developer",
            [
                "Managed CS2 community server databases and player information.",
                "Worked with SQL databases, server configuration, and plugins.",
                "Performed troubleshooting and technical maintenance.",
                "Built and modified technical systems used by online communities.",
            ],
        ),
        (
            "AI / Automation Projects",
            [
                "Built JobHunterAI, a Python project for tailored job application documents.",
                "Worked with AI-assisted development workflows.",
                "Created proof-of-concept pipelines and structured project documentation.",
            ],
        ),
    ],
    "cybersecurity": [
        (
            "Technical Support Representative - Sky UK",
            [
                "Provided technical support to UK customers in English.",
                "Diagnosed connectivity and service issues.",
                "Followed troubleshooting procedures and communicated clearly with users.",
                "Built strong problem-solving and customer communication skills.",
            ],
        ),
        (
            "Cybersecurity Learning / Home Lab",
            [
                "Practiced Linux and virtual machine workflows.",
                "Worked with security-oriented tools and environments.",
                "Studied networking, vulnerability research, and defensive security concepts.",
            ],
        ),
    ],
}

ROLE_PROJECTS = {
    "support": [
        "JobHunterAI",
        "SQL Player Database",
        "Python Automation Toolkit",
        "Surgical AI Demo",
    ],
    "developer": [
        "JobHunterAI",
        "SQL Player Database",
        "Python Automation Toolkit",
        "Surgical AI Demo",
    ],
    "cybersecurity": [
        "JobHunterAI",
        "SQL Player Database",
        "Python Automation Toolkit",
        "Cybersecurity Home Lab",
    ],
}

ROLE_COVER_LETTERS = {
    "support": (
        "My background includes English-speaking technical support, troubleshooting, "
        "SQL, Linux/Windows systems, server administration, and Python automation."
    ),
    "developer": (
        "My background includes Python, SQL, Git, Linux, automation, web projects, "
        "database-backed tools, and AI-assisted development workflows."
    ),
    "cybersecurity": (
        "My background includes Linux, networking fundamentals, Python scripting, "
        "SQL, virtual machines, server administration, and technical troubleshooting."
    ),
}

ROLE_COVER_DETAILS = {
    "support": (
        "In my previous support experience, I worked with UK customers, diagnosed "
        "connectivity and service issues, and explained technical steps clearly to "
        "non-technical users. I also maintain technical projects involving "
        "databases, automation, and server-side systems."
    ),
    "developer": (
        "My projects include JobHunterAI, SQL database work, automation scripts, "
        "and AI-assisted development workflows. I am comfortable learning quickly, "
        "organizing code clearly, and solving technical problems step by step."
    ),
    "cybersecurity": (
        "My technical background combines support troubleshooting, Linux, "
        "networking fundamentals, virtual machines, SQL, and Python scripting. "
        "I am especially interested in SOC analysis, incident response, and "
        "defensive security."
    ),
}

ROLE_LINKEDIN_MESSAGES = {
    "support": (
        "My background includes English-speaking technical support, SQL, "
        "Linux/Windows troubleshooting, server administration, and Python automation."
    ),
    "developer": (
        "My background includes Python, SQL, Git, Linux, automation, and "
        "AI-assisted development projects."
    ),
    "cybersecurity": (
        "My background includes Linux, networking fundamentals, Python scripting, "
        "SQL, virtual machines, and technical troubleshooting."
    ),
}


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def experience_sections(role: str) -> str:
    sections = []
    for title, bullets in ROLE_EXPERIENCE[role]:
        sections.append(f"### {title}\n\n{bullet_list(bullets)}")
    return "\n\n".join(sections)


def generate_resume(
    role: str,
    role_display_name: str,
    profile: str,
    job_description: str,
) -> str:
    template = read_text_file(RESUME_TEMPLATE_PATH, required=True)
    return template.format(
        contact_block=CONTACT_BLOCK,
        target_role=role_display_name,
        professional_summary=ROLE_SUMMARIES[role],
        core_skills=bullet_list(ROLE_SKILLS[role]),
        relevant_experience=experience_sections(role),
        selected_projects=bullet_list(ROLE_PROJECTS[role]),
    )


def generate_cover_letter(
    role: str,
    role_display_name: str,
    profile: str,
    job_description: str,
) -> str:
    return f"""Dear Hiring Manager,

I am interested in the {role_display_name} position. {ROLE_COVER_LETTERS[role]}

{ROLE_COVER_DETAILS[role]}

I would be glad to discuss how my technical background and communication skills can support your team.

Kind regards,
Nikola Titirinov
"""


def generate_linkedin_message(role: str, role_display_name: str) -> str:
    return f"""Hello,

I came across your {role_display_name} opportunity and would like to connect. {ROLE_LINKEDIN_MESSAGES[role]}

Best regards,
Nikola Titirinov
"""

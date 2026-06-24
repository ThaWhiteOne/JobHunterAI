from pathlib import Path

print("JobHunterAI")
print("Generating files...")

output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

resume = """
# Nikola Titirinov

## Technical Skills

Python
SQL
Linux
Windows

## Experience

Sky UK Technical Support
Community Server Administration
AI Projects
"""

cover_letter = """
Dear Hiring Manager,

I am interested in this position and believe my experience in technical support, SQL, Python and troubleshooting makes me a strong candidate.

Kind regards,

Nikola Titirinov
"""

linkedin_message = """
Hello,

I came across your opportunity and would love to connect and discuss it further.

Best regards,
Nikola Titirinov
"""

(output_dir / "resume.md").write_text(resume)
(output_dir / "cover_letter.md").write_text(cover_letter)
(output_dir / "linkedin_message.txt").write_text(linkedin_message)

print("Done.")
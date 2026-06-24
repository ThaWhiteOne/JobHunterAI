# JobHunterAI

JobHunterAI is an offline Python tool that reads a job description, detects the closest role category, and generates tailored application files.

It is built as both a practical job-search assistant and a clean junior portfolio project.

## Features

- Reads `examples/sample_job.txt`
- Detects the target role with keyword scoring
- Selects the matching candidate profile
- Generates a tailored resume, cover letter, and LinkedIn message
- Works offline without OpenAI API calls or external services

## Supported Roles

- Technical Support / Application Support
- Junior Python / Web Developer
- Junior Cybersecurity / SOC Analyst

## Usage

```bash
python main.py
```

Use a custom job description file:

```bash
python main.py examples/sample_job.txt
python main.py --job examples/sample_job.txt
```

Print role scores and profile selection details:

```bash
python main.py --debug
```

Generated files are written to `outputs/`:

- `outputs/resume.md`
- `outputs/cover_letter.md`
- `outputs/linkedin_message.txt`

The `outputs/` folder is ignored by Git because the files are generated.

## Project Structure

```text
main.py
config.py
file_utils.py
role_detector.py
profile_selector.py
generators.py
README.md
requirements.txt
.gitignore
examples/sample_job.txt
profiles/master_profile.md
profiles/support_cv.md
profiles/developer_cv.md
profiles/cyber_cv.md
templates/resume_template.md
tests/test_role_detector.py
outputs/
```

## Manual Tests

Put one of these examples into `examples/sample_job.txt`, then run:

```bash
python main.py
```

Support example:

```text
Technical Support Engineer, SQL, troubleshooting, customer support
```

Expected role: `support`

Developer example:

```text
Junior Python Developer, APIs, backend, Git, web applications
```

Expected role: `developer`

Cybersecurity example:

```text
Junior SOC Analyst, SIEM, incident response, vulnerability, security events
```

Expected role: `cybersecurity`

Run the automated role detection tests:

```bash
python -m unittest
```

## Current Limitations

- Uses simple keyword scoring instead of AI.
- Reads one job description file per run.
- Generates Markdown/text files only.
- Does not track job applications yet.

## Roadmap

- Add a SQLite job tracker
- Add DOCX/PDF export
- Add optional AI mode later while keeping offline mode

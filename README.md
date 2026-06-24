# JobHunterAI

JobHunterAI is an offline Python tool that reads a job description, detects the closest role category, and generates tailored application files.

It is built as both a practical job-search assistant and a clean junior portfolio project.

## Features

- Reads `examples/sample_job.txt`
- Detects the target role with keyword scoring
- Selects the matching candidate profile
- Generates a tailored resume, cover letter, and LinkedIn message
- Tracks job applications with a local SQLite database
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

Generate files and save the application in the tracker:

```bash
python main.py --job examples/sample_job.txt --track --company "Example Ltd" --position "Support Engineer" --url "https://example.com/job"
```

Generated files are written to `outputs/`:

- `outputs/resume.md`
- `outputs/cover_letter.md`
- `outputs/linkedin_message.txt`

The `outputs/` folder is ignored by Git because the files are generated.

## Job Tracker

Add a tracked job:

```bash
python tracker.py add --company "Example Ltd" --position "Support Engineer" --url "https://example.com/job" --role support
```

List tracked jobs:

```bash
python tracker.py list
```

Update a job status:

```bash
python tracker.py update --id 1 --status applied
```

Supported statuses are:

```text
saved, generated, applied, interview, rejected, offer
```

The tracker stores data in `job_tracker.db`, which is ignored by Git.

## Project Structure

```text
main.py
tracker.py
config.py
file_utils.py
role_detector.py
profile_selector.py
generators.py
tracker_db.py
README.md
requirements.txt
.gitignore
examples/sample_job.txt
profiles/master_profile.md
profiles/support_cv.md
profiles/developer_cv.md
profiles/cyber_cv.md
templates/resume_template.md
tests/
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

Run the automated tests:

```bash
python -m unittest
```

The tests cover role detection, profile fallback behavior, basic document generation, generator-to-tracker integration, and job tracker database operations.

## Current Limitations

- Uses simple keyword scoring instead of AI.
- Reads one job description file per run.
- Generates Markdown/text files only.
- Job tracker is local-only and uses SQLite.

## Roadmap

- Add DOCX/PDF export
- Add optional AI mode later while keeping offline mode

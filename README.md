# JobHunterAI

JobHunterAI is an offline Python tool that reads a job description, detects the closest role category, and generates tailored application files.

It is built as both a practical job-search assistant and a clean junior portfolio project.

## Features

- Reads `examples/sample_job.txt`
- Detects the target role with keyword scoring
- Selects the matching candidate profile
- Generates a tailored resume, cover letter, and LinkedIn message
- Can generate a full offline application package with one command
- Optionally exports generated documents to simple HTML files
- Optionally creates review notes with matched keywords and a pre-apply checklist
- Optionally prepares an offline AI brief for future tailoring
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

Write generated files to a custom folder:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer
```

Generate the full offline package for a real application draft:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --full-package
```

Save the original job description beside the generated files:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --save-job-text
```

Export browser-friendly HTML copies:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --export html
```

Create application review notes before sending:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --review-notes
```

Prepare an offline AI brief for a future AI/automation step:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --ai-brief
```

Generate files and save the application in the tracker:

```bash
python main.py --job examples/sample_job.txt --track --company "Example Ltd" --position "Support Engineer" --url "https://example.com/job"
```

When `--track` is used without `--output-dir`, JobHunterAI creates a folder name from the company and position, such as `outputs/example-ltd-support-engineer`.

By default, generated files are written to `outputs/`:

- `outputs/resume.md`
- `outputs/cover_letter.md`
- `outputs/linkedin_message.txt`

When `--full-package` is used, JobHunterAI also writes the original job description, review notes, AI brief, and HTML copies.

When `--save-job-text` is used, JobHunterAI also writes `job_description.txt` to the same output folder.

When `--export html` is used, JobHunterAI also writes:

- `outputs/resume.html`
- `outputs/cover_letter.html`
- `outputs/linkedin_message.html`

When `--review-notes` is used, JobHunterAI also writes `application_review.md` with detected role details, matched keywords, extracted requirement lines, and a checklist.

When `--ai-brief` is used, JobHunterAI also writes `ai_brief.md` with the job description, selected profile, generated drafts, matched keywords, and strict AI guardrails. This file is only a preparation artifact; it does not call an AI API.

The `outputs/` folder is ignored by Git because the files are generated.

## Job Tracker

Add a tracked job:

```bash
python tracker.py add --company "Example Ltd" --position "Support Engineer" --url "https://example.com/job" --role support --output-dir outputs/example-ltd-support-engineer
```

List tracked jobs:

```bash
python tracker.py list
```

List tracked jobs by status:

```bash
python tracker.py list --status applied
```

List tracked jobs by role:

```bash
python tracker.py list --role support
```

Combine filters:

```bash
python tracker.py list --status applied --role developer
```

Show tracker summary counts:

```bash
python tracker.py stats
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

Use a different tracker database:

```bash
set JOBHUNTERAI_DB_PATH=C:\path\to\jobs.db
python tracker.py list
```

## Project Structure

```text
main.py
tracker.py
ai_prompt_builder.py
config.py
file_utils.py
role_detector.py
profile_selector.py
generators.py
html_exporter.py
job_analyzer.py
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

The tests cover role detection, job analysis, AI brief generation, profile fallback behavior, basic document generation, HTML export, generator-to-tracker integration, job tracker database operations, saved job text, and basic CLI commands.
The full package command is also covered by the automated tests.

## Current Limitations

- Uses simple keyword scoring instead of AI.
- Reads one job description file per run.
- Generates Markdown, text, and simple HTML files only.
- AI brief generation is offline and does not call an API yet.
- Job tracker is local-only and uses SQLite.

## Roadmap

- Add DOCX/PDF export
- Add optional AI mode later while keeping offline mode
- Add an automation/AI unit after the offline workflow is reliable

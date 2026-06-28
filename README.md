# JobHunterAI

JobHunterAI is an offline Python tool that reads a job description, detects the closest role category, and generates tailored application files.

It is built as both a practical job-search assistant and a clean junior portfolio project.

## Features

- Reads `examples/sample_job.txt`
- Detects the target role with keyword scoring
- Selects the matching candidate profile
- Generates a tailored resume, cover letter, and LinkedIn message
- Can generate a full offline application package with one command
- Optionally uses AI to generate stronger tailored drafts from the selected profile
- Optionally uses AI to automatically revise drafts before files are written
- Validates profile and template source files before automation
- Saves copied job descriptions into a local job inbox
- Runs the safe generation/check/review workflow with one pipeline command
- Runs the safe pipeline for multiple job description files in a batch
- Creates a final ready-to-apply report for generated packages
- Creates a structured application packet for future automation handoff
- Creates a non-submitting submission plan for the final apply step
- Opens a controlled apply session without filling forms or submitting
- Creates a safe form-fill plan for future browser automation
- Reuses local application answers from an ignored profile file when available
- Optionally exports generated documents to simple HTML, DOCX, and PDF files
- Optionally creates review notes with matched keywords and a pre-apply checklist
- Optionally prepares an offline AI brief for future tailoring
- Optionally writes a JSON manifest for future automation handoff
- Includes a safe Automation Unit checker for generated manifests
- Includes an offline Recruiter Review Agent for draft quality checks
- Optionally runs an AI recruiter review when explicitly requested
- Tracks job applications with a local SQLite database
- Works offline by default without OpenAI API calls or external services

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

Check whether profile/template source files are ready for automation:

```bash
python profile_validator.py --write-report
```

Create a one-time profile cleanup guide:

```bash
python profile_validator.py --write-report --write-guide
```

Save a copied job description into the local job inbox:

```bash
python job_intake.py add --company "Example Ltd" --position "Support Engineer" --url "https://example.com/job" --text "Paste the job description here"
```

List saved job descriptions:

```bash
python job_intake.py list
```

Run the offline package pipeline with one command:

```bash
python pipeline.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer
```

Run the AI draft pipeline with automatic revision:

```bash
python pipeline.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --ai
```

Run the pipeline for every `.txt` job description in a folder:

```bash
python batch_pipeline.py --jobs-dir jobs --output-root outputs/batch
```

Run the batch pipeline with AI drafts and automatic revision:

```bash
python batch_pipeline.py --jobs-dir jobs --output-root outputs/batch --ai
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

Export Word documents:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --export docx
```

Export PDF files:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --export pdf
```

Export all supported formats:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --export all
```

Create application review notes before sending:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --review-notes
```

Prepare an offline AI brief for a future AI/automation step:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --ai-brief
```

Generate the drafts with AI using the selected profile as the source of truth:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --full-package --ai-drafts
```

Generate AI drafts and automatically revise them before writing final files:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --full-package --ai-drafts --ai-auto-revise
```

Create a machine-readable application manifest:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --manifest
```

Check a generated package with the safe Automation Unit:

```bash
python automation_unit.py check outputs/example-ltd-support-engineer/application_manifest.json
```

Write the Automation Unit check as a report file:

```bash
python automation_unit.py check outputs/example-ltd-support-engineer/application_manifest.json --write-report
```

Check whether a generated package is ready for the final apply step:

```bash
python readiness_checker.py outputs/example-ltd-support-engineer --write-report
```

Build a structured handoff packet for future apply automation:

```bash
python application_packet.py outputs/example-ltd-support-engineer --write
```

Build a non-submitting submission plan from the handoff packet:

```bash
python submission_planner.py outputs/example-ltd-support-engineer --write
```

Prepare a controlled browser apply session:

```bash
python apply_assistant.py outputs/example-ltd-support-engineer --write
```

Create a safe form-fill plan for future browser automation:

```bash
python form_fill_planner.py outputs/example-ltd-support-engineer --write
```

Use a local application answers file for repeated form answers:

```bash
copy profiles\application_answers.example.md profiles\application_answers.md
python form_fill_planner.py outputs/example-ltd-support-engineer --write
```

Open the job URL from the packet in your default browser:

```bash
python apply_assistant.py outputs/example-ltd-support-engineer --write --open-browser
```

Review generated drafts like a recruiter:

```bash
python automation_unit.py review outputs/example-ltd-support-engineer/application_manifest.json --write-report
```

Optionally run an AI recruiter review after the offline review:

```bash
python automation_unit.py review outputs/example-ltd-support-engineer/application_manifest.json --write-report --ai-review
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

When `--full-package` is used, JobHunterAI also writes the original job description, review notes, AI brief, manifest, and HTML/DOCX/PDF copies.

When `--save-job-text` is used, JobHunterAI also writes `job_description.txt` to the same output folder.

When `--export html` is used, JobHunterAI also writes:

- `outputs/resume.html`
- `outputs/cover_letter.html`
- `outputs/linkedin_message.html`

When `--export docx` is used, JobHunterAI also writes:

- `outputs/resume.docx`
- `outputs/cover_letter.docx`

When `--export pdf` is used, JobHunterAI also writes:

- `outputs/resume.pdf`
- `outputs/cover_letter.pdf`

Use `--export all` to write HTML copies for all generated documents plus DOCX/PDF copies for the resume and cover letter.

When `--review-notes` is used, JobHunterAI also writes `application_review.md` with detected role details, matched keywords, extracted requirement lines, and a checklist.

When `--ai-brief` is used, JobHunterAI also writes `ai_brief.md` with the job description, selected profile, generated drafts, matched keywords, and strict AI guardrails. This file is only a preparation artifact; it does not call an AI API.

When `--ai-drafts` is used, JobHunterAI asks OpenAI to generate `resume.md`, `cover_letter.md`, and `linkedin_message.txt` from the selected profile, job description, and template guidance. It is designed for the future fully automated workflow: update the profile/template once, then let the tool generate job-specific drafts without per-application editing.

When `--ai-auto-revise` is used, JobHunterAI sends the generated drafts through a second AI recruiter/editor pass before writing the final files. It also writes `ai_revision_notes.md` so you can see what the automated revision changed.

`profile_validator.py` checks the master profile, role profiles, and resume template before automation. Missing files or required sections are errors. Placeholder-style text and missing dates are warnings so you can improve the source data once and reuse it safely.

Use `profile_validator.py --write-guide` to create `outputs/profile_improvement_guide.md`, a checklist for adding truthful dates, project context, real links, and source-backed details without inventing experience.

The AI draft and revision prompts explicitly tell the model to avoid generic filler, avoid implying paid work unless the profile says it was paid, use plain ASCII punctuation, and prefer specific evidence from the profile.

`job_intake.py` saves copied job descriptions into the ignored `jobs/` folder and updates `jobs/job_index.json`. It does not scrape job boards or submit applications.

`pipeline.py` runs profile validation, full package generation, the Automation Unit check, recruiter review, readiness check, application packet builder, and submission planner in order. It writes `pipeline_report.md` in the selected output folder. It does not submit applications.

`readiness_checker.py` reads a generated output folder or manifest and writes `ready_to_apply_report.md`. It checks required package files, manifest consistency, offline recruiter review score, warnings, optional AI review files, and tracker linkage. It does not submit applications.

`application_packet.py` writes `application_packet.json`, a structured handoff containing readiness status, job metadata, selected files, reports, and automation guardrails. The packet marks `automation_allowed` as `false`; it does not submit applications.

`submission_planner.py` reads `application_packet.json` and writes `submission_plan.md`, a human-readable apply sequence with job metadata, file paths, readiness status, warnings, and guardrails. It does not submit applications.

`apply_assistant.py` reads `application_packet.json`, checks that the package is ready, optionally opens the job URL in the default browser, and writes `apply_session.md`. It does not fill forms, click apply, or submit applications.

`form_fill_planner.py` reads `application_packet.json`, `profiles/master_profile.md`, and optional `profiles/application_answers.md`, then writes `form_fill_plan.json` and `form_fill_plan.md`. The plan includes safe contact fields, preferred document uploads, reusable application answers, review-only fields, and guardrails. It does not fill forms or submit applications.

`profiles/application_answers.example.md` is a tracked template. Copy it to `profiles/application_answers.md` and fill in truthful reusable answers such as work authorization, visa sponsorship, start date, and salary expectation. `profiles/application_answers.md` is ignored by Git.

`batch_pipeline.py` runs `pipeline.py` for every `.txt` job description in a folder. It creates one output folder per job and writes `batch_report.md` in the batch output root. It continues after failed jobs by default, or stops early with `--stop-on-error`.

The local `jobs/` folder is ignored by Git so real job descriptions are not committed.

When `--manifest` is used, JobHunterAI also writes `application_manifest.json` with detected role details, generated file paths, matched keywords, tracker ID if available, and automation guardrails.

`automation_unit.py check` reads `application_manifest.json`, confirms expected files exist, prints the detected role, and repeats the guardrails. It does not submit applications or call external APIs.

When `--write-report` is used, the Automation Unit also writes `automation_report.md` beside the manifest.

`automation_unit.py review` reads the generated resume, cover letter, and LinkedIn message from the manifest, then writes recruiter-style feedback. It checks for placeholders, missing files, weak length signals, keyword alignment, and claims that need manual verification. It does not submit applications or call an AI API.

`automation_unit.py review --ai-review` keeps the offline review first, then optionally calls OpenAI for a second recruiter-style review. If `OPENAI_API_KEY` is missing, the AI review is skipped and the offline review still completes.

To enable optional AI review, create a local `.env` file:

```text
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4.1
```

`.env` is ignored by Git. You can also set `OPENAI_API_KEY` and `OPENAI_MODEL` as environment variables instead.

The `outputs/` folder is ignored by Git because the files are generated.

## Recommended Workflow

For a real application draft:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --full-package
```

For an AI-generated application draft:

```bash
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --full-package --ai-drafts
```

For the most automated draft flow:

```bash
python profile_validator.py --write-report
python main.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --full-package --ai-drafts --ai-auto-revise
```

Or run the same safe package flow through the pipeline:

```bash
python pipeline.py --job examples/sample_job.txt --output-dir outputs/example-ltd-support-engineer --ai
```

For multiple saved job descriptions:

```bash
python job_intake.py add --company "Example Ltd" --position "Support Engineer" --text "Paste the job description here"
python batch_pipeline.py --jobs-dir jobs --output-root outputs/batch --ai
```

Review these files before applying:

- `resume.md` or `resume.docx`
- `cover_letter.md` or `cover_letter.docx`
- `linkedin_message.txt`
- `application_review.md`
- `ai_brief.md`
- `ai_revision_notes.md` when `--ai-auto-revise` is used
- `profile_improvement_guide.md` when `--write-guide` is used
- `ready_to_apply_report.md`
- `application_packet.json`
- `submission_plan.md`
- `apply_session.md` when `apply_assistant.py --write` is used
- `form_fill_plan.json` and `form_fill_plan.md` when `form_fill_planner.py --write` is used
- `pipeline_report.md` when `pipeline.py` is used
- `batch_report.md` when `batch_pipeline.py` is used

Then run the safe Automation Unit check:

```bash
python automation_unit.py check outputs/example-ltd-support-engineer/application_manifest.json --write-report
```

Then run the Recruiter Review Agent:

```bash
python automation_unit.py review outputs/example-ltd-support-engineer/application_manifest.json --write-report
```

Then run the readiness gate:

```bash
python readiness_checker.py outputs/example-ltd-support-engineer --write-report
```

Then build the structured application packet:

```bash
python application_packet.py outputs/example-ltd-support-engineer --write
```

Then build the final submission plan:

```bash
python submission_planner.py outputs/example-ltd-support-engineer --write
```

Then prepare the controlled apply session:

```bash
python apply_assistant.py outputs/example-ltd-support-engineer --write --open-browser
```

Then create the safe form-fill plan:

```bash
python form_fill_planner.py outputs/example-ltd-support-engineer --write
```

For reusable application form answers, first create the local ignored answers file:

```bash
copy profiles\application_answers.example.md profiles\application_answers.md
```

Optional AI recruiter check:

```bash
python automation_unit.py review outputs/example-ltd-support-engineer/application_manifest.json --write-report --ai-review
```

After reviewing the generated drafts, `automation_report.md`, `recruiter_review.md`, and optional `ai_recruiter_review.md`, apply manually through the job site or recruiter message.

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
automation_unit.py
profile_validator.py
job_intake.py
pipeline.py
batch_pipeline.py
readiness_checker.py
application_packet.py
submission_planner.py
apply_assistant.py
form_fill_planner.py
ai_draft_generator.py
ai_draft_reviser.py
ai_reviewer.py
ai_prompt_builder.py
config.py
file_utils.py
role_detector.py
profile_selector.py
generators.py
document_exporter.py
draft_reviewer.py
html_exporter.py
job_analyzer.py
manifest_builder.py
tracker_db.py
README.md
requirements.txt
.gitignore
examples/sample_job.txt
profiles/master_profile.md
profiles/application_answers.example.md
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

The tests cover role detection, job intake, profile validation and profile improvement guidance, single-job and batch pipeline orchestration, readiness checking, application packet generation, submission planning, controlled apply session setup, safe form-fill planning, job analysis, AI brief generation, AI draft parsing/revision, manifest generation, Automation Unit checks/reports, recruiter-style draft review, profile fallback behavior, basic document generation, HTML/DOCX/PDF export, generator-to-tracker integration, job tracker database operations, saved job text, and basic CLI commands.
AI draft/revision/reviewer tests use mocks and do not call the OpenAI API.
The full package command is also covered by the automated tests.

## Current Limitations

- Uses simple keyword scoring for role detection.
- `main.py` and `pipeline.py` read one job description per run; `batch_pipeline.py` handles a folder of saved `.txt` job descriptions.
- Job intake currently saves manually copied job descriptions; automated search/import is still future work.
- Profile validation warns about missing dates, but the user still needs to add truthful dates to profile files.
- The profile improvement guide suggests what to add, but it does not edit profile facts automatically.
- Reusable application answers are optional and must be filled truthfully in local `profiles/application_answers.md`.
- DOCX/PDF exports are simple offline documents for the resume and cover letter, not custom-designed templates.
- AI brief generation is offline. Optional AI draft generation, automatic revision, and recruiter review only run when requested.
- Manifest generation prepares automation handoff data but does not submit applications.
- Pipeline, readiness checker, application packet builder, submission planner, apply assistant, form-fill planner, and Automation Unit currently validate packages and write reports only; they do not apply to jobs.
- Apply assistant can open the job URL in a browser, but it does not fill forms or submit applications.
- Form-fill planner prepares field mappings, but it does not interact with web pages.
- Recruiter Review Agent is offline/rule-based by default; optional AI mode can add a second review pass.
- Job tracker is local-only and uses SQLite.

## Roadmap

- Improve DOCX/PDF styling templates
- Refine optional AI review prompts with real application feedback
- Add controlled browser/job-site automation with explicit user approval gates
- Add controlled job search/import flows that save job descriptions into batch input folders

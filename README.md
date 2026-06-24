# JobHunterAI

JobHunterAI is a small Python portfolio project that reads a job description, detects the closest role category, and generates tailored application files.

## Role Categories

- Technical Support / Application Support
- Junior Developer / Python / Web Developer
- Cybersecurity / SOC Analyst

## How It Works

1. Reads `examples/sample_job.txt`
2. Scores role keywords in the job description
3. Selects the matching profile from `profiles/`
4. Generates files in `outputs/`

The project currently runs locally without OpenAI API calls or external services.

## Usage

```bash
python main.py
```

## Generated Files

Running the script creates:

- `outputs/resume.md`
- `outputs/cover_letter.md`
- `outputs/linkedin_message.txt`

## Project Structure

```text
main.py
README.md
requirements.txt
.gitignore
examples/sample_job.txt
profiles/master_profile.md
profiles/support_cv.md
profiles/developer_cv.md
profiles/cyber_cv.md
templates/resume_template.md
outputs/
```

# halo-platform-qa
This repository is part of the Halo Cognitive Assistant Platform.
Scope and mapping to SRS / SAD / RTM are defined in the DEV - Development Baseline & Workflow document.

## CI evidence pack (security & privacy)
A CI-generated evidence pack is produced by GitHub Actions workflow "QA Assess Evidence Pack" (runs-on: windows-latest).
The artifact name is "qa_assess_evidence" and contains machine- and audit-friendly outputs under artifacts/qa_assess:

- security-assessment.md
- privacy-assessment.md
- bandit.json
- detect_secrets.json
- pip_audit.clean.json
- pip_audit.summary.txt
- links.json

### Run from CLI (GitHub Actions)
Trigger (manual):
  gh -R halo-plat/halo-platform-qa workflow run "QA Assess Evidence Pack" --ref main

Find latest run:
  gh -R halo-plat/halo-platform-qa run list --workflow="qa-assess.yml" --branch main --limit 5

Download artifact:
  gh -R halo-plat/halo-platform-qa run download <RUN_ID> -n qa_assess_evidence -D artifacts/ci_download/qa_assess_evidence

### Run locally (Win11)
Generate the same pack locally:
  python tools/qa_assess.py . artifacts/qa_assess artifacts/qa_assess/security-assessment.md artifacts/qa_assess/privacy-assessment.md artifacts/qa_assess/links.json

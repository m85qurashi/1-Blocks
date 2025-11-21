# Pilot Evidence Folder

- `qa/` — reliability soak logs, mutation reports, CI artifacts (template: `qa/template_metrics.md`). Store raw exports, screenshots, and link dashboards.
- `biz/` — ROI calculations, cost vs baseline analysis, stakeholder feedback (template: `biz/roi_template.md`). Attach spreadsheets or PDF summaries as needed.

Usage instructions:
1. After each Basel-I run, copy CI reports into `qa/` with naming `run-YYYYMMDD.md` and reference metrics template.
2. Update ROI template with actual numbers and cite supporting data (e.g., token dashboard screenshot) per row.
3. Link evidence in gate deck and update `planning/approvals/G5_signoff.md` with file references.

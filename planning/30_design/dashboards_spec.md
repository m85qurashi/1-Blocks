# Dashboard Specification

Sourced from Data measurement plan.

1. **Pilot ROI Dashboard:** Cycle time, AI contribution %, token spend vs budget.
2. **Quality Dashboard:** BLOCKERS/WARNINGS trends, mutation kill-rate, defects.
3. **Reliability Dashboard:** flow success, P50/P95 latency, retries.
4. **Adoption Dashboard:** active repos, flows/day, catalog growth.

All dashboards must ingest TaskEvent, FlowMetric, BlockVerification streams. Ownership: Data + Biz.

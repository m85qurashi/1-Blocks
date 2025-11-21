# User Acceptance Testing (UAT) Plan — Multi-LLM Orchestrator + Verified Blocks

## 1. Objectives
- Validate end-to-end plan→impl→review→docs flows across representative repositories.
- Confirm quality gates (contract, coverage, mutation, security, LLM review) enforce thresholds.
- Measure productivity, quality, and cost metrics in near-production conditions (Phase 6 soak).
- Capture user feedback on CLI/CI experience and onboarding friction.

## 2. Scope
- **Participants:** 10 pilot repositories (Phase 6 cohort) covering compliance, security, testing, deployment, monitoring.
- **Environment:** FlowEngine v1.3 in production namespace (minikube or target cluster).
- **Components under test:** FlowEngine APIs, CLI, quality gates, LLM review gate (Claude), TaskDB, evidence logging.

## 3. Entry Criteria
- FlowEngine v1.3 deployed and healthy (`kubectl get pods -n production`).
- API secrets configured (Anthropic, OpenAI, Gemini placeholders).
- 5 quality gates operational (contract, coverage ≥80%, mutation ≥70%, security pass, LLM review ≥65%).
- Pilot repos onboarded (RB-LAUNCH-001) and developers have CLI access.

## 4. Test Scenarios
| ID | Scenario | Repos | Steps | Expected Result |
| --- | --- | --- | --- | --- |
| UAT-01 | Compliance block generation | compliance-repo-4/5 | Run full flow via CLI (`blocks generate ...`) | Flow succeeds, contract/security/LLM gates pass, coverage/mutation block until tests added |
| UAT-02 | Security analysis block | security-repo-4/5 | Run flow, inspect Semgrep findings | Security gate pass/fail recorded, LLM review score logged |
| UAT-03 | Test automation block | test-repo-4/5 | Flow with missing tests | Coverage/mutation gates fail, flow marked unsuccessful |
| UAT-04 | Deployment automation | deploy-repo-4/5 | Flow with adequate tests | All gates pass, flow recorded as success |
| UAT-05 | Monitoring blueprint | monitor-repo-4/5 | Flow across 3 gates + LLM review | Gate metrics stored, cost recorded |

## 5. Success Criteria
- ≥80% of flows enforce gates correctly (blocking when thresholds unmet).
- ≥2 successful flows per workflow family after remedial actions.
- Cost/flow ≤ $0.10; average duration ≤ 2 minutes.
- User feedback: majority report manageable onboarding and CLI use.

## 6. Data Collection
- Metrics logged in `MVP_METRICS_LOG.md` (date, repo, flows, success %, cost, notes).
- Detailed gate outcomes stored in PostgreSQL (`flows`, `flow_metrics` tables).
- Qualitative feedback captured via shared doc or Slack `#orchestrator-launch`.
- Issues tracked in git/SRE backlog.

## 7. Exit Criteria
- Minimum 20 flows executed (combined Batch 1 + Batch 2 already ≥49).
- Evidence folder `evidence/phase1_quality_gates/` updated with batch results.
- Outstanding defects triaged and assigned.
- Go/No-Go recommendation prepared for G6 gate (Dec 5).

## 8. Schedule
- Nov 16–24: Execute UAT scenarios, log metrics, gather feedback.
- Nov 25–30: Address issues, rerun failed scenarios, finalize evidence.
- Dec 1–4: Compile report for G6 review.

## 9. Roles
| Role | Responsibilities |
| --- | --- |
| PM/Product Persona | Coordinate UAT schedule, collect feedback |
| Engineering Persona | Support FlowEngine/CLI issues |
| QA Persona | Monitor gate metrics, analyze failures |
| Data Persona | Extract metrics/dashboards |
| SRE Persona | Monitor infrastructure, respond to incidents |
| Pilot Repo Owners | Execute flows, provide feedback |

## 10. Reporting
- Daily update in `#orchestrator-launch` channel (flows run, issues, next steps).
- Final UAT summary delivered with G6 evidence package.

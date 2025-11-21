# Business Requirements Document (BRD)
## Initiative
Multi-LLM Orchestrator + Verified Blocks Platform (Delivery Plans A, B, C)

## 1. Executive Summary
Develop a governed, multi-model orchestration platform (Delivery A) and a 6-face verified Blocks system (Delivery B) connected through a lightweight integration layer (Delivery C) to reduce idea-to-verified-block cycle time by 30% while holding cost and quality controls.

## 2. Problem & Opportunity
- Fragmented AI-assisted delivery results in duplicated tooling and inconsistent ROI tracking.
- Lack of contract-first blocks leads to regressions and costly manual reviews.
- Opportunity to standardize orchestration and block authoring to reach ≥80% PR coverage by AI review flows with ≤ baseline defect rate.

## 3. Business Objectives & Success Metrics
| Objective | Metric | Target |
| --- | --- | --- |
| Improve productivity | Idea→Verified Block cycle time | -30% vs baseline |
| Control delivery cost | Tokens/feature | Within budget envelopes defined in Playbook §8 |
| Increase adoption | Pilot repos using orchestrated review flow | ≥80% |
| Maintain quality | Post-merge defects (30 days) | ≤ baseline |
| ROI visibility | Cost/benefit per feature | Reported per release |

## 4. Scope
- **In scope:** Lifecycle Phases 0–7 per framework; Basel-I Structure Trio pilot; dashboards for ROI/cost; budget controls for LLM usage.
- **Out of scope:** External customer launch, vendor renegotiation beyond initial contracts.

## 5. Stakeholders & RACI Alignment
- PM (Product) – Responsible/Accountable for plan package.
- Tech Lead – Accountable for technical correctness and Delivery A/B/C feasibility.
- Biz/Finance – Responsible for ROI modeling, cost guardrails, and governance approvals at G1, G4.
- QA/SRE/Data – Consulted for quality and measurement commitments.

## 6. Requirements
### 6.1 Functional
1. Provide ROI dashboard with per-feature token, latency, and BLOCKER metrics (Phase 4+).
2. Capture cost model assumptions for orchestrator and blocks during Discovery (Phase 1).
3. Enforce governance rules for pricing/usage policy in Definition (Phase 2).

### 6.2 Non-Functional / Constraints
- Budgets per flow enforced via Platform Eng instrumentation.
- PII and secrets compliance per Security policy (Definition gate input).
- Vendor diversification plan to mitigate supply risk (Operate/Scale phase).

## 7. Financials & ROI Hypothesis

### 7.1 Baseline Cost (Current State)
- **LLM Tooling Spend:** $4,200/year (GitHub Copilot licenses, ad-hoc API usage).
- **Manual Review Labor:** ~480 eng-hours/year @ $200/day = $96K (code review cycles, incident triage).
- **Defect Remediation:** ~125 post-merge defects/year × $800/incident = $100K.
- **Total Baseline:** ~$200K annual delivery + quality cost.

### 7.2 Projected Savings (Pilot-Validated)
- **AI-Originated Code:** 38% (pilot avg) reduces manual implementation effort by 18–22% → ~$19K labor savings.
- **Cycle Time Reduction:** -34% idea→verified saves 215 eng-days/year → $43K labor value.
- **Defect Reduction:** -25% defects (pilot trend) → $25K incident cost avoidance.
- **Gross Annual Benefit:** ~$87K (conservative; scales with adoption).

### 7.3 Investment Needs

#### Budget Envelopes (Approved G4)
| Delivery | Component | Annual Budget | Vendor Allocation | Notes |
| --- | --- | --- | --- | --- |
| A (Orchestrator) | Claude (architect/review) | $35K | Anthropic API | 70% of model spend; premium routing |
| A (Orchestrator) | ChatGPT (impl/planner) | $18K | OpenAI API | 30% of model spend |
| A (Orchestrator) | Gemini (context) | $6K | Google AI | Specialist role; low-volume |
| A (Orchestrator) | 4th Model (TBD) | $3K | Reserved | Test generation pilot |
| B (Blocks) | Verification compute | $8K | Internal infra | Mutation/property testing CI |
| C (Integration) | Artifact storage | $4K | S3/GCS | Immutable context bundles |
| **Total Model/Infra** | | **$74K** | | Within $80K approved envelope |

#### Vendor Cost Assumptions (Nov 2025 Pricing)
- **Anthropic Claude (Sonnet 4.5):** $3/M input tokens, $15/M output tokens.
- **OpenAI GPT-4 Turbo:** $10/M input, $30/M output (negotiated volume discount pending).
- **Google Gemini Pro:** $0.50/M input, $1.50/M output.
- **Risk Buffer:** 15% ($11K) for pricing changes, overage, vendor fallback.

#### Engineering Staffing (Delivery A/B/C)
- **Build Phase (4 months):** 2.5 FTE Platform Eng, 1.5 FTE App Eng, 0.5 FTE QA = ~$280K labor.
- **Operate/Scale (ongoing):** 0.3 FTE maintenance, prompt tuning, model eval = ~$60K/year.

### 7.4 ROI Summary
- **Year 1 Investment:** $74K (models/infra) + $280K (build labor) + $60K (ops) = **$414K**.
- **Year 1 Benefit:** $87K (efficiency) + intangible quality/velocity gains.
- **Payback:** 18–24 months at 50-feature/year adoption; **3.6× ROI** at scale (pilot-validated).
- **Break-Even Threshold:** 35 features/year using orchestrated flows (pilot suggests 50+ achievable).

### 7.5 Cost Controls & Governance
- Per-flow token caps enforced via Platform Eng instrumentation (§6.2).
- Monthly budget reviews; alert thresholds at 80% spend.
- Vendor diversification plan (Phase 7) mitigates pricing lock-in risk.

## 8. Risks & Mitigations
| Risk | Phase | Mitigation |
| --- | --- | --- |
| Token cost overruns | Build/Validate | Enforce per-flow token caps, monitor dashboards |
| Compliance gaps | Definition/Design | Security review, secrets plan, gating |
| Adoption lag | Validate/Launch | Training (Enablement WBS 6.2), pilot success narrative |

## 9. Gate Dependencies
- **G1:** ROI hypothesis + cost model complete.
- **G2:** Pricing/usage policy, governance controls approved.
- **G4:** Budget sign-off confirming orchestration/blocks within spend envelope.
- **G5:** Pilot ROI check vs baseline documented.

## 10. Appendices
- References: Governance Framework v1.0, Multi-LLM Playbook v1.0, Orchestrator/Blocks Framework doc.

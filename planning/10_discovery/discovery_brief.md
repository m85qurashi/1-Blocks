# Discovery Brief — Multi-LLM Orchestrator + Verified Blocks

## 1. Inputs
- Idea One-Pager (00_idea/one_pager.md)
- SteeringDirections idea framework + playbook

## 2. User Journeys & JTBD
1. **Platform Engineer** wants to route work to best-suited models without manual orchestration.
2. **App Engineer** needs contract-first blocks with automated verification to trust AI output.
3. **PM/QA** needs evidence (BLOCKERS, tests, metrics) before accepting AI-generated code.

## 3. Alternatives & Competitive Scan
- Build vs buy (internal vs vendor orchestrators) — vendor tools lack block verification + multi-model governance.
- IDE plugins provide assistance but not lifecycle governance.

## 4. Opportunity & ROI Hypothesis
- Productivity gain: 30% faster verified delivery.
- Cost control: token budgets + automation reduce review effort 15–20%.
- Quality: Mutation kill-rate ≥60% reduces escaped defects.

## 5. Risks & Dependencies
| Risk | Mitigation |
| --- | --- |
| Token cost spikes | Budget caps, FlowEngine cost guards |
| Compliance (PII/secrets) | SRE/Sec posture, prompt redaction |
| Adoption | Enablement track (training, playbooks) |

## 6. Spike Plan
- Evaluate ModelRouter prototypes with 4-model mix.
- Prototype BlockBlueprint schema + schema-driven test generation.
- Test integration service for context bundle performance.

## 7. Prioritized Scope Recommendation
- Proceed with Basel-I pilot slice covering Delivery A/B/C minimal features.
- Focus on CLI/CI flows first, defer deep VS Code integration to post-pilot.

**Gate G1 Status:** Ready for review (scope + measurable outcomes defined).

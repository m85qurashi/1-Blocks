# SRE/Security Operations Plan

## 1. SLOs & Reliability Targets
| Service | SLI | Target |
| --- | --- | --- |
| FlowEngine API | Success rate | ≥99% |
| FlowEngine API | P95 latency | ≤90s plan/impl, ≤45s review/docs |
| Catalog API | Availability | ≥99.5% |
| Verification Service | Mutation harness completion | ≥98% runs |

## 2. Security & Secrets Posture
- Secrets stored in vault; CLI obtains short-lived tokens.
- Prompts scrub PII; default deny list enforced.
- Artifact registry encrypts data at rest; access via service principals.

## 3. Runbooks
- **Incident categories:** flow failure, model provider outage, budget breach, security alert.
- Each runbook includes detection signals, mitigation steps, rollback plan, communications.

## 4. Rollout Strategy
- Canary deployments per flow type with token budget guardrails.
- Automated rollback if flow success <98% or cost > budget threshold for 15 min.
- Basel-I pilot limited to dedicated workspace before expansion.

## 5. Monitoring & Alerts
- Metrics from Data plan feed Grafana dashboards; alerts on success rate, latency, mutation completion, token budget usage.
- Security monitoring integrates with SIEM for secret usage anomalies.

## 6. Gate Alignment
- **G2:** Secrets plan + privacy posture documented (sections 2 & 5).
- **G3:** Runbooks + threat model review.
- **G4:** Rollout strategy + monitoring plan validated.
- **G6:** Launch readiness includes oncall schedule updates and capacity plan.

## 7. Open Items
- Finalize incident communication templates with PM/Biz.
- Determine auto-scaling rules for FlowEngine workloads.

# Dependency Map
| Dependency | Needed By | Notes |
| --- | --- | --- |
| Model provider contracts | FlowEngine, review flows | Biz to confirm budget + vendor limits |
| Telemetry stack | Measurement plan, dashboards | Data + SRE to choose stack |
| QA mutation harness | Catalog publishing | Blocks cannot publish without kill-rate metric |
| Artifact registry storage | Integration layer | Needs security sign-off |
| VS Code CLI integration | Adoption goals | Optional for pilot, required post-G5 |

# Changelog

All notable changes to FlowEngine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2025-11-21

### Added
- **Repo Readiness API (v2.0.0)** with SQLAlchemy-based architecture
  - Idea intake endpoint for workflow proposals
  - Repository readiness tracking with 4-point checklist
  - Wave assignment system (soak, wave_1, wave_2, future)
  - Quality gates preventing non-ready repos from production waves
  - Wave export to markdown for governance reviews
  - API key authentication via X-API-Key header
  - CORS support for team_site integration

- **Multi-LLM Infrastructure**
  - Claude Sonnet 4.5 integration (primary)
  - OpenAI GPT-4 Turbo support (fallback)
  - Google Gemini Pro support (bulk/cost-effective)
  - LLM orchestrator with parallel execution
  - Consensus scoring capability

- **Ops Console UI**
  - Real-time connection to Readiness API
  - Idea submission form
  - Readiness tracking interface
  - Wave assignment dashboard
  - Live data tables with refresh

- **Testing Infrastructure**
  - API endpoint tests (4 tests covering idea creation, readiness flow, wave assignment)
  - LLM orchestrator tests (3 tests for parallel execution, fallback, error handling)
  - In-memory SQLite test database
  - Isolated test fixtures

- **Comprehensive Documentation**
  - Executive Summary with ROI analysis
  - Getting Started guide
  - UAT Plan for pilot execution
  - MVP Metrics Log (52+ flows, $11.80 cost validation)
  - Multi-LLM readiness evidence
  - Planning documents across 7 phases
  - Architecture diagrams and interface contracts

### Changed
- Upgraded Repo Readiness API from direct PostgreSQL to SQLAlchemy ORM
- Refactored domain types into separate module for reusability
- Updated requirements.txt with SQLAlchemy 2.0.23, httpx 0.27.0, google-generativeai
- Enhanced LLM Review Gate to use real Claude API instead of heuristics

### Fixed
- CORS configuration for cross-origin requests from team_site
- Database connection handling with proper session management
- API key protection for write operations
- Enum serialization in JSON responses

### Performance
- Average flow execution: 4 seconds
- Average cost per flow: $0.05
- LLM Review cost: ~$0.001 per review
- Gate enforcement: 60% pass rate (correctly blocking low-quality code)

### Evidence
- 52+ flows executed across 24+ repositories
- 5 workflow families validated (compliance, security, testing, deployment, monitoring)
- 260+ individual gate checks performed
- Total validation cost: $11.80
- Real Claude scoring: 29% more critical than heuristics

---

## [1.2.0] - 2025-11-14

### Added
- **5-Gate Quality System**
  - Contract Validation Gate (75% threshold)
  - Unit Test Coverage Gate (80% threshold)
  - Mutation Testing Gate (70% threshold)
  - Security Scan Gate (100% pass required)
  - LLM Review Gate (65% threshold) - initially with heuristic stub

- **Evidence Collection Framework**
  - Phase 1 quality gates evidence
  - Batch execution tracking
  - Gate performance metrics
  - Cost and duration logging

### Changed
- Expanded from 4-gate to 5-gate system
- Improved gate threshold calibration
- Enhanced evidence capture for governance review

---

## [1.1.0] - 2025-11-14 (AM)

### Added
- **FlowEngine Core Application**
  - FastAPI-based REST API
  - PostgreSQL database integration
  - Flow generation endpoint
  - Metrics summary endpoint
  - Health and readiness checks

- **4-Gate Initial System**
  - Contract Validation
  - Unit Test Coverage
  - Mutation Testing
  - Security Scan

- **Deployment Infrastructure**
  - Kubernetes deployment manifests
  - PostgreSQL configuration
  - Docker containerization
  - Deployment scripts (deploy.sh, enable-kubernetes.sh)

### Performance
- Generated 6 test flows successfully
- Total cost: $9.90
- All endpoints operational

---

## [1.0.0] - 2025-11-13

### Added
- **Project Structure**
  - Governance framework
  - Multi-persona organization (Steering, Business, Product, Engineering, QA, Data, SRE)
  - Planning directory with 7 phases (idea → launch)
  - Team site with request hub

- **Planning Framework**
  - Comprehensive planning templates
  - Gate-based approval process (G2-G6)
  - Architecture diagrams and interface contracts
  - Runbooks for operational scenarios
  - Training materials and enablement plans

### Documentation
- Business Requirements Document (BRD)
- Product Requirements Document (PRD)
- Software Requirements Specification (SRS)
- Quality Plan
- Measurement Plan
- SRE Operations Plan

---

## Roadmap

### [1.4.0] - Planned
- [ ] Multi-LLM fallback integration into production gates
- [ ] Redis caching layer for LLM reviews
- [ ] Real-time WebSocket updates for Ops Console
- [ ] Advanced analytics dashboard
- [ ] GitHub Actions CI/CD integration

### [2.0.0] - Future
- [ ] GitHub/GitLab native integration
- [ ] Slack/Teams notification system
- [ ] Custom gate plugin architecture
- [ ] ML-based threshold optimization
- [ ] Multi-tenant support
- [ ] GraphQL API
- [ ] Mobile-responsive UI

---

## Version History Summary

| Version | Release Date | Key Features |
|---------|-------------|--------------|
| 1.3.0 | 2025-11-21 | Repo Readiness API, Multi-LLM, Ops Console, Comprehensive Docs |
| 1.2.0 | 2025-11-14 | 5-Gate System, Evidence Framework |
| 1.1.0 | 2025-11-14 | FlowEngine Core, 4-Gate System, K8s Deployment |
| 1.0.0 | 2025-11-13 | Initial project structure, Planning framework |

---

[1.3.0]: https://github.com/m85qurashi/1-Blocks/releases/tag/v1.3.0
[1.2.0]: https://github.com/m85qurashi/1-Blocks/releases/tag/v1.2.0
[1.1.0]: https://github.com/m85qurashi/1-Blocks/releases/tag/v1.1.0
[1.0.0]: https://github.com/m85qurashi/1-Blocks/releases/tag/v1.0.0

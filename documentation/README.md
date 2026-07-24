# Project Showcase Documentation — Lagovia Train Tracker

Detailed showcase documentation covering each completed implementation phase of the **Lagovia Train Tracker** project.

---

## Phase Documentation Index

| Phase | Document | Description | Status |
|-------|----------|-------------|--------|
| **Phase 0** | [PHASE_0.md](PHASE_0.md) | Repo & Tooling Skeleton, FastAPI setup, React + Vite setup, `Makefile` CI-lite | Completed |
| **Phase 1** | [PHASE_1.md](PHASE_1.md) | Pure `irail_client.py` fetch/parse module, zero FastAPI imports, `respx` unit tests | Completed |
| **Phase 2** | [PHASE_2.md](PHASE_2.md) | Pure `domain.py` logic, 15-min UTC window boundary filtering, response contract shaping | Completed |
| **Phase 3** | [PHASE_3.md](PHASE_3.md) | `GET /departures` endpoint, 3-char min query 400 validation, concurrent fan-out, error isolation | Completed |

---

## Documentation Structure

Each phase document contains:
- **Overview & Objectives**: Goals and enforced constraints.
- **Component Breakdown**: Code snippets and file paths.
- **Verification & Test Execution**: Command output logs.
- **Architectural & Design Trade-Offs**: Explanations for key engineering decisions.

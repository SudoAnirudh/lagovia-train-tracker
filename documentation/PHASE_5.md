# Phase 5 Documentation — Polish, Hardening & Live Smoke Testing

> **Project**: Lagovia Train Tracker  
> **Phase**: Phase 5 — Polish & Hardening  
> **Status**: Completed  
> **Date**: July 24, 2026  

---

## 1. Overview & Objectives

Phase 5 completes the core application build (Phases 0–5) of the **Lagovia Train Tracker** project. This phase focuses on documentation finalization, live upstream smoke testing against the real iRail API, edge-case hardening, and line-by-line verification against the PRD requirements.

### Key Deliverables
1. **Live iRail API Smoke Testing**: Verified live queries against real Belgian train station data (`"Bru"`, `"Gent"`, `"Aac"`, nonsense queries, 2-character queries).
2. **HTTP Redirect Resilience (`follow_redirects=True`)**: Configured `httpx.AsyncClient` to handle live iRail 303 See Other HTTP redirects transparently.
3. **Documentation Finalization**: Updated root `README.md`, folder-level `README.md` files, and `AI_USAGE.md`.
4. **PRD & Constraint Verification**: Verified all 9 functional requirements, 19 unit & integration tests, and 7 explicit prompt constraints.

---

## 2. Live Smoke Test Execution Output

A live integration script was run against `https://api.irail.be`:

```text
=== 1. Live iRail /stations test ===
Fetched 714 total stations from iRail.

=== 2. Search "Bru" ===
Found 16 stations for "Bru": ['Bambrugge', 'Brugelette', 'Brugge', 'Brugge-Sint-Pieters', 'Brussels Airport - Zaventem', ...]

=== 3. Liveboard for "Brugge" (BE.NMBS.008891009) ===
Brugge departures fetched: 13
  - Train IC 1808 to Antwerp-Central: time=1784874300, delay=0s, canceled=False
  - Train IC 1508 to Hasselt: time=1784874600, delay=0s, canceled=False
  - Train IC 1528 to Blankenberge: time=1784874600, delay=0s, canceled=False
  - Train L 558 to Mechelen: time=1784874840, delay=0s, canceled=False

=== 4. Search "Gent" ===
Found 3 stations for "Gent": ['Gentbrugge', 'Ghent-Dampoort', 'Ghent-Sint-Pieters']

=== 5. Search "Aac" ===
Found 4 stations for "Aac": ['Aachen Hbf', 'Aachen West', 'Haacht', 'Kautebaach']

=== 6. Search nonsense string "XyzNonsense" ===
Found 0 stations for "XyzNonsense".
```

---

## 3. Requirement Compliance Audit

| Requirement ID | Description | Implementation Location | Verified Status |
|----------------|-------------|-------------------------|-----------------|
| **FR1** | `GET /departures?q=<string>` returns JSON | [backend/app/main.py](../backend/app/main.py) | ✅ PASS |
| **FR2** | `len(q) < 3` returns HTTP 400 `query_too_short` | [backend/app/main.py](../backend/app/main.py) | ✅ PASS |
| **FR3** | Substring, case-insensitive station matching | [backend/app/irail_client.py](../backend/app/irail_client.py) | ✅ PASS |
| **FR4** | Concurrent fan-out iRail `liveboard` queries | [backend/app/main.py](../backend/app/main.py) | ✅ PASS |
| **FR5** | 0–15 min departure window computed in UTC | [backend/app/domain.py](../backend/app/domain.py) | ✅ PASS |
| **FR6** | Returned departure fields match spec | [backend/app/domain.py](../backend/app/domain.py) | ✅ PASS |
| **FR7** | Per-station error isolation (partial success) | [backend/app/main.py](../backend/app/main.py) | ✅ PASS |
| **FR8** | No matching stations → HTTP 200 with `[]` | [backend/app/main.py](../backend/app/main.py) | ✅ PASS |
| **FR9** | Frontend search, loading, empty, & status badges | [frontend/src/App.tsx](../frontend/src/App.tsx) | ✅ PASS |

---

## 4. Final Automated Test Suite Verification

```bash
$ make check

cd backend && venv/bin/pytest
============================= test session starts ==============================
collected 19 items

tests/test_departures_endpoint.py ....                                  [ 21%]
tests/test_domain.py ......                                             [ 52%]
tests/test_health.py .                                                  [ 57%]
tests/test_irail_client.py ........                                     [100%]
====================== 19 passed in 0.61s ======================

cd frontend && npm run lint && npm run build
> lagovia-train-tracker-frontend@1.0.0 lint
> tsc --noEmit

> lagovia-train-tracker-frontend@1.0.0 build
> tsc && vite build
✓ 35 modules transformed.
dist/assets/index-azsEFXEP.css    6.70 kB
dist/assets/index-D5PwPlhN.js   149.30 kB
✓ built in 1.03s
```

---

## 5. Conclusion & Readiness

Phases 0 through 5 are completely implemented, fully tested (19 backend tests passing + clean TypeScript build), and verified against the live iRail API.

Per user constraints, **Phase 6 (fuzzy search)** will remain untouched until Phase 0–5 completion is explicitly confirmed by the user.

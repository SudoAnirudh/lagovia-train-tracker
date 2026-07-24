# Implementation Prompt — Lagovia Train Tracker

Use this as the opening prompt to an AI coding agent (Claude Code, Cursor, etc.) once
`PRD.md`, `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, `TECH_STACK.md`, and `RULES.md` are in
the repo root. Paste it as-is, or adapt per phase (see "Phase-by-phase variant" below).

---

## Full-build prompt

```
You are implementing the Lagovia Train Tracker project in this repository.

Before writing any code, read these files in full and treat them as binding:
- PRD.md — requirements, API contract, in/out of scope
- IMPLEMENTATION_PLAN.md — the phase order to build in
- AGENTS.md — repo conventions, layout, and hard rules for how you work in this repo
- TECH_STACK.md — the chosen stack and why; do not introduce alternatives without flagging it
- RULES.md — enforceable engineering rules (testing, error handling, git hygiene)

Task: implement Phase 0 through Phase 5 of IMPLEMENTATION_PLAN.md, in order. Do not
start Phase 6 (fuzzy search) until Phases 0–5 are complete and I've confirmed it.

Constraints that override convenience:
1. Backend: Python + FastAPI, per TECH_STACK.md. Frontend: React + TypeScript + Vite.
2. irail_client.py and domain.py must have zero FastAPI imports and must be unit
   testable without network access — mock iRail responses in tests.
3. The 15-minute departure window must be computed in UTC, server-side, with explicit
   boundary tests (exactly now, exactly +15min, +15min+1s excluded).
4. Queries under 3 characters return HTTP 400 with error code `query_too_short` —
   never a 200 with an empty list for this case.
5. A failed upstream call for one matched station must not fail the whole response —
   return that station with status "error" and let the rest succeed.
6. Match the JSON response shape in PRD.md §7 exactly. If you need to deviate, stop and
   tell me why before proceeding — don't silently diverge docs from code.
7. Every network/loading/empty/error state must be visibly handled on the frontend —
   no state should render a blank screen.

For each phase:
- Implement it.
- Write the tests specified for that phase in IMPLEMENTATION_PLAN.md / RULES.md.
- Run the tests and show me the output.
- Give me a short summary of what you built and any decision you made that wasn't
  fully specified in the docs (e.g. debounce vs. submit button, retry policy) — I'll
  confirm or redirect before you move to the next phase.

Stop and ask me before:
- Adding any dependency not already named in TECH_STACK.md.
- Adding anything listed under "Explicitly Out of Scope" in PRD.md §4.
- Changing the documented API contract.

Start with Phase 0.
```

---

## Phase-by-phase variant

If you'd rather review after each phase instead of letting the agent run through 0–5,
swap the task line for:

```
Task: implement ONLY Phase <N> of IMPLEMENTATION_PLAN.md. Stop after it's done, tests
pass, and you've summarized what you built and any open decisions. Wait for my
go-ahead before starting the next phase.
```

Re-send with `<N>` incremented after each review. Slower, but each phase gets a real
checkpoint — useful if you want to be able to explain every diff in the walkthrough
without having skimmed a large batch of changes.

---

## Bonus (fuzzy search) prompt — only after Phases 0–5 are solid

```
Phases 0–5 are complete and confirmed. Now implement Phase 6 (fuzzy search) from
IMPLEMENTATION_PLAN.md: substring matching stays the primary path; fuzzy matching
(e.g. rapidfuzz) only fills in when substring search returns zero stations. Add this
as an additive layer — don't modify the existing substring path. Add "Antverpen" →
"Antwerpen-Centraal" as a test case, since it's the brief's own example. Update
TECH_STACK.md with a one-line justification for the new dependency, per RULES.md rule 6.
```

---

## Why the prompt is structured this way

- **Documents-as-contract, not documents-as-suggestion**: the agent is told to treat
  the five docs as binding, not as background reading — this is what keeps an agent
  from quietly expanding scope mid-session.
- **Explicit stop conditions**: naming exactly when the agent must pause (new
  dependency, scope-list item, contract change) turns AGENTS.md's soft guidance into
  hard checkpoints in the actual prompt.
- **Phase gating**: mirrors IMPLEMENTATION_PLAN.md's own sequencing logic — domain
  logic and its tests before the HTTP layer, HTTP layer before frontend — so you're
  never debugging three unverified layers at once.
- **Forced summarization per phase**: cheap insurance for the walkthrough — you get a
  running log of decisions as they're made, instead of reconstructing "why did I do
  this" from memory afterward.

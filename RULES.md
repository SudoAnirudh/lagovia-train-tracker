# Engineering Rules

Short, enforceable rules for this repo — for humans and AI agents alike. If a rule can't
be checked by a reviewer in under a minute, it doesn't belong here.

## Code

1. **No function does two jobs.** Fetching from iRail, filtering by time window, and
   shaping the HTTP response are three separate functions, each independently testable.
   If a diff adds logic to `main.py` that isn't pure orchestration, that's a signal to
   extract it to `domain.py`.
2. **All times are UTC internally, ISO 8601 on the wire.** Convert to local display
   format only in the frontend, only for rendering.
3. **Every upstream call has an explicit timeout.** No unbounded waits on iRail.
4. **Every error path returns a typed, documented shape** — no bare stack traces or
   generic `{"error": "something went wrong"}` reaching the client.
5. **No silent catch-and-ignore.** If an exception is caught and not re-raised, the
   reason must be a one-line comment, and it must still be logged.
6. **New dependency = one-line justification in `TECH_STACK.md`.** Not a formal process
   — just enough that "why is this here" has an answer six months from now.

## Testing

7. **Domain logic (`domain.py`, `irail_client.py`) has unit tests with no live network
   calls.** Mock iRail responses; commit the fixtures.
8. **The 15-minute window has explicit boundary tests**: a departure at exactly `now`,
   exactly `now + 15min`, and `now + 15min + 1s` (the last one must be excluded).
9. **The 3-character minimum has a test on both sides of the boundary** (2 chars → 400,
   3 chars → normal processing, even if it returns zero matches).
10. **At least one test exercises partial upstream failure** — one matched station
    succeeds, one fails — asserting the response still returns 200 with per-station
    status, not a 500.

## Git / process

11. **Commits are scoped to one phase/concern at a time**, matching
    `IMPLEMENTATION_PLAN.md` phases where practical — makes the history itself part of
    the explanation of how the thing was built, which is useful for the walkthrough.
12. **Every non-obvious decision gets a one-line "why" — in a commit message, code
    comment, or README, not just in your head.** The walkthrough will ask "why did you
    do X"; the answer should already be written down somewhere.
13. **Don't merge/commit code you can't explain.** This includes AI-generated code —
    if it's in the repo, you own it and should be able to walk through it live.

## Frontend

14. **Every network state is rendered**: loading, empty-result, per-item error,
    success. No state silently falls through to a blank screen.
15. **Delay = 0 is shown as "on time," not omitted** — the brief explicitly calls out
    `0 = on time` as a value to display, not a value to hide.
16. **Cancelled departures are visually distinct**, not just present as a boolean
    somewhere in the DOM a user has to hunt for.

## AI usage

17. **Log AI usage as you go**, not reconstructed from memory at the end — append to
    `AI_USAGE.md` in the same sitting you use the tool, including prompts and what was
    kept vs. rewritten vs. rejected.
18. **Never commit AI output you haven't read.** "I accepted this suggestion" in
    `AI_USAGE.md` means you read it and agreed with it, not that you clicked accept.

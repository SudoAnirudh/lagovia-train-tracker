# Phase 4 Documentation — Frontend UI Implementation

> **Project**: Lagovia Train Tracker  
> **Phase**: Phase 4 — Frontend UI  
> **Status**: Completed  
> **Date**: July 24, 2026  

---

## 1. Overview & Objectives

Phase 4 delivers the single-page React 18 + TypeScript user interface for the **Lagovia Train Tracker** application in `frontend/src/`.

### Key Rules & Constraints Enforced
1. **Explicit Submit Trigger**: The search interface uses an explicit submit button ("Search Departures") rather than live debounced keystroke requests, reducing upstream iRail load and providing unambiguous UX.
2. **Instant Client-Side Validation**: Searches with fewer than 3 characters trigger an immediate client-side validation message ("Please enter at least 3 characters to search stations") without firing network calls, while the backend remains the authority on validation.
3. **Comprehensive State Rendering (Rule #14 & Constraint #7)**: Every network state is explicitly rendered:
   - **Loading state**: Spinner loader with clear status messaging.
   - **Empty results state**: Helpful empty message when no stations match query.
   - **Global error state**: Server error banner with retry button.
   - **Per-station error state**: If one station fails upstream, a warning badge is displayed inside that station's card while other stations render normally.
4. **Visual Rules (Rules #15 & #16)**:
   - `delay_minutes === 0` is explicitly displayed as a green **"On time"** badge (never hidden).
   - Delayed departures display an amber **"+X min"** badge.
   - Cancelled departures display a bold red **"CANCELLED"** badge with line-through styling on train information.

---

## 2. Component Architecture

```text
frontend/src/
├── api.ts                  # Typed fetch client for /departures with error handling
├── types.ts                # TypeScript interface definitions for API response models
├── components/
│   ├── SearchForm.tsx      # Input field, client-side validation, submit trigger
│   ├── StationCard.tsx     # Per-station container, header, error state & departure list
│   └── DepartureRow.tsx    # Table row displaying train number, time, destination, status
├── App.tsx                 # Root layout, state management (loading, error, empty, success)
└── index.css               # Design system, CSS variables, badges, and responsive tables
```

---

## 3. UI Component Details

### 3.1 Search & Validation (`SearchForm.tsx`)
Validates query length before calling `onSearch`:
```typescript
if (trimmed.length < 3) {
  setValidationError('Please enter at least 3 characters to search stations.');
  return;
}
```

### 3.2 Status Badge Rendering (`DepartureRow.tsx`)
```tsx
{cancelled ? (
  <span className="badge badge-cancelled">CANCELLED</span>
) : delay_minutes > 0 ? (
  <span className="badge badge-delayed">+{delay_minutes} min</span>
) : (
  <span className="badge badge-ontime">On time</span>
)}
```

---

## 4. Verification & Build Output

Executing `make check` verifies both backend tests and frontend typechecking and production build:

```bash
$ make check

cd backend && venv/bin/pytest
======================= 19 passed in 0.61s =======================

cd frontend && npm run lint && npm run build
> lagovia-train-tracker-frontend@1.0.0 lint
> tsc --noEmit

> lagovia-train-tracker-frontend@1.0.0 build
> tsc && vite build
vite v5.4.21 building for production...
✓ 35 modules transformed.
dist/index.html                   0.41 kB │ gzip:  0.28 kB
dist/assets/index-azsEFXEP.css    6.70 kB │ gzip:  2.01 kB
dist/assets/index-D5PwPlhN.js   149.30 kB │ gzip: 48.08 kB
✓ built in 983ms
```

---

## 5. Key Design Decisions & Trade-Offs

1. **Submit Button vs. Debouncing**:
   Chosen explicit submit trigger over debounced search. This prevents accidental multi-character requests to iRail while the user is still typing, saving bandwidth and improving stability.
2. **Local Time Formatting**:
   Scheduled departure times arrive as UTC ISO 8601 strings (e.g. `"2026-07-24T10:22:00Z"`). The frontend formats them to local `HH:mm` display format using `toLocaleTimeString()`.

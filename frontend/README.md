# Frontend — Lagovia Train Tracker

React + TypeScript Single Page Application (SPA) built with Vite for the Lagovia Train Tracker application.

---

## Technical Stack

- **Framework**: React 18
- **Language**: TypeScript (strict mode)
- **Build Tool**: Vite
- **Styling**: Vanilla CSS with modern custom properties (CSS variables)

---

## Directory Layout

```text
frontend/
├── src/
│   ├── App.tsx          # Main application component
│   ├── main.tsx         # React DOM entrypoint
│   └── index.css        # Core styles & design system tokens
├── dist/                # Production build output (generated)
├── index.html           # HTML template
├── package.json         # Dependencies & npm scripts
├── tsconfig.json        # TypeScript compiler options
├── vite.config.ts       # Vite configuration & dev API proxying
└── README.md            # This document
```

---

## Quickstart

### 1. Installation

```bash
cd frontend
npm install
```

### 2. Development Server

```bash
npm run dev
```

The app will start at `http://localhost:3000`.

---

## Available Scripts

- `npm run dev`: Start Vite development server with hot module replacement (HMR).
- `npm run lint`: Run TypeScript type-checker (`tsc --noEmit`) without emitting build files.
- `npm run build`: Execute typecheck and generate production bundle in `dist/`.
- `npm run preview`: Serve production build locally for verification.

---

## API Proxying Configuration

Vite is configured in `vite.config.ts` to proxy requests starting with `/departures` and `/health` to the FastAPI backend running at `http://127.0.0.1:8000`:

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/departures': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
    },
  },
});
```

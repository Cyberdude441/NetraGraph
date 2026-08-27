# NetraGraph AI Frontend

The frontend is a Vite + React + TanStack Router application. It owns the investigation UI, client state, deterministic demo fallbacks, and HTTP access through `src/services/api.ts`.

## Local Commands

From the repository root:

```bash
npm run dev
npm run build
npm run lint
```

The root scripts delegate to this directory so existing workflows remain valid.

## Source Layout

- `src/components/`: reusable UI and investigation surfaces
- `src/routes/`: application pages
- `src/hooks/`: client state and query hooks
- `src/services/`: API and report/evidence client services
- `src/data/`: synthetic demo fallback data
- `src/utils/`: deterministic client-side presentation and fallback analysis helpers
- `src/styles.css`: global design tokens and layout utilities

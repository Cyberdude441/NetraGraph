# NetraGraph UI Layout Audit

Audit baseline: current Vite React frontend and FastAPI backend before the architecture/layout pass.

## Dashboard

**Section:** Top header row  
**Current Layout:** Fixed sidebar plus a flex header containing title, search, Add Record, and profile actions.  
**Problem:** Header spacing is flexible and can compress the search field and profile at narrower desktop widths.  
**Affected Row:** Global application header.  
**Affected Column:** Main content header, especially between 1024px and 1400px.  
**Reason:** Main content offset and sidebar breakpoint must be coordinated; action groups have no explicit width allocation.  
**Required Fix:** Use a fixed 280px desktop sidebar, an explicit main-content offset, and a header grid with title, search, actions, and profile regions.

**Section:** Dashboard metric cards  
**Current Layout:** Five-card responsive grid with `lg:grid-cols-5`; cards have a desktop minimum width but no explicit row overflow strategy.  
**Problem:** At 1366px the usable main width is close to the combined 220px card minimums plus gaps.  
**Affected Row:** Top KPI row.  
**Affected Column:** All five metric cards.  
**Reason:** 280px sidebar plus page padding leaves insufficient space for five 220px cards at some desktop widths.  
**Required Fix:** Preserve five desktop columns, use stable card sizing and compact internal content, and prevent body-level horizontal scrolling.

## Entities & Profiles

**Section:** Filters / entity list / dossier  
**Current Layout:** Route-level multi-panel layout with filter and result surfaces.  
**Problem:** Filter controls and dossier content can create nested scrolling and long-value clipping.  
**Affected Row:** Entity explorer workspace.  
**Affected Column:** Filters and right dossier.  
**Reason:** Panel widths are driven by content and breakpoints rather than explicit minimums; entity metadata is dense.  
**Required Fix:** Use a 320px collapsible filter column, a list column with 450px minimum at desktop, and a 500px dossier rail with wrapped IDs/values.

## Knowledge Graph

**Section:** Graph canvas and analysis controls  
**Current Layout:** Graph canvas with filters, selected entity details, and analytics panels.  
**Problem:** Floating controls and analysis panels compete for the same canvas area.  
**Affected Row:** Graph viewport and bottom analysis region.  
**Reason:** Multiple panels use absolute/flex positioning without a single drawer ownership model.  
**Required Fix:** Reserve a bounded graph canvas, use a bottom analytics drawer, and keep selected entity details in a separate right drawer.

## Alerts & Anomalies

**Section:** Filters / alert stream / explanation  
**Current Layout:** Dense panels with analytics cards and alert detail content.  
**Problem:** Center alert content can compress while left filters and right explanation remain visually heavy.  
**Affected Row:** Main anomaly workspace.  
**Affected Column:** Filter and alert stream columns.  
**Reason:** Repeated card containers and fixed-width content compete for horizontal space.  
**Required Fix:** Allocate approximately 300px filters, 500px alert stream, and flexible explanation; collapse advanced analysis on smaller widths.

## Geographic Intelligence

**Section:** Filters / map / location dossier  
**Current Layout:** Map with overlays, controls, and location detail surfaces.  
**Problem:** Map loses usable area when filters and dossier content are expanded.  
**Affected Row:** GIS workspace.  
**Affected Column:** Map center column.  
**Reason:** Side panels consume width and map overlays are not consistently bounded.  
**Required Fix:** Use 300px filters, a flexible map center, and a 350px dossier rail; allow mobile vertical stacking.

## AI Assistant

**Section:** Context / chat / evidence  
**Current Layout:** Context manager, query workspace, reasoning pipeline, and evidence cards.  
**Problem:** Evidence and query panels become narrow and dense at desktop widths below the widest breakpoint.  
**Affected Row:** Assistant workspace.  
**Affected Column:** Chat center and evidence rail.  
**Reason:** Content panels have competing minimum content sizes and repeated bordered containers.  
**Required Fix:** Allocate 300px context, at least half the available width to chat, and 400px evidence at wide desktop; collapse context/evidence below desktop.

## Case Workspace

**Section:** Case header and investigation body  
**Current Layout:** Header, left case navigation, center content, and a desktop context rail added in the previous pass.  
**Problem:** At intermediate widths, the navigation/context columns can reduce the investigation content too aggressively.  
**Affected Row:** Case workspace body.  
**Affected Column:** Left navigation, center content, right context rail.  
**Reason:** Three-column layout is applied without a dedicated tablet collapse strategy.  
**Required Fix:** Keep the header compact, collapse the context rail below desktop, and use compact icon-plus-label case navigation with one primary scroll owner.

## Global Findings

- Fixed-height surfaces can clip content when viewport height is short.
- Multiple nested `overflow-y-auto` regions increase scroll ambiguity.
- Several routes import synthetic data and analytical algorithms directly into route/components; these are domain/data concerns rather than UI concerns.
- `frontend/src/routes/network.tsx` contained a direct backend `fetch` instead of using the shared API service.
- Root-level package/build configuration currently serves the frontend while backend is Python; the frontend needs an explicit package boundary.
- Global sizing and body overflow safeguards are required to prevent layout bleed.

## Architecture Fix Direction

- Move the React application into `frontend/` while preserving its internal `src/` imports and Vite/TanStack behavior.
- Keep Python application logic, APIs, database, graph processing, AI, and evidence services under `backend/`.
- Add a frontend-owned API service boundary and route direct network calls through it.
- Add explicit frontend and backend package metadata without changing runtime algorithms or endpoint contracts.

## Completion Report

### Frontend/Backend Separation Completed

- React/Vite application moved to `frontend/`.
- Python FastAPI application remains under `backend/`.
- Root scripts delegate to the frontend for backward-compatible `npm run dev`, `npm run build`, and `npm run lint` commands.
- Graph public-data access now goes through `frontend/src/services/api.ts`.
- Added frontend and backend package metadata plus Dockerfiles and root Compose orchestration.

### UI Audit Completed

- Added fixed desktop shell geometry with a 280px sidebar and explicit content offset.
- Added 80px tablet icon rail and mobile drawer behavior.
- Added global box sizing and horizontal overflow protection.
- Removed fixed-height clipping from the audited workspace shells and protected side columns from shrinking.
- Preserved the dashboard five-column metric row and 220px desktop card minimum.
- Added compact case navigation and a three-column case workspace at desktop width.

### Fixed Pages

- Dashboard
- Entities & Profiles
- Knowledge Graph
- Alerts & Anomalies
- Geographic Intelligence
- AI Assistant
- Case Workspace

### Remaining Issues

- Existing frontend lint output contains a broad backlog of Prettier and explicit-`any` findings in untouched legacy code; no wholesale formatting pass was applied because it would create unrelated churn.
- The frontend still contains deterministic synthetic fallback datasets and analytical helpers for offline/demo behavior. Moving those algorithms to backend endpoints would change runtime behavior and API contracts, so they remain client-side by design.
- Docker image builds were configured but not executed because Docker availability was not established in this environment.

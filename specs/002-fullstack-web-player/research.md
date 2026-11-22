# Technical Research & Architecture Decisions: Decoupled Full-Stack Web Player

**Feature**: `002-fullstack-web-player`
**Date**: 2026-11-21
**Status**: Completed

---

## 1. Flask REST API Architecture & Blueprints

### Decision
- Use Flask's Application Factory pattern (`create_app(config=...)`) in `src/api/app.py`.
- Structure endpoints across 3 domain-specific Blueprints:
  - `books_bp` (`/api/books`): Book upload, list catalog, book sentence retrieval.
  - `player_bp` (`/api`): Audio sentence synthesis/streaming (`/api/audio/<book_id>/<sentence_idx>`), bookmark get/update (`/api/bookmarks/<book_id>`), session creation (`/api/sessions`).
  - `analytics_bp` (`/api/analytics`): Summary KPI metrics (`/api/analytics/summary`) and binary Matplotlib chart streams (`/api/analytics/charts/<chart_type>.png`).
- Enable Cross-Origin Resource Sharing via `flask-cors` (`CORS(app, resources={r"/api/*": {"origins": "*"}})`) allowing the Vite dev server (`http://localhost:5173`) and production web builds to communicate smoothly.

### Rationale
- Enforces strict tier separation: Route handlers only unpack HTTP requests, validate schemas, call Core Engine services, and return JSON/binary responses. No database queries, TTS logic, or tokenization are implemented in routes.
- Modular Blueprints prevent single-file route sprawl and allow independent testing of each endpoint domain.

### Alternatives Considered
- *FastAPI*: Excellent async framework, but adds `uvicorn`/`starlette` async runtime overhead when our Core Engine and database repositories are currently synchronous and multithreaded. Flask integrates natively with existing synchronous SQLAlchemy connection pooling and Python standard libraries.
- *Single-file Flask app*: Violates Constitution Principle I and user requirement ("No business logic directly embedded in routes; no monolithic files").

---

## 2. Request Validation & Structured Error Handling

### Decision
- Use Pydantic v2 schemas in `src/api/schemas/` to validate incoming JSON payloads and multipart upload form data.
- Decorate routes or use helper functions to parse and validate request data before passing to services.
- Register global error handlers in Flask for:
  - `ValidationError` (Pydantic) -> HTTP 400 Bad Request with field-level error messages (`{"error": "Validation failed", "details": [...]}`).
  - `LookupError` / `FileNotFoundError` -> HTTP 404 Not Found (`{"error": "Resource not found"}`).
  - `ValueError` -> HTTP 422 Unprocessable Entity.
  - `Exception` -> HTTP 500 Internal Server Error with sanitized error logging (never leaking sensitive secrets).

### Rationale
- Satisfies requirement FR-008 and success criterion SC-006 (100% of invalid payloads receive deterministic JSON responses without uncaught 500 crashes).

---

## 3. Audio Streaming & Lookahead Buffering via HTTP

### Decision
- Endpoint: `GET /api/audio/<book_id>/<sentence_idx>?speed=1.0&voice=...`
- The endpoint queries the Core Engine's `LookaheadBuffer` / `AudioCacheManager` / `TTSFactory`:
  - If cached on disk (`.studylab/cache/audio/<book_id>/<hash>.mp3`), returns immediately via Flask's `send_file(path, mimetype="audio/mpeg")`.
  - If not cached, synthesizes on demand, writes to cache, logs latency telemetry, and streams the file.
- Frontend Player Architecture (`useAudioPlayer` custom hook):
  - Uses dual HTML5 `Audio` instances (Active Player & Pre-fetch Player).
  - When sentence $N$ starts playing, the pre-fetch instance loads `/api/audio/<book_id>/<sentence_idx + 1>`.
  - When sentence $N$ completes, playback flips instantly to the pre-fetched audio, achieving $<200$ms transition silence (SC-003).

### Rationale
- Discrete sentence endpoints enable instant random-access seeking (jump to sentence 42 without downloading the entire book).
- Browser native caching via HTTP `Cache-Control: public, max-age=86400` ensures repeated listening of sentences consumes zero network bandwidth and zero TTS API calls.

### Alternatives Considered
- *Single continuous chunked HTTP stream*: Difficult to seek sentence-by-sentence, hard to sync visual sentence highlights, and prone to broken pipe errors on network hiccups.

---

## 4. Headless Matplotlib Visual Chart Streaming

### Decision
- Core Engine module: `src/core/analytics/dashboard.py` implementing `generate_listening_trend_chart()` and `generate_latency_metric_chart()`.
- Enforce headless backend: `matplotlib.use('Agg')` at module import time.
- Chart generation procedure:
  1. Query aggregated statistics from `SqlSessionRepository` and `SqlTelemetryRepository`.
  2. Plot dual-axis / multi-panel figures with high-contrast, clean styling (dark mode friendly, clear labels, legends).
  3. Render directly into in-memory `io.BytesIO` buffer via `fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')`.
  4. Close figure explicitly via `plt.close(fig)` to eliminate memory leaks.
  5. Flask streams buffer via `send_file(buf, mimetype='image/png')` with `Cache-Control: no-cache`.

### Rationale
- Strictly complies with Constitution Principle IV (Headless & Clean Matplotlib Visualization).
- Prevents GUI freezing or X11/Wayland display errors on headless servers and local dev machines.

---

## 5. React SPA Frontend Architecture (Vite + React + TypeScript)

### Decision
- Build tooling: Vite 5+ with `@vitejs/plugin-react` and TypeScript.
- Directory layout in `frontend/`:
  - `src/api/`: Typed API client using native `fetch` with error normalization (`client.ts`, `booksApi.ts`, `playerApi.ts`, `analyticsApi.ts`).
  - `src/hooks/`: Modular custom hooks (`useAudioPlayer.ts`, `useBookCatalog.ts`, `useDashboard.ts`).
  - `src/components/`: Modular subdirectories (`Player/`, `BookUploader/`, `Dashboard/`, `Navbar/`, `common/`).
  - `src/pages/`: Route views (`LibraryPage.tsx`, `PlayerPage.tsx`, `DashboardPage.tsx`).
  - `src/types/`: Shared TypeScript interfaces matching API schema definitions.
- Constraint enforcement: Maximum 250 lines of code per file; no monolithic components.

### Rationale
- Vite provides sub-second hot module replacement (HMR) and lightweight production builds.
- TypeScript ensures strict contract adherence with Flask API schemas.
- Custom hook separation isolates audio DOM manipulation from UI layout components.

# Implementation Plan: Decoupled Full-Stack Web Player

**Branch**: `feature/002-fullstack-web-app` | **Date**: 2026-11-21 | **Spec**: [spec.md](file:///home/hai/Du_lieu_hoc_tap/Project/BTL_Python_Project/StudyLab/specs/002-fullstack-web-player/spec.md)

**Input**: Feature specification from `specs/002-fullstack-web-player/spec.md`

## Summary

Build a decoupled full-stack web application for the Smart Audiobook Reader comprising three strictly isolated tiers:
1. **Python Core Engine (`src/core`)**: Domain logic for text ingestion, 35-word clause boundary chunking, Edge-TTS audio synthesis, disk caching, SQLAlchemy MySQL connection pooling, and headless Matplotlib visual dashboard generation.
2. **Flask REST API (`src/api`)**: Blueprint-driven HTTP service (`books_bp`, `player_bp`, `analytics_bp`) with CORS, Pydantic request validation schemas, and audio streaming endpoints with zero embedded business logic.
3. **React SPA Frontend (`frontend`)**: Vite + React + TypeScript component architecture with separated API clients, custom `useAudioPlayer` hooks, modular UI components (`Player`, `BookUploader`, `Dashboard`), and dedicated pages without monolithic files.

---

## Technical Context

**Language/Version**: Python 3.12 (Backend) and TypeScript 5.3+ / Node.js 18+ (Frontend)

**Primary Dependencies**:
- *Backend*: Flask 3.0+, Flask-CORS 4.0+, SQLAlchemy 2.0+, Pydantic 2.5+, Edge-TTS 6.1+, Matplotlib 3.8+, PyMySQL 1.1+, python-dotenv 1.0+
- *Frontend*: React 18.2+, Vite 5.0+, Lucide React (icons), native HTML5 Audio API

**Storage**: MySQL 8.0+ / SQLite 3 via SQLAlchemy connection pooling (`pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`)

**Testing**: `pytest` and `pytest-mock` (Backend unit, contract, and integration tests); Vitest / RTL (Frontend component tests)

**Target Platform**: Linux / macOS / Windows localhost web browser

**Project Type**: Decoupled 3-Tier Full-Stack Web Application

**Performance Goals**:
- Time-to-first-sentence audio playback: $<1.5$ seconds
- Inter-sentence transition silence: $<200$ ms via client-side lookahead audio buffering
- Headless Matplotlib chart rendering: $<1.0$ second

**Constraints**:
- Strict 3-tier decoupling: Zero domain/database logic in Flask route handlers
- Zero cloud model training: Strictly third-party APIs (Edge-TTS)
- Headless Matplotlib: `matplotlib.use('Agg')` strictly enforced
- Frontend modularity: No file exceeds 250 LOC; no monolithic components

**Scale/Scope**: Single-user localhost audiobook streaming, cataloging, and observability dashboard

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Compliance Status | Justification |
| :--- | :--- | :--- | :--- |
| **I. Modular & Decoupled Architecture** | Domain logic, HTTP API, and frontend strictly isolated; no cyclic dependencies | **PASS** | `src/core/` contains pure domain logic. `src/api/` handles HTTP only. `frontend/` communicates exclusively via REST APIs. |
| **II. Cloud TTS API-First** | Zero local model training; production third-party APIs (Edge-TTS) | **PASS** | Uses Microsoft Edge-TTS with sentence-level chunking and local disk caching. |
| **III. Observability & Telemetry** | Per-sentence TTS latency and LAN/Tailscale ping logged to `network_metrics` | **PASS** | Captured during synthesis and exposed via `/api/analytics` endpoints. |
| **IV. Headless Matplotlib Visualization** | Matplotlib decoupled from event loops (`matplotlib.use('Agg')`) | **PASS** | Visual dashboards rendered to `io.BytesIO` buffers and streamed as PNGs. |
| **V. Test-First Discipline** | Deterministic, offline unit & integration tests with mocks | **PASS** | Comprehensive mocked test suite verifying API contracts and core domain logic. |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-fullstack-web-player/
├── plan.md              # Implementation plan (this document)
├── research.md          # Phase 0 architectural decisions and research
├── data-model.md        # Phase 1 data entities, Pydantic schemas, and TS interfaces
├── quickstart.md        # Phase 1 runnable verification guide
├── contracts/           # Phase 1 interface contracts
│   ├── rest-api-endpoints.md
│   └── frontend-components.md
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code Layout

```text
# Tier 1: Python Core Engine
src/core/
├── ingestion/           # Document loader, rule-based tokenizer, clause splitter
├── tts/                 # Edge-TTS adapter, OpenAI adapter, TTS factory, base protocol
├── storage/             # SQLAlchemy engine pool, migrations DDL, SQL repositories
├── models/              # Book, BookSentence, Bookmark, ReadingSession, NetworkMetric
├── player/              # LookaheadBuffer, AudioCacheManager, SessionTracker
├── analytics/           # Headless Matplotlib dashboard chart generators
├── telemetry/           # NetworkProbe, TelemetryCollector
└── config.py            # Centralized Pydantic settings

# Tier 2: Flask REST API
src/api/
├── app.py               # Flask application factory, CORS setup, error handlers
├── routes/              # Modular Blueprints
│   ├── books.py         # /api/books (list, ingest, sentences)
│   ├── player.py        # /api (audio stream, bookmarks, sessions)
│   └── analytics.py     # /api/analytics (summary metrics, chart PNG streams)
└── schemas/             # Pydantic request & response validation schemas
    ├── book_schemas.py
    ├── player_schemas.py
    └── analytics_schemas.py

# Tier 3: React SPA Frontend
frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
└── src/
    ├── api/             # Typed API clients (client.ts, booksApi.ts, playerApi.ts, analyticsApi.ts)
    ├── hooks/           # useAudioPlayer.ts, useBookCatalog.ts, useDashboard.ts
    ├── components/
    │   ├── Navbar/      # Navigation header
    │   ├── Player/      # SentenceList, PlayerControls, ProgressBar
    │   ├── BookUploader/# FileDropZone, UploadModal
    │   ├── Dashboard/   # MetricCard, ChartViewer
    │   └── common/      # Reusable UI primitives
    ├── pages/
    │   ├── LibraryPage.tsx
    │   ├── PlayerPage.tsx
    │   └── DashboardPage.tsx
    ├── types/           # book.ts, player.ts, analytics.ts
    ├── App.tsx
    └── main.tsx

# Tests
tests/
├── unit/                # Core engine & schema unit tests
├── integration/         # API endpoint & database integration tests
└── conftest.py          # Shared test fixtures & mocks
```

**Structure Decision**: Web application layout strictly separating `src/core/` (backend domain), `src/api/` (HTTP service), and `frontend/` (React SPA).

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| *None* | All designs strictly follow the Constitution without architecture violations. | N/A |

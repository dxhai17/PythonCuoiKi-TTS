# Feature Specification: Decoupled Full-Stack Web Player

**Feature Branch**: `feature/002-fullstack-web-app`

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "Build a decoupled full-stack web application for the Smart Audiobook Reader consisting of three strictly separated tiers: 1. Python Core Engine (in src/core): Domain logic for book ingestion, chunking, Edge-TTS synthesis, SQLAlchemy MySQL persistence, and headless Matplotlib dashboard generation. 2. Flask REST API (in src/api): Modular Blueprint-based HTTP layer with CORS, request validation schemas, and audio streaming endpoints. No business logic directly embedded in routes. 3. React SPA Frontend (in frontend): Vite-based component architecture with separated API clients, custom audio player hooks, modular UI components (Player, BookUploader, Dashboard), and dedicated pages. No monolithic files allowed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Web Audio Playback & Real-Time Sentence Synchronization (Priority: P1)

As a listener using a web browser, I want to open an audiobook, stream high-fidelity synthesized speech sentence-by-sentence, and visually follow along with real-time sentence highlighting so that I can listen and read simultaneously with full playback control.

**Why this priority**: Core value delivery. Listening with sentence-level visual feedback and interactive playback controls is the primary reason users interact with the application.

**Independent Test**: Ingest a book, navigate to `http://localhost:5173/play/1`, click Play, and verify audio plays within 1.5s while the currently spoken sentence is highlighted and the next sentence is pre-fetched.

**Acceptance Scenarios**:

1. **Given** a cataloged book with indexed sentences, **When** the user clicks "Play", **Then** the browser begins streaming audio for the current sentence within 1.5 seconds and visually highlights the matching text line.
2. **Given** active speech playback, **When** the user presses `[Space]` or clicks the Pause button, **Then** audio pauses immediately and active reading duration tracking halts.
3. **Given** active speech playback, **When** the user clicks "Next Sentence" or presses the Right Arrow key, **Then** playback advances to the subsequent sentence, pre-fetches upcoming audio in the background, and updates highlighted text.
4. **Given** active speech playback, **When** the user adjusts the speed slider between 0.7x and 2.0x, **Then** subsequent synthesized audio sentences adapt to the new rate.

---

### User Story 2 - Web Document Ingestion & Library Cataloging (Priority: P1)

As an audiobook reader, I want to upload text (`.txt`) and Markdown (`.md`) files through a web interface, provide metadata (title, author), and immediately see the book cataloged with total chapters, sentences, and words.

**Why this priority**: Required for book acquisition and content management. Enables users to load custom reading material without terminal access.

**Independent Test**: Navigate to the Library page (`/`), drag and drop a 50KB text file into the `BookUploader` component, fill title and author, submit, and verify the book appears in the library grid within 3 seconds.

**Acceptance Scenarios**:

1. **Given** a user on the Library page, **When** they drag-and-drop a valid `.txt` or `.md` file and submit, **Then** the backend parses chapters, segments sentences with 35-word clause splitting, records content hashes, and returns a catalog card showing total sentences and word count.
2. **Given** a user attempting to upload a file with an unsupported extension (e.g., `.pdf` or `.exe`), **When** they drop the file, **Then** the UI rejects the upload with an informative validation error before dispatching an HTTP request.
3. **Given** a document that has already been ingested with the same content hash, **When** submitted again, **Then** the system detects the duplicate and directs the user to the existing catalog entry without creating duplicate records.

---

### User Story 3 - Session Resumption & Persistent Bookmark Tracking (Priority: P2)

As a returning reader, I want my exact sentence position and completion percentage to persist automatically so that when I reload the page or return days later, I can resume reading exactly where I left off without manual searching.

**Why this priority**: High user convenience and retention. Eliminates lost progress when navigating away or closing browser tabs.

**Independent Test**: Play 5 sentences of a book, close the browser tab, reopen `/play/<book_id>`, and verify the player automatically positions at sentence 6 with accurate completion percentage.

**Acceptance Scenarios**:

1. **Given** a playback session where the user has listened to several sentences, **When** the user navigates away or closes the tab, **Then** the frontend syncs the bookmark position and session duration to the backend.
2. **Given** a book with a saved bookmark, **When** the user opens the player for that book, **Then** the player restores the exact bookmarked sentence and completion percentage.
3. **Given** a completed reading session, **When** the session ends, **Then** a session record is saved storing active duration (seconds), words read, and sentences read.

---

### User Story 4 - Visual Analytics & Latency Telemetry Dashboard (Priority: P3)

As a reader and system administrator, I want to view a visual analytics dashboard displaying my personal listening habits alongside technical latency metrics (synthesis speed, LAN, and Tailscale roundtrip latency) so that I can track my reading progress and verify network performance.

**Why this priority**: Fulfills Constitution Principle III & IV (Observability and Headless Matplotlib Dashboards) and provides analytical insight into reading speed and network quality.

**Independent Test**: Open the Dashboard page (`/dashboard`), verify that daily listening minutes, weekly trend charts, total words absorbed, average TTS generation latency, and LAN/Tailscale ping metrics are displayed cleanly.

**Acceptance Scenarios**:

1. **Given** recorded reading sessions and network metrics in the database, **When** the user navigates to `/dashboard`, **Then** the page displays high-contrast visual charts showing weekly listening trend and technical latency distributions.
2. **Given** the dashboard view, **When** the user switches the time filter (e.g., 7 days vs 30 days), **Then** charts and aggregated summary metrics refresh dynamically.

---

### Edge Cases

- **Audio Playback Interruption**: What happens when network connectivity to the speech synthesis API drops mid-book? The frontend displays a temporary buffering indicator, attempts up to 2 retries with exponential backoff, and alerts the user if the server remains unreachable without crashing the UI.
- **Oversized / Malformed Files**: How does the system handle an uploaded file larger than 10MB or containing binary characters? The API schema validation rejects files exceeding the size limit with HTTP 413, and the reader sanitizes non-UTF8 characters.
- **Rapid Navigation / Seeking**: What happens when a user clicks the skip button 5 times in rapid succession? Previous unplayed audio requests are aborted, lookahead buffer discards stale sentence pre-fetches, and buffering focuses immediately on the target sentence index.
- **Simultaneous Tab Playback**: What happens if a user opens the same book in two browser tabs? Each tab maintains local audio playback state; bookmark synchronization updates with the latest timestamp.

## Requirements *(mandatory)*

### Functional Requirements

#### Core Engine Layer (`src/core`)
- **FR-001**: System MUST encapsulate all domain models, document parsing, clause-boundary sub-segmentation, and content hashing within `src/core/ingestion`.
- **FR-002**: System MUST synthesize speech sentence-by-sentence via pluggable providers (Edge-TTS default, optional OpenAI) with local disk caching within `src/core/tts`.
- **FR-003**: System MUST execute all database operations using parameterized queries, SQLAlchemy connection pooling, and migrations within `src/core/storage`.
- **FR-004**: System MUST generate high-contrast visual dashboards headlessly using Matplotlib (`matplotlib.use('Agg')`) without GUI event loop binding within `src/core/analytics`.
- **FR-005**: System MUST measure TTS generation latency and probe LAN and Tailscale ping latency non-blockingly within `src/core/telemetry`.

#### REST API Layer (`src/api`)
- **FR-006**: System MUST organize HTTP endpoints into modular Flask Blueprints (`books_bp`, `player_bp`, `analytics_bp`) without business logic embedded in route handlers.
- **FR-007**: System MUST configure Cross-Origin Resource Sharing (CORS) to allow requests from the React SPA development and production origins.
- **FR-008**: System MUST validate all incoming HTTP request bodies and query parameters using explicit Pydantic schemas, returning structured HTTP 400 errors for invalid inputs.
- **FR-009**: System MUST serve sentence audio streams via discrete sentence endpoints (`GET /api/audio/<book_id>/<sentence_idx>`), allowing the frontend `useAudioPlayer` hook to execute client-side lookahead audio buffering, instant sentence skipping, sentence-level visual text highlighting, and standard browser caching.
- **FR-010**: System MUST expose visual Matplotlib charts and summary metrics via a dual presentation approach: headless Matplotlib generated binary PNG image endpoints (`GET /api/analytics/charts/listening-trends.png` and `GET /api/analytics/charts/latency-metrics.png`) for publication-grade visual charts, combined with structured JSON endpoints (`GET /api/analytics/summary`) for responsive numeric metric cards.

#### React SPA Frontend Layer (`frontend`)
- **FR-011**: System MUST be scaffolded with Vite + React + TypeScript with strict separation between API clients, custom hooks, reusable components, and route pages.
- **FR-012**: System MUST provide dedicated route pages: Library (`/`), Player (`/play/:bookId`), and Dashboard (`/dashboard`).
- **FR-013**: System MUST encapsulate audio playback, buffering, speed control, and sentence tracking in a custom hook (`useAudioPlayer`).
- **FR-014**: System MUST provide a `BookUploader` component supporting drag-and-drop file ingestion with real-time validation and progress feedback.
- **FR-015**: No frontend file may exceed 250 lines of code; monolithic presentation or business components are strictly prohibited.

### Key Entities *(include if feature involves data)*

- **Book**: Represents cataloged reading material. Key attributes: `id`, `title`, `author`, `source_path`, `content_hash`, `total_chapters`, `total_sentences`, `total_words`, `created_at`.
- **BookSentence**: Represents an indexed sentence chunk. Key attributes: `id`, `book_id`, `chapter_index`, `sentence_index`, `text_content`, `word_count`, `content_hash`, `cached_audio_path`.
- **Bookmark**: Tracks user reading position. Key attributes: `id`, `book_id`, `current_chapter`, `current_sentence_index`, `completion_percentage`, `last_read_at`.
- **ReadingSession**: Records listening duration and volume. Key attributes: `id`, `book_id`, `start_time`, `end_time`, `duration_seconds`, `sentences_read`, `words_read`.
- **NetworkMetric**: Records operational and network performance. Key attributes: `id`, `session_id`, `sentence_index`, `response_time_seconds`, `lan_ping_ms`, `tailscale_ping_ms`, `status`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can upload a 100KB text document and view it cataloged and ready for playback in under 3.0 seconds.
- **SC-002**: First audio sentence playback commences within 1.5 seconds of clicking Play in the browser.
- **SC-003**: Seamless audio transition between consecutive sentences occurs with less than 200ms of inter-sentence silence due to lookahead pre-fetching.
- **SC-004**: Exact bookmark sentence position and completion percentage restore with 100% fidelity upon page reload.
- **SC-005**: Visual analytics dashboard charts generate and load in under 1.0 second on local server environments.
- **SC-006**: 100% of malformed or invalid client requests receive deterministic JSON error responses without uncaught 500 server crashes.
- **SC-007**: Separation of concerns test: Zero domain or database logic imports exist inside `src/api` route functions (verified via automated architecture/import linting).

## Assumptions

- **Localhost Deployment**: The Flask backend runs on `http://localhost:5000` and the React Vite dev server runs on `http://localhost:5173` with CORS enabled or Vite proxy configured.
- **Browser Audio Capability**: Users access the application via modern desktop or mobile browsers supporting HTML5 Audio and standard audio codecs (MP3/WAV).
- **Single-User Local Profile**: Authentication and multi-user login are out of scope for this version; bookmarks and sessions attach to the local database profile.
- **Speech Synthesis Engine**: Default voice synthesis uses Microsoft Edge-TTS without requiring third-party cloud API keys or payments.

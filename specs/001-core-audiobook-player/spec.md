# Feature Specification: Core Audiobook Ingestion, Session Tracking, and Audio Player

**Feature Branch**: `001-core-audiobook-player`

**Created**: 2026-11-20

**Status**: Draft

**Input**: User description: "Build core audiobook ingestion, MySQL session tracking, and TTS API player"

## Clarifications

### Session 2026-11-20

- Q: Which speech synthesis provider strategy should be used as the default engine for audio playback? → A: Pluggable provider adapter with Microsoft Edge-TTS as the default (zero-cost, no API key required), with support for OpenAI TTS and Google Cloud TTS when API credentials are configured.
- Q: Should synthesized sentence audio files be cached on local disk for subsequent playback sessions? → A: Persistent local disk cache (keyed by content hash/sentence index) with instant reuse on replay and configurable cache clearing.
- Q: How should the user interact with and control audio playback during an active reading session? → A: Interactive Terminal UI with live sentence display and real-time hotkeys (Space for pause/resume, Left/Right arrows for sentence skipping, Up/Down arrows for speed adjustment, Q to exit & persist progress).
- Q: How should target host addresses for measuring LAN and Tailscale network latency be configured? → A: Configurable via environment variables (LAN_PING_HOST and TAILSCALE_PING_HOST in .env) with sensible fallback defaults (local gateway and Tailscale MagicDNS 100.100.100.100).
- Q: How should the ingestion engine segment long run-on sentences or paragraphs that lack standard sentence-ending punctuation? → A: Automatically split on clause boundaries (semicolons, colons, dashes, commas) when a segment exceeds 35 words to preserve natural cadence and prevent buffering delays.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Text Ingestion and Library Cataloging (Priority: P1)

As a listener/learner, I want to import written text and books into my personal library so that they are structured into readable chapters and sentences ready for audio narration.

**Why this priority**: Ingestion and structured text representation form the foundational requirement of the system. Without successfully cataloging and segmenting books, no speech synthesis or session tracking is possible.

**Independent Test**: Can be fully tested by importing a sample plain text or markdown document into the system; verify that the book is cataloged with title, total word count, total sentence count, and cleanly partitioned sentences.

**Acceptance Scenarios**:

1. **Given** a valid text file containing structured content, **When** the user imports the file into the reader, **Then** the system registers the book in the library, calculates word count, segments the text into indexed chapters and sentences, and reports successful ingestion.
2. **Given** an empty, corrupted, or unsupported file, **When** the user attempts to ingest it, **Then** the system rejects the file with an actionable, user-friendly error message without altering the library state.
3. **Given** a book that has already been ingested, **When** the user imports the same book again, **Then** the system detects the existing record and allows the user to update or keep the existing catalog item without duplication.

---

### User Story 2 - Real-Time Audio Playback and Navigation (Priority: P1)

As a listener, I want to play, pause, resume, and navigate through the audio narration of any book in my library with responsive controls so that I can listen comfortably and control my learning pace.

**Why this priority**: Audio playback is the primary end-user value proposition. Users must be able to listen smoothly with standard audio playback controls and adjust reading speed.

**Independent Test**: Can be fully tested by selecting any cataloged book, triggering playback, testing pause/resume/stop, skipping forward and backward across sentences, and altering playback speed; verify that audio plays accurately and responsiveness is instantaneous.

**Acceptance Scenarios**:

1. **Given** an ingested book in the library, **When** the user initiates playback, **Then** the system opens an interactive terminal UI displaying the current sentence, synthesizes speech, streams audio output, and pre-buffers the next sentence for seamless listening.
2. **Given** active audio narration in the terminal UI, **When** the user presses Space, **Then** audio playback immediately pauses at the current sentence boundary and the UI updates status to Paused.
3. **Given** paused narration in the terminal UI, **When** the user presses Space, **Then** playback resumes seamlessly from the current sentence without repeating previously completed sentences.
4. **Given** active or paused playback in the terminal UI, **When** the user presses Right or Left arrow keys, **Then** playback navigates to the next or previous sentence index and updates the current listening display immediately.
5. **Given** audio playback, **When** the user adjusts the playback speed with Up or Down arrow keys (e.g., 0.75x to 2.0x), **Then** subsequent audio renders at the selected tempo without unnatural pitch distortion.
6. **Given** an active session, **When** the user presses Q, **Then** playback cleanly terminates, the bookmark is updated, and the reading session metrics are saved.

---

### User Story 3 - Reading Session Tracking and Bookmark Resumption (Priority: P2)

As a learner, I want the system to automatically track my reading sessions (listening time, words absorbed) and bookmark my exact progress so that I can resume exactly where I stopped and monitor my study habits over time.

**Why this priority**: Study continuity and self-monitoring are critical for regular readers. Losing one's position in a book creates friction, and tracking study metrics supports habit building.

**Independent Test**: Can be fully tested by listening to an ingested book for several minutes, pausing or closing the session, and inspecting the recorded session metrics and saved bookmark; verify that opening the book restores the exact sentence position.

**Acceptance Scenarios**:

1. **Given** an active listening session, **When** the user pauses, stops, or exits the reader, **Then** the system persists a session record containing start time, end time, total active duration (seconds), sentence count, and total words absorbed.
2. **Given** an active listening session, **When** the listening position advances, **Then** the system automatically updates the persistent bookmark for that book with the current chapter, sentence index, and overall completion percentage.
3. **Given** a book with a saved bookmark, **When** the user reopens the book, **Then** the system prompts or defaults to resume playback at the exact bookmarked sentence.

---

### User Story 4 - Audio Synthesis Performance and Latency Telemetry (Priority: P3)

As a user and system administrator, I want the system to measure and record speech synthesis latency and network responsiveness for each sentence so that I have visibility into audio generation health and buffering stability.

**Why this priority**: Speech synthesis relies on network-connected generation services. Monitoring sentence response times and latency is essential for diagnosing buffering delays or degraded listening experiences.

**Independent Test**: Can be fully tested by running a continuous playback session across multiple sentences; verify that response times (in seconds per sentence) and round-trip network metrics are accurately logged alongside each session.

**Acceptance Scenarios**:

1. **Given** an audio synthesis request for a sentence, **When** the generation completes, **Then** the system records the response time in seconds alongside the session telemetry.
2. **Given** network latency or temporary speech service unavailability, **When** an audio generation request exceeds typical latency or fails, **Then** the system retries gracefully, alerts the user if buffering runs out, and logs the degraded metric without crashing or losing session progress.

---

### Edge Cases

- **Extremely Long Sentences**: When a sentence contains unusually high word counts (>35 words without terminal punctuation), the ingestion engine automatically splits the text at clause boundaries (semicolons, colons, em-dashes, commas) so that speech synthesis does not exceed payload limits or create awkward delays.
- **Network Interruption During Playback**: If the network connection drops while listening, how does the system behave when buffered sentences run out? (System should pause gracefully, notify user, and retain current bookmark).
- **Abrupt Application Termination**: If the application process is terminated unexpectedly, how is progress protected? (Bookmarks should be updated continuously or flushed periodically so no more than one sentence of progress is lost).
- **Special Characters and Punctuation**: How does the system handle non-standard characters, mathematical formulas, or unpunctuated text? (Text pre-processing must normalize whitespace, strip unpronounceable formatting artifacts, and ensure clean sentence segmentation).
- **Book Completion**: When a user reaches the final sentence of a book, how is the session finalized? (Bookmark records 100% completion, session logs final word totals, and playback stops cleanly).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow users to ingest books from plain text (`.txt`) and Markdown (`.md`) file formats into the persistent library.
- **FR-002**: The system MUST parse ingested book content into structured chapters, sections, and sequentially indexed sentences, automatically sub-segmenting run-on text at clause boundaries (semicolons, colons, dashes, commas) when any segment exceeds 35 words.
- **FR-003**: The system MUST compute and store catalog metadata for each book, including title, source location, total word count, total sentence count, and creation timestamp.
- **FR-004**: The system MUST synthesize speech for text sentences using a pluggable provider interface, defaulting to Microsoft Edge-TTS for zero-cost operation and supporting OpenAI TTS / Google Cloud TTS when configured, streaming audio output to the user's audio device.
- **FR-005**: The system MUST provide an interactive terminal UI during playback displaying the current sentence, book progress, and listening statistics, supporting real-time single-keystroke controls: Play/Pause (Space), Next/Previous Sentence (Right/Left Arrows), Speed Adjustment (Up/Down Arrows), and Stop/Save (Q).
- **FR-006**: The system MUST maintain a lookahead audio buffer and persist synthesized sentence audio to a local disk cache (keyed by content hash and book/sentence index), allowing instantaneous replay without repeated network requests or redundant API consumption.
- **FR-007**: The system MUST automatically maintain a persistent bookmark per book, recording the current chapter, current sentence index, and overall completion percentage.
- **FR-008**: The system MUST automatically resume playback from the bookmarked sentence when a user re-opens any book.
- **FR-009**: The system MUST record reading session history, tracking session start time, end time, active listening duration (seconds), sentences consumed, and total words absorbed.
- **FR-010**: The system MUST measure and log synthesis performance and network telemetry per sentence—including speech generation response time (seconds), LAN ping latency (ms), and Tailscale mesh latency (ms)—using target hosts configured via environment settings (with local gateway and Tailscale MagicDNS 100.100.100.100 fallbacks).
- **FR-011**: The system MUST handle speech synthesis service failures and network drops gracefully, notifying the user without application crashes or loss of persisted progress.

### Key Entities

- **Book**: Represents a distinct reading work in the library. Key attributes: unique identifier, title, source file reference, total word count, total sentence count, total chapters, creation timestamp, last accessed timestamp.
- **Sentence / Text Segment**: Represents an individual atomic unit of reading and speech synthesis within a book. Key attributes: book reference, chapter index, sentence index, text content, content hash, word count, cached audio file path (if synthesized).
- **Bookmark**: Represents the user's latest reading position in a book. Key attributes: book reference, current chapter index, current sentence index, completion percentage, updated timestamp.
- **Reading Session**: Represents a discrete listening study period. Key attributes: unique session identifier, book reference, start timestamp, end timestamp, active duration (seconds), sentences read, words absorbed.
- **Network & Synthesis Telemetry**: Represents operational performance measurements during reading sessions. Key attributes: session reference, sentence index, response time (seconds), LAN latency (milliseconds), Tailscale latency (milliseconds), timestamp, status code/indicator.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A 100,000-word book is fully ingested, parsed, and cataloged into the library in under 5 seconds.
- **SC-002**: Audio playback commences in under 2 seconds after the user triggers "Play" on any ingested book under normal network conditions.
- **SC-003**: The audio transition between consecutive sentences exhibits less than 150 milliseconds of perceptible delay during normal buffered playback.
- **SC-004**: Reading bookmark position is maintained with 100% accuracy, restoring the exact sentence across 100% of tested application restarts.
- **SC-005**: Reading sessions record duration and absorbed word counts with 100% data integrity, with zero unrecorded sessions upon normal or graceful termination.
- **SC-006**: In the event of a network outage or speech synthesis service failure, the system halts gracefully and displays an informative notification within 3 seconds, losing zero prior bookmark progress.

## Assumptions

- **File Formats**: The initial core version strictly targets plain text (`.txt`) and Markdown (`.md`) inputs; extraction from PDF or complex EPUB layouts is deferred to future format adapters.
- **Connectivity & Speech Provider**: High-quality speech synthesis operates via a pluggable engine architecture defaulting to Microsoft Edge-TTS (requiring internet connectivity but no paid API key), with configurable support for OpenAI TTS or Google Cloud TTS.
- **Audio Output**: Playback is directed to the primary audio output device configured on the operating system.
- **Audio Caching**: Synthesized audio files are stored locally in an audio cache directory, enabling instant replay and reducing network load.
- **Network Telemetry Targets**: Network round-trip pings for LAN and Tailscale use host addresses configured via environment variables with fallback defaults.
- **User Profile**: Single-user local profile is assumed for initial catalog and session management; multi-user tenancy is out of scope for the core version.
- **Local Persistence**: A reliable local relational database is available for storing books, bookmarks, sessions, and operational metrics.

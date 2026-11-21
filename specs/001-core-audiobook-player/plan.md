# Implementation Plan: Core Audiobook Ingestion, Session Tracking, and Audio Player

**Branch**: `001-core-audiobook-player` | **Date**: 2026-11-20 | **Spec**: [spec.md](file:///home/hai/Du_lieu_hoc_tap/Project/BTL_Python_Project/StudyLab/specs/001-core-audiobook-player/spec.md)

**Input**: Feature specification from `specs/001-core-audiobook-player/spec.md`

## Summary

Build the foundational core of the Smart Audiobook Reader:
1. **Ingestion Engine**: Ingest and tokenize `.txt` and `.md` documents into structured chapters and indexed sentences with a 35-word clause boundary sub-segmentation rule.
2. **Pluggable TTS Adapter**: Synthesize speech sentence-by-sentence using a pluggable provider interface defaulting to Microsoft Edge-TTS (zero-cost, no API key), with disk-based audio caching.
3. **Audio Player & Interactive TUI**: Lookahead background buffering using `pygame.mixer` coupled with an interactive `rich`/`readchar` terminal UI offering real-time progress, sentence text display, and single-keystroke controls (`Space`, Arrows, `q`).
4. **Relational Persistence**: MySQL connection pool via SQLAlchemy executing parameterized queries to track `books`, `book_sentences`, `bookmarks`, `reading_sessions`, and `network_metrics` (API response times, LAN ping, Tailscale ping).

---

## Technical Context

**Language/Version**: Python 3.11+ (modern typing: `list[str]`, `dict[str, Any]`, `X | None`)

**Primary Dependencies**:
- `edge-tts`: Free neural cloud speech synthesis (default engine)
- `pygame`: Cross-platform audio playback and mixer controls
- `SQLAlchemy` & `PyMySQL`: Connection pooling (`create_engine`) and parameterized SQL query execution
- `rich`: Terminal UI rendering, progress bars, tables, and live views
- `readchar`: Raw, non-blocking single-keystroke input handling
- `pydantic`: Schema validation and serialization
- `python-dotenv`: Environment configuration loading

**Storage**:
- MySQL 8.0+ / MariaDB 10.5+ for books, sentences, bookmarks, sessions, and telemetry
- Local filesystem (`.studylab/cache/audio/`) for content-hashed MP3 audio segments

**Testing**: `pytest`, `pytest-mock` (strictly 100% offline; all TTS and ping calls mocked)

**Target Platform**: Linux (x86_64 / aarch64), macOS, and POSIX environments

**Project Type**: CLI application with Interactive Terminal UI (TUI) and decoupled library modules

**Performance Goals**:
- Ingestion of 100,000 words in <5 seconds (SC-001)
- Audio playback starts within 2 seconds of pressing Play (SC-002)
- Audio transition between sentences <150ms perceptible delay (SC-003)
- 100% bookmark restoration accuracy on restart (SC-004)

**Constraints**:
- Zero paid API key requirement out-of-the-box (free Edge-TTS default)
- No cloud model training infrastructure
- Parameterized SQL queries only (no SQL injection)
- Graceful degradation if external network drops

**Scale/Scope**: Single-user local profile, personal library of hundreds of books, tens of thousands of sentences

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Compliance Status | Architectural Validation |
|---|---|---|
| **I. Library-First & Modular Architecture** | **PASS** | Domain logic decoupled into isolated modules (`ingestion`, `tts`, `player`, `storage`, `telemetry`); no cyclic dependencies. |
| **II. Test-First & Automated Verification** | **PASS** | `pytest` test suite with `MockTTSProvider` and offline repository tests; 100% network isolation during tests. |
| **III. CLI & Programmatic Interoperability** | **PASS** | Full CLI command schema with structured `--json` outputs, standard text in/out, and explicit exit codes. |
| **IV. Type Safety & Explicit Contracts** | **PASS** | Strict PEP 484/526 typing across all modules; Pydantic and dataclass models for all domain entities. |
| **V. Defensive Design & Observability** | **PASS** | Structured logging, explicit exception handling, sentence latency and LAN/Tailscale ping telemetry, zero committed secrets. |
| **User Rule: MySQL Connection Pooling** | **PASS** | SQLAlchemy engine configured with `pool_size=5`, `max_overflow=10`, `pool_pre_ping=True`. |
| **User Rule: No Cloud Model Training** | **PASS** | Third-party inference APIs only (Edge-TTS, OpenAI); no training infrastructure. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-core-audiobook-player/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Phase 0 architectural & technical decisions
├── data-model.md        # Relational schema & entity definitions
├── quickstart.md        # End-to-end verification and run guide
├── contracts/           # Interface contracts
│   ├── cli-interface.md
│   ├── tts-provider-contract.md
│   └── storage-contract.md
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code Layout

```text
src/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py              # CLI entrypoint & subcommands (ingest, list, play, metrics)
│   └── player_view.py       # Rich/readchar Terminal UI
├── ingestion/
│   ├── __init__.py
│   ├── parser.py            # Sentence & chapter tokenizer (35-word clause split)
│   └── reader.py            # File loading & text normalization
├── models/
│   ├── __init__.py
│   ├── book.py              # Book, BookSentence, Bookmark dataclasses
│   ├── session.py           # ReadingSession dataclass
│   └── telemetry.py         # NetworkMetric dataclass
├── player/
│   ├── __init__.py
│   ├── audio_player.py      # Pygame mixer audio playback controller
│   └── buffer_manager.py    # Lookahead pre-fetch queue & cache coordinator
├── storage/
│   ├── __init__.py
│   ├── db.py                # SQLAlchemy pooled engine & transaction helper
│   ├── migrations.py        # DDL table creation scripts
│   └── repositories.py      # Parameterized repository implementations
├── telemetry/
│   ├── __init__.py
│   ├── network_probe.py     # LAN & Tailscale ping latency probe
│   └── collector.py         # Metrics aggregator
└── tts/
    ├── __init__.py
    ├── base.py              # Abstract TTSProvider protocol & AudioSynthesisResult
    ├── edge_tts_adapter.py  # Edge-TTS implementation (default)
    ├── openai_adapter.py    # OpenAI TTS implementation (optional)
    └── factory.py           # Provider resolver / injector

tests/
├── conftest.py              # Shared test fixtures & MockTTSProvider
├── unit/
│   ├── test_parser.py       # Sentence splitting & 35-word clause test
│   ├── test_tts_provider.py # Mock TTS synthesis tests
│   ├── test_buffer.py       # Lookahead buffer queue tests
│   └── test_telemetry.py    # Ping probe tests
└── integration/
    ├── test_storage.py      # Repository tests with test database
    └── test_cli.py          # CLI command integration tests
```

**Structure Decision**: Single project modular layout cleanly organizing domain ingestion, playback, telemetry, persistence, and CLI presentation.

---

## Complexity Tracking

> No violations or unnecessary abstractions introduced. All components strictly adhere to project constitution principles and user rules.

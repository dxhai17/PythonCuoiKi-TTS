# Research & Architectural Decisions: Core Audiobook Ingestion, Session Tracking, and TTS Player

**Feature**: `001-core-audiobook-player`
**Date**: 2026-11-20
**Status**: Completed

## 1. Text Ingestion & Sentence Segmentation Architecture

- **Decision**: Implement a custom lightweight rule-based sentence tokenizer in `src/ingestion/parser.py` combining regex punctuation boundaries (`.`, `!`, `?`, `\n\n`) with an abbreviation filter and a 35-word clause sub-segmentation rule (`:`, `;`, `—`, `,`).
- **Rationale**:
  - Processing 100,000 words must finish in under 5 seconds (SC-001). Heavy NLP frameworks (spaCy, Stanza) incur multi-second cold-start initialization and require downloading external multi-megabyte language models.
  - A deterministic rule-based tokenizer achieves >50,000 words/second in pure Python, respects sentence boundaries, handles common titles/abbreviations (Mr., Dr., e.g., i.e.), and reliably applies the user-specified 35-word clause boundary splitting to prevent TTS buffer timeouts.
- **Alternatives Considered**:
  - `nltk.tokenize.sent_tokenize`: Required downloading NLTK `punkt` data files at runtime, which violates offline determinism rules in isolated test environments.
  - `spaCy`: Excessively heavy dependency (~500MB wheel + model weight downloads), unnecessarily complex for plain text and markdown.
  - Simple `str.split('.')`: Too naive; incorrectly segments numbers ("3.14"), abbreviations, and questions/exclamations.

---

## 2. Text-to-Speech (TTS) Pluggable Provider & Audio Streaming

- **Decision**: Define a formal abstract base class `TTSProvider` in `src/tts/base.py` and implement `EdgeTTSProvider` using Microsoft Edge-TTS as the primary default, accompanied by extensible stubs/adapters for `OpenAITTSProvider` and `GoogleCloudTTSProvider`.
- **Rationale**:
  - Satisfies clarification decision (Session 2026-11-20, Q1) and project constraint against cloud model training.
  - Edge-TTS is free, requires zero paid API keys, provides high-fidelity natural neural speech (e.g. `en-US-ChristopherNeural` or `vi-VN-NamMinhNeural`), and outputs standard MP3/audio streams directly.
  - A clean provider interface (`synthesize(text: str, voice: str | None, speed: float) -> AudioResult`) decouples domain reading logic from vendor SDKs and allows complete offline mocking during `pytest` test runs.
- **Alternatives Considered**:
  - Direct OpenAI SDK dependency: Forces every developer/reviewer to supply a paid OpenAI credit balance to run tests or demo the app.
  - Direct OS `pyttsx3` offline synthesis: Highly robotic voices, platform-dependent audio device crashes on Linux without `espeak`, unsuited for long audiobook listening.

---

## 3. Audio Playback, Buffering & Lookahead Queue

- **Decision**: Use `pygame.mixer` (initialized in headless/audio-only mode) managed by an asynchronous/threaded `AudioPlayer` controller in `src/player/audio_player.py`.
- **Rationale**:
  - `pygame.mixer` provides cross-platform, battle-tested MP3 playback controls: play, pause, unpause, stop, volume adjustment, and playback end-of-track detection via custom events or polling.
  - Can be decoupled from any graphical display by running with `os.environ["SDL_VIDEODRIVER"] = "dummy"` and initializing only `pygame.mixer.init()`.
  - Lookahead audio buffering is implemented via a producer-consumer background thread (`queue.Queue[SentenceAudio]`) that pre-synthesizes sentence `N+1` while sentence `N` is actively playing, satisfying the <150ms transition requirement (SC-003).
- **Alternatives Considered**:
  - Calling external system binary `ffplay` or `mpv`: Fragile dependency requiring users to have external C binaries installed on PATH; harder to capture precise sentence completion events programmatically.
  - `miniaudio`: Lower-level, requires custom streaming buffer loops and manual PCM format decoding.

---

## 4. Local Disk Audio Caching Strategy

- **Decision**: Store synthesized sentence audio in `.studylab/cache/audio/{book_id}/{sentence_hash}.mp3`. Key is generated via SHA-256 of `(sentence_text + voice_id + str(speed))`.
- **Rationale**:
  - Satisfies clarification decision (Session 2026-11-20, Q2).
  - Content hashing guarantees that identical sentences are never re-fetched even if sentence indexing shifts slightly.
  - Checking cache existence prior to dispatching network requests makes re-listening instantaneous (<10ms) and eliminates redundant network/API costs.
- **Alternatives Considered**:
  - In-memory cache only: Lost upon application quit; repeated sessions on the same chapter re-incur network calls.
  - Storing audio blobs directly in MySQL: Bloats database backups, introduces high I/O overhead on relational tables, and exceeds typical row size comfort zones.

---

## 5. MySQL Connection Pooling & Database Layer

- **Decision**: Use `SQLAlchemy` engine connection pool (`create_engine("mysql+pymysql://...", pool_pre_ping=True, pool_size=5, max_overflow=10)`) with parameterized `text(...)` SQL queries or lightweight mapped dataclasses.
- **Rationale**:
  - Satisfies project rules (MySQL with parameterized queries and connection pooling; no SQL injection vulnerabilities).
  - `PyMySQL` is pure Python (no C compiler / `mysqlclient` build toolchain dependencies on Linux/macOS).
  - SQLAlchemy connection pooling handles connection timeouts, health checks (`pool_pre_ping=True`), and thread safety across the playback and telemetry threads.
  - Raw parameterized queries preserve complete transparency over queries for `books`, `reading_sessions`, and `network_metrics`.
- **Alternatives Considered**:
  - `mysql.connector.pooling`: Less flexible error handling and lacks automatic disconnect reconnection compared to SQLAlchemy pool.
  - Heavy full ORM (e.g., complex Django ORM or deep declarative models with autoflush): Violates Principle V (Simplicity & YAGNI); adds unnecessary abstraction layers for 4 straightforward tables.

---

## 6. Interactive Terminal UI (TUI) & Event Handling

- **Decision**: Build the terminal interface using `rich.live` and `readchar` in `src/cli/player_view.py`.
- **Rationale**:
  - Satisfies clarification decision (Session 2026-11-20, Q3).
  - `rich` provides beautiful, cross-platform terminal formatting (colored panels, progress bars, status badges) with flicker-free `Live` display refreshes.
  - `readchar.readkey()` provides non-blocking, raw single-keystroke capture without requiring the user to press Enter (`Space` for pause/resume, `Left`/`Right` for skip, `Up`/`Down` for speed, `q` for quit).
- **Alternatives Considered**:
  - Standard `curses`: Highly platform-dependent, notoriously difficult to test in standard automated test runners or CI environments, easily breaks terminal state on uncaught exceptions.
  - `textual`: Full async framework that imposes heavy event loop ownership over the entire process, complicating integration with audio streaming threads.

---

## 7. Network Latency & Telemetry Probing

- **Decision**: Implement `NetworkProbe` in `src/telemetry/network_probe.py` using ICMP sockets (or TCP connect probes to target port if non-root ICMP is restricted) with a strict 500ms timeout, reading target addresses from `LAN_PING_HOST` and `TAILSCALE_PING_HOST` from `.env`.
- **Rationale**:
  - Satisfies clarification decision (Session 2026-11-20, Q4) and project rules (`network_metrics` table with response time in sec/sentence, LAN/Tailscale ping in ms).
  - TCP handshake connect time (or non-blocking ping) avoids privilege escalation issues on unprivileged Linux environments where ICMP raw sockets require root privileges.
  - Fallbacks: LAN defaults to default gateway (`192.168.1.1` or socket route discovery), Tailscale defaults to `100.100.100.100` (Tailscale MagicDNS).
- **Alternatives Considered**:
  - Spawning `ping -c 1`: Shell subprocess execution adds significant CPU overhead per sentence and is platform-specific (Windows vs Linux ping arguments).

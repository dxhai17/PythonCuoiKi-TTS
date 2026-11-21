<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- List of modified principles:
  - Added project-specific mandates for MySQL, Matplotlib, and Cloud TTS API
  - Enforced strict Zero-Cloud-Training constraint for speech synthesis
- Added sections:
  - Technical Performance & Network Latency Telemetry
- Follow-up TODOs: None
-->

# Smart Audiobook Reader Constitution

## Core Principles

### I. Modular & Decoupled Architecture
The system MUST be structured into isolated, testable modules with strict boundary contracts:
1. `ingestion`: Parsing and extracting text from ebook/document formats.
2. `tts_client`: Interfacing with third-party speech synthesis APIs, handling sentence chunking and audio streaming.
3. `storage`: MySQL schema management, repositories, connection pooling, and transactional operations.
4. `analytics`: Matplotlib dashboards, data aggregation (listening time, words absorbed), and technical telemetry.
Cyclic dependencies between these domains are strictly prohibited.
*Rationale*: Isolating external I/O (MySQL, TTS APIs) from presentation and analytics ensures testability and seamless service swapping.

### II. Cloud TTS API-First (Zero Model Training Policy)
Voice synthesis MUST strictly utilize production-ready third-party commercial APIs (e.g., OpenAI Audio, ElevenLabs, Google Cloud TTS, or Edge-TTS). 
- Local neural network training or deploying cloud GPU training infrastructure is STRICTLY PROHIBITED.
- Audio synthesis MUST be requested in sentence/paragraph chunks to minimize time-to-first-byte (TTFB).
- API credentials MUST be loaded strictly via environment variables (`.env`) and NEVER hardcoded or checked into VCS.
*Rationale*: Focuses engineering effort on user experience and reliable application logic without incurring prohibitive cloud compute costs or maintenance overhead.

### III. Comprehensive Telemetry & Observability
Every listening session and audio synthesis request MUST generate structured telemetry persisted directly to MySQL:
- User metrics: Daily and weekly listening duration (minutes) and cumulative words absorbed.
- Technical performance metrics: Average server roundtrip response time (seconds per sentence) and network latency (LAN / Tailscale ping in milliseconds).
Raw `print()` debugging statements in production modules are prohibited; standard structured logging (`logging` module) MUST be used.
*Rationale*: Real-time and historical telemetry provides transparency into network conditions and cloud API responsiveness.

### IV. Headless & Clean Matplotlib Visualization
All visualization and dashboard generation using Matplotlib MUST be decoupled from GUI rendering loops:
- Matplotlib MUST operate in headless mode (`matplotlib.use('Agg')` or equivalent) when rendering charts to files, web buffers, or desktop image canvases.
- Dashboards MUST feature clear dual-axis or multi-panel subplots separating user learning metrics (minutes listened, words read) from technical performance tables (latency, response times).
- Visual assets MUST be optimized and styled cleanly with consistent color palettes, labeled axes, and readable legends.
*Rationale*: Headless generation prevents GUI freezing and allows reuse across CLI, desktop windows, or automated reporting tasks.

### V. Test-First Discipline & External Mocking (NON-NEGOTIABLE)
Test-driven development (TDD) is mandatory. Unit and integration tests (`pytest`) MUST be written alongside domain logic:
- External network boundaries (MySQL database, TTS APIs, Tailscale/LAN ping probes) MUST be isolated via test doubles, stubs, or mock fixtures.
- Test suites MUST execute fast and pass 100% deterministically in offline environments.
*Rationale*: Mocking third-party APIs prevents unexpected billing during automated test runs and ensures predictable CI verification.

## Technology Stack & Engineering Standards
- **Runtime**: Python 3.11+ (CPython).
- **Database**: MySQL 8.0+ using connection pooling (`mysql-connector-python`, `PyMySQL`, or `SQLAlchemy`).
- **Visualization**: `matplotlib` (with `numpy`/`pandas` for data aggregation).
- **TTS Integration**: Modern REST/gRPC client SDKs with async/streaming capability.
- **Data Validation & Schemas**: `pydantic` v2 or Python standard `dataclasses`.
- **Code Quality**: PEP 8 compliance enforced by Ruff / Flake8, with explicit type hints (PEP 484).

## Development Workflow & Quality Gates
- **Specification-Driven**: Every feature MUST proceed through SpecKit stages (`/speckit-specify` ➔ `/speckit-plan` ➔ `/speckit-tasks` ➔ `/speckit-implement`).
- **Quality Gates**:
  1. Static analysis and type checking MUST pass with zero unresolved errors.
  2. The automated test suite MUST pass with 100% success rate without making live external API calls.
  3. Database migrations MUST be reproducible and version-controlled.

## Governance
This Constitution is the authoritative reference for the Smart Audiobook Reader project. Any modification requires a documented rationale, version update, and compatibility assessment across existing feature specifications.

**Version**: 1.1.0 | **Ratified**: 2026-11-20 | **Last Amended**: 2026-11-20
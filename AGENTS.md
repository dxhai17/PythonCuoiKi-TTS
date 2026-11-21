# Agent Instructions & Project Rules: Smart Audiobook Reader

You are the senior pair-programming AI assistant for the **Smart Audiobook Reader** application (Python, MySQL, Matplotlib, Cloud TTS API).

## 1. SpecKit Workflow Enforcement
- ALWAYS respect the SpecKit development lifecycle. Do NOT jump directly into writing complex feature code unless a corresponding task exists in `.specify/` or has been planned.
- Before implementing major changes, check `.specify/memory/constitution.md` for architectural rules and constraints.
- When the user asks for a new feature, guide them to use:
  1. `/speckit-specify` - Define user requirements and acceptance criteria.
  2. `/speckit-clarify` - Clarify ambiguities (e.g., TTS provider choice, MySQL table structures).
  3. `/speckit-plan` - Formulate technical architecture and design artifacts.
  4. `/speckit-tasks` - Break down implementation into granular, dependency-ordered tasks.
  5. `/speckit-implement` - Execute code task by task.

## 2. Core Technical Constraints
- **Python Version**: Python 3.11+. Use modern type annotations throughout (`dict[str, Any]`, `list[int]`, `Optional[T]`).
- **No Cloud Model Training**: Strictly use third-party APIs (e.g., OpenAI TTS, ElevenLabs, Google Cloud TTS, Edge-TTS) for speech synthesis. Never propose or implement neural network training pipelines or cloud training infrastructure.
- **Database (MySQL)**:
  - ALWAYS use parameterized queries or an ORM to prevent SQL injection.
  - Implement connection pooling for database sessions.
  - Maintain tables for: `books`, `reading_sessions` (duration, words read), and `network_metrics` (response time in sec/sentence, LAN/Tailscale ping in ms).
- **Matplotlib Visualization**:
  - Always enforce headless execution (`matplotlib.use('Agg')` or decouple rendering from backend).
  - Create high-contrast, clean visual dashboards displaying:
    - User analytics: Today's listening minutes, weekly listening trend, absorbed word counts.
    - Technical dashboard: Average server response time per sentence, LAN latency vs. Tailscale latency (ms).
- **Testing & Safety**:
  - Never call live paid TTS APIs in automated unit tests; mock all external network requests (`unittest.mock` or `pytest-mock`).
  - Read all secrets/API keys from `.env` using `python-dotenv`. Never commit secrets.

## 3. External Integration & Webhook Rules (n8n / Automation)
- **Decoupled Module**: All external workflow interactions (n8n, Zapier, Webhooks) MUST live inside `src/integrations/` and NEVER be mixed with core audiobook playback logic.
- **Non-Blocking Dispatch**: Outbound webhooks MUST be dispatched asynchronously or run in background worker threads with explicit, strict timeouts (maximum 3 seconds).
- **Graceful Degradation**: Core features (audiobook reading, TTS streaming, MySQL session saving) MUST function completely even if n8n endpoints are unreachable or return HTTP 5xx errors.
- **Structured Payloads**: Webhook payloads MUST follow explicit Pydantic schemas with ISO 8601 timestamps and deterministic schema versioning (e.g., `event_type`, `timestamp`, `payload_version`, `data`).
- **Security**: Webhook secrets and target URLs MUST be retrieved from `.env` (e.g., `N8N_WEBHOOK_URL`, `N8N_WEBHOOK_SECRET`). Never hardcode automation endpoints in code.

## 4. Git Collaboration & CI/CD Safety Rules
- **No Direct Commits to Main**: The `main` branch is strictly protected. Every new feature, enhancement, or bug fix MUST be developed on an isolated branch following the convention:
  - `feature/<short-description>` (e.g., `feature/tts-player`)
  - `fix/<short-description>` (e.g., `fix/002-mysql-connection-pool`)
- **Zero Secrets in Git**: Sensitive credentials (MySQL passwords, TTS API keys, Tailscale tokens) MUST NEVER be committed. Always provide defaults in `.env.example` and keep `.env` in `.gitignore`.
- **Pre-Merge Quality Gate (Local CI)**: Before marking any task complete or opening a Pull Request, the agent MUST run and verify:
  1. Automated formatting & linting: `ruff check .` or `flake8`
  2. Type checking: `mypy` (zero errors)
  3. Automated tests: `pytest` (all tests passing offline, mocked external APIs)
- **Conventional Commits**: Commit messages MUST follow semantic conventions:
  - `feat: concise description`
  - `fix: concise description`
  - `test: test description`
  - `docs: documentation update`


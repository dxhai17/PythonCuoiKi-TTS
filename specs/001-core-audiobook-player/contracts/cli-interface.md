# CLI Contract: Smart Audiobook Reader (`studylab`)

**Feature**: `001-core-audiobook-player`
**Date**: 2026-11-20

The `studylab` CLI is the primary programmatic and human interface for managing the audiobook library, listening to books, and inspecting operational telemetry.

All subcommands adhere to Constitution Principle III:
- Support standard input/arguments for ingress.
- Structured `--json` machine-readable output option alongside human-readable Rich formatting.
- Explicit non-zero exit codes on error with diagnostic messages on stderr.

---

## Command Matrix

| Command | Purpose | Input Arguments | Output Format | Exit Codes |
|---|---|---|---|---|
| `studylab ingest` | Parse and catalog a book | `<file_path> [--title] [--author]` | JSON / Rich Table | `0` (Success), `1` (File not found), `2` (Parse error) |
| `studylab list` | List all cataloged books | `[--limit] [--offset] [--json]` | JSON / Rich Table | `0` (Success), `3` (DB Error) |
| `studylab play` | Start/resume audiobook playback | `<book_id> [--sentence] [--speed] [--voice]` | Interactive TUI | `0` (Clean quit), `4` (Book not found), `5` (Audio error) |
| `studylab metrics` | View session and telemetry stats | `[--book-id] [--days] [--json]` | JSON / Rich Table | `0` (Success), `3` (DB Error) |

---

## Command Specifications

### 1. `studylab ingest <file_path>`

Imports a plain text (`.txt`) or Markdown (`.md`) file, parses chapters/sentences, and stores them in MySQL.

- **Options**:
  - `--title <text>`: Custom title (defaults to filename).
  - `--author <text>`: Author name (defaults to "Unknown").
  - `--json`: Output machine-readable JSON.
- **Example Usage**:
  ```bash
  python -m src.cli.main ingest ./sample.txt --title "The Art of War" --author "Sun Tzu"
  ```
- **JSON Output Sample**:
  ```json
  {
    "status": "success",
    "book_id": 1,
    "title": "The Art of War",
    "total_chapters": 13,
    "total_sentences": 420,
    "total_words": 12850
  }
  ```

---

### 2. `studylab list`

Lists all ingested books with their current bookmark progress.

- **Options**:
  - `--json`: Return books array as JSON.
- **Example Usage**:
  ```bash
  python -m src.cli.main list
  ```
- **JSON Output Sample**:
  ```json
  [
    {
      "id": 1,
      "title": "The Art of War",
      "author": "Sun Tzu",
      "total_words": 12850,
      "current_sentence_index": 45,
      "completion_percentage": 10.7,
      "last_read_at": "2026-11-20T11:00:00"
    }
  ]
  ```

---

### 3. `studylab play <book_id>`

Launches the interactive Terminal UI (TUI) to listen to the book, automatically resuming from the saved bookmark.

- **Options**:
  - `--sentence <index>`: Override bookmark and start from specific sentence index.
  - `--speed <float>`: Playback speed (0.75 to 2.0, default 1.0).
  - `--voice <name>`: Voice identifier for speech engine.
- **TUI Keybindings**:
  - `[Space]`: Toggle Play / Pause.
  - `[Right Arrow]`: Skip to next sentence.
  - `[Left Arrow]`: Return to previous sentence.
  - `[Up Arrow]`: Increase playback speed by +0.1x.
  - `[Down Arrow]`: Decrease playback speed by -0.1x.
  - `[q]`: Quit session, flush metrics, and save bookmark.
- **Example Usage**:
  ```bash
  python -m src.cli.main play 1
  ```

---

### 4. `studylab metrics`

Displays aggregated study session logs and network latency statistics.

- **Options**:
  - `--book-id <id>`: Filter metrics for a specific book.
  - `--days <int>`: Scope to past N days (default 7).
  - `--json`: Output metrics as JSON.
- **JSON Output Sample**:
  ```json
  {
    "total_listening_minutes": 145.5,
    "total_words_absorbed": 18200,
    "total_sessions": 6,
    "avg_sentence_response_time_sec": 0.42,
    "avg_lan_ping_ms": 2.4,
    "avg_tailscale_ping_ms": 28.6
  }
  ```

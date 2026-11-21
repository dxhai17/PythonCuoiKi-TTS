# Quickstart & Verification Guide: Core Audiobook Ingestion, Session Tracking, and Audio Player

**Feature**: `001-core-audiobook-player`
**Date**: 2026-11-20

This guide provides end-to-end procedures for configuring, launching, and verifying the core audiobook ingestion, MySQL session tracking, and audio player system.

---

## 1. Prerequisites

- **Python**: Version 3.11+
- **Database**: MySQL 8.0+ or MariaDB 10.5+ running locally or in Docker
- **System Audio**: Functioning audio device (or dummy audio driver in headless environments)
- **Environment**: Virtual environment with dependencies installed

---

## 2. Environment Setup

Create `.env` based on `.env.example`:

```bash
# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=studylab
DB_PASSWORD=studylab_password
DB_NAME=studylab_audiobook

# Text-to-Speech Settings
TTS_PROVIDER=edge-tts
TTS_DEFAULT_VOICE=en-US-ChristopherNeural

# Optional Paid Providers (Not required for Edge-TTS)
# OPENAI_API_KEY=sk-...

# Network Latency Telemetry Probing
LAN_PING_HOST=192.168.1.1
TAILSCALE_PING_HOST=100.100.100.100

# Cache Directory
AUDIO_CACHE_DIR=.studylab/cache/audio
```

Initialize database tables:
```bash
python -m src.storage.migrations
```

---

## 3. End-to-End Verification Scenarios

### Scenario 1: Book Ingestion & Parsing
Verify that a sample document is ingested, segmented into indexed sentences, and stored in MySQL:

```bash
# Create a sample text file
cat << 'EOF' > sample_book.txt
# Chapter 1: The Gathering Storm

The morning sun broke through the thick fog, casting long shadows across the valley. It was a silent dawn.
Every soldier prepared their equipment in solemn silence, knowing that the decisive battle would begin before nightfall.
EOF

# Ingest book into StudyLab
python -m src.cli.main ingest sample_book.txt --title "The Gathering Storm" --author "Historical Archives"
```

**Expected Outcome**:
- Success message output indicating book cataloged.
- `books` table contains 1 row with `total_sentences: 3` and calculated word count.
- `book_sentences` table contains 3 indexed rows with SHA-256 hashes.
- `bookmarks` table initializes with `current_sentence_index: 0`.

---

### Scenario 2: Interactive Playback & Navigation
Verify real-time playback, TUI display, and hotkey navigation:

```bash
python -m src.cli.main play 1
```

**Actions**:
1. Verify audio begins playing sentence 1 within 2 seconds.
2. Press `[Space]` — verify playback pauses and TUI displays `[PAUSED]`.
3. Press `[Right Arrow]` — verify playback advances to sentence 2 and synthesizes audio.
4. Press `[q]` — verify reader quits cleanly, saves progress, and flushes session telemetry.

**Expected Outcome**:
- TUI exits cleanly without terminal corruption.
- Audio files cached under `.studylab/cache/audio/1/`.

---

### Scenario 3: Reading Session & Telemetry Verification
Verify that session duration, absorbed words, and telemetry were persisted to MySQL:

```bash
python -m src.cli.main metrics --book-id 1 --json
```

**Expected Outcome**:
- Returns valid JSON payload showing:
  - `total_listening_minutes > 0`
  - `total_words_absorbed > 0`
  - `avg_sentence_response_time_sec > 0`
  - `avg_lan_ping_ms` and `avg_tailscale_ping_ms` populated.

---

### Scenario 4: Automated Offline Test Suite
Verify that all unit and integration tests execute and pass 100% offline with mocked external APIs:

```bash
pytest tests/ -v
```

**Expected Outcome**:
- 100% of tests pass.
- Zero network requests dispatched to live TTS APIs.

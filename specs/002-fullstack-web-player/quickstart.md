# Quickstart & Verification Guide: Decoupled Full-Stack Web Player

**Feature**: `002-fullstack-web-player`
**Date**: 2026-11-21

This guide details the procedure for starting the Flask backend, launching the React SPA frontend, and verifying all end-to-end user workflows on localhost.

---

## 1. Prerequisites

- **Python**: 3.11+ (virtual environment activated at `.venv`)
- **Node.js**: 18+ and `npm`
- **Database**: SQLite (default fallback with `DB_USE_SQLITE=true`) or MySQL running on localhost

---

## 2. Starting the Backend Server (Flask REST API)

Ensure dependencies (`flask`, `flask-cors`, etc.) are installed in `.venv`:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run database migrations
python -m src.core.storage.migrations

# 3. Start the Flask REST API on localhost:5000
python -m src.api.app
```

Verify backend is responding:
```bash
curl http://localhost:5000/api/books
```

---

## 3. Starting the Frontend Server (React + Vite)

In a separate terminal:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install npm dependencies
npm install

# 3. Start Vite dev server on localhost:5173
npm run dev
```

Open your browser at: `http://localhost:5173`

---

## 4. End-to-End Verification Scenarios

### Scenario 1: Web Book Upload & Ingestion
1. Open `http://localhost:5173/` in your browser.
2. Click **"Upload Book"**.
3. Drag and drop `test_sample.txt` (or any `.txt`/`.md` file).
4. Enter Title: *"The First Flight"*, Author: *"Orville Wright"*.
5. Click **"Upload & Process"**.
6. **Expected Outcome**: The book is parsed and immediately appears in the library grid showing sentence and word count.

### Scenario 2: Real-Time Audio Playback & Text Highlighting
1. Click **"Listen"** on any cataloged book (navigates to `http://localhost:5173/play/1`).
2. Click **"Play"** (or press `[Space]`).
3. **Expected Outcome**:
   - Audio begins playing within 1.5 seconds.
   - The first sentence text is highlighted with an active reading badge.
   - When sentence 1 finishes, sentence 2 begins playing without noticeable pause (<200ms gap).
   - Click "Next Sentence" (or press Right Arrow): playback skips to the next sentence and updates the active highlighted sentence.

### Scenario 3: Bookmark Resumption Across Browser Reloads
1. Play through sentence 3 of any book.
2. Press `[Space]` to pause.
3. Refresh the browser page (`F5`).
4. **Expected Outcome**: The player restores sentence 3 as the active sentence and displays the saved completion percentage.

### Scenario 4: Analytics Dashboard & Matplotlib Visualization
1. Click **"Dashboard"** in the navigation bar (`http://localhost:5173/dashboard`).
2. **Expected Outcome**:
   - Numeric KPI cards display Total Listening Minutes, Words Absorbed, Total Sessions, and Average TTS Latency.
   - Dual Matplotlib visual charts (`listening-trends.png` and `latency-metrics.png`) render cleanly with high contrast.

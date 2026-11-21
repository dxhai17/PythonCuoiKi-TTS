# REST API Contract: Decoupled Full-Stack Web Player

**Base URL**: `http://localhost:5000/api`
**Format**: JSON (Request & Response) / Audio Stream (`audio/mpeg`) / PNG Image (`image/png`)

---

## 1. Books Blueprint (`/api/books`)

### `GET /api/books`
- **Description**: List all cataloged books with pagination.
- **Query Parameters**:
  - `limit` (int, default 50)
  - `offset` (int, default 0)
- **Response `200 OK`**:
  ```json
  [
    {
      "id": 1,
      "title": "The First Flight",
      "author": "Orville Wright",
      "total_chapters": 1,
      "total_sentences": 42,
      "total_words": 650,
      "created_at": "2026-11-21T12:00:00Z"
    }
  ]
  ```

### `POST /api/books/ingest`
- **Description**: Upload and catalog a `.txt` or `.md` book file.
- **Request**: Multipart Form Data
  - `file`: File upload (`.txt` or `.md`, max 10MB)
  - `title`: string (optional, extracted from content if missing)
  - `author`: string (optional, default: "Unknown")
- **Response `201 Created`**:
  ```json
  {
    "status": "success",
    "book_id": 1,
    "title": "The First Flight",
    "total_chapters": 1,
    "total_sentences": 42,
    "total_words": 650
  }
  ```
- **Error `400 Bad Request`**:
  ```json
  {
    "error": "Unsupported file format. Only .txt and .md files are supported."
  }
  ```

### `GET /api/books/<book_id>/sentences`
- **Description**: Fetch all indexed sentences for a book for text synchronization.
- **Response `200 OK`**:
  ```json
  {
    "book_id": 1,
    "total_sentences": 42,
    "sentences": [
      {
        "sentence_index": 0,
        "chapter_index": 1,
        "text_content": "The morning sun broke through the thick fog.",
        "word_count": 8
      }
    ]
  }
  ```

---

## 2. Player Blueprint (`/api`)

### `GET /api/audio/<book_id>/<sentence_index>`
- **Description**: Stream synthesized MP3 audio for an indexed sentence.
- **Query Parameters**:
  - `speed` (float, default 1.0, range 0.7 - 2.0)
  - `voice` (string, optional)
- **Response `200 OK`**:
  - `Content-Type: audio/mpeg`
  - `Cache-Control: public, max-age=86400`
  - Audio binary payload.

### `GET /api/bookmarks/<book_id>`
- **Description**: Retrieve saved bookmark for a book.
- **Response `200 OK`**:
  ```json
  {
    "book_id": 1,
    "current_chapter": 1,
    "current_sentence_index": 5,
    "completion_percentage": 11.9,
    "last_read_at": "2026-11-21T14:30:00Z"
  }
  ```

### `POST /api/bookmarks`
- **Description**: Update bookmark position.
- **Request `application/json`**:
  ```json
  {
    "book_id": 1,
    "current_chapter": 1,
    "current_sentence_index": 6,
    "completion_percentage": 14.2
  }
  ```
- **Response `200 OK`**: `{"status": "updated"}`

### `POST /api/sessions`
- **Description**: Record a completed reading session.
- **Request `application/json`**:
  ```json
  {
    "book_id": 1,
    "duration_seconds": 180,
    "sentences_read": 12,
    "words_read": 164,
    "start_time": "2026-11-21T14:20:00Z",
    "end_time": "2026-11-21T14:23:00Z"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "session_id": 4,
    "status": "saved"
  }
  ```

---

## 3. Analytics Blueprint (`/api/analytics`)

### `GET /api/analytics/summary`
- **Description**: Return aggregated listening and network KPI metrics.
- **Response `200 OK`**:
  ```json
  {
    "total_listening_minutes": 45.2,
    "total_words_absorbed": 5420,
    "total_sessions": 3,
    "avg_sentence_response_time_sec": 0.41,
    "avg_lan_ping_ms": 2.1,
    "avg_tailscale_ping_ms": 26.8,
    "recent_sessions_count": 3
  }
  ```

### `GET /api/analytics/charts/listening-trends.png`
- **Description**: Binary headless Matplotlib PNG visual chart showing weekly listening trend.
- **Response `200 OK`**:
  - `Content-Type: image/png`
  - `Cache-Control: no-cache`
  - Image binary payload.

### `GET /api/analytics/charts/latency-metrics.png`
- **Description**: Binary headless Matplotlib PNG visual chart showing synthesis latency and LAN/Tailscale ping distributions.
- **Response `200 OK`**:
  - `Content-Type: image/png`
  - `Cache-Control: no-cache`
  - Image binary payload.

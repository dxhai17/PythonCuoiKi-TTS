# Frontend Component & Hook Contracts: Decoupled Full-Stack Web Player

**Framework**: React 18+ with TypeScript & Vite
**Rule**: Maximum 250 LOC per file; zero monolithic files.

---

## 1. Custom Hooks Contract (`frontend/src/hooks/`)

### `useAudioPlayer(bookId: number, initialSentenceIndex: number)`
- **Purpose**: Encapsulates dual-HTML5-audio pre-fetching, speed controls, play/pause state, and bookmark synchronization.
- **Hook State**:
  ```typescript
  interface UseAudioPlayerReturn {
    isPlaying: boolean;
    isBuffering: boolean;
    currentIndex: number;
    speed: number;
    lastLatencySec: number;
    play: () => void;
    pause: () => void;
    togglePlay: () => void;
    skipForward: () => void;
    skipBackward: () => void;
    seekToSentence: (index: number) => void;
    setSpeed: (speed: number) => void;
  }
  ```

### `useBookCatalog()`
- **Purpose**: Manages fetching library books, sorting, and file upload state.
- **Hook State**:
  ```typescript
  interface UseBookCatalogReturn {
    books: Book[];
    isLoading: boolean;
    error: string | null;
    uploadBook: (file: File, title?: string, author?: string) => Promise<Book>;
    refreshBooks: () => Promise<void>;
  }
  ```

### `useDashboard()`
- **Purpose**: Manages summary metrics retrieval and chart refresh state.
- **Hook State**:
  ```typescript
  interface UseDashboardReturn {
    summary: AnalyticsSummary | null;
    isLoading: boolean;
    error: string | null;
    refreshMetrics: () => Promise<void>;
  }
  ```

---

## 2. Component Boundaries (`frontend/src/components/`)

### `Player/`
- `AudioPlayerContainer.tsx`: Coordinates sentence text list, controls, and progress bar.
- `SentenceList.tsx`: Displays scrollable list of book sentences with auto-scroll and visual highlighting on the active spoken sentence.
- `PlayerControls.tsx`: Play/Pause button, Next/Previous skip buttons, speed dropdown/slider, latency indicator.
- `ProgressBar.tsx`: Percentage completion bar with seek interaction.

### `BookUploader/`
- `BookUploaderModal.tsx`: Modal dialog containing form and upload states.
- `FileDropZone.tsx`: Drag-and-drop file target accepting `.txt` and `.md` with client-side extension validation.

### `Dashboard/`
- `MetricCard.tsx`: Reusable single-metric KPI card (e.g., Total Minutes, Words Absorbed, LAN Latency).
- `ChartViewer.tsx`: Card embedding Matplotlib PNG image stream with refresh trigger and loading skeleton.

### `Navbar/`
- `Navbar.tsx`: Header navigation between Library (`/`), Player (`/play`), and Dashboard (`/dashboard`).

---

## 3. Dedicated Route Pages (`frontend/src/pages/`)

- `LibraryPage.tsx` (`/`): Grid of cataloged books, "Upload Book" trigger button, empty state guide.
- `PlayerPage.tsx` (`/play/:bookId`): Full-featured reading and listening view with text synchronization.
- `DashboardPage.tsx` (`/dashboard`): Analytics dashboard with KPI metric grid and Matplotlib visual charts.

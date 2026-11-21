export interface Bookmark {
  book_id: number;
  current_chapter: number;
  current_sentence_index: number;
  completion_percentage: number;
  last_read_at?: string;
}

export interface AudioPlayerState {
  isPlaying: boolean;
  isBuffering: boolean;
  currentIndex: number;
  speed: number;
  voice: string;
  lastLatencySec: number;
}

export interface ReadingSessionPayload {
  book_id: number;
  duration_seconds: number;
  sentences_read: number;
  words_read: number;
  start_time: string;
  end_time: string;
}

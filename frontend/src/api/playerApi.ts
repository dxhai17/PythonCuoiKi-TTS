import { apiGet, apiPost } from './client.ts';
import { BookSentence } from '../types/book.ts';
import { Bookmark, ReadingSessionPayload } from '../types/player.ts';

export async function fetchBookSentences(bookId: number): Promise<{
  book_id: number;
  total_sentences: number;
  sentences: BookSentence[];
}> {
  return apiGet<{ book_id: number; total_sentences: number; sentences: BookSentence[] }>(
    `/books/${bookId}/sentences`
  );
}

export async function fetchBookmark(bookId: number): Promise<Bookmark> {
  return apiGet<Bookmark>(`/bookmarks/${bookId}`);
}

export async function updateBookmark(payload: {
  book_id: number;
  current_chapter: number;
  current_sentence_index: number;
  completion_percentage: number;
}): Promise<void> {
  await apiPost('/bookmarks', payload);
}

export async function recordReadingSession(payload: ReadingSessionPayload): Promise<void> {
  await apiPost('/sessions', payload);
}

export function getAudioStreamUrl(
  bookId: number,
  sentenceIndex: number,
  speed: number = 1.0,
  voice?: string
): string {
  const params = new URLSearchParams({ speed: speed.toFixed(2) });
  if (voice) {
    params.append('voice', voice);
  }
  return `/api/audio/${bookId}/${sentenceIndex}?${params.toString()}`;
}

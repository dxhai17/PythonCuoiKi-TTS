import React, { useEffect, useState } from 'react';
import { BookSentence } from '../types/book.ts';
import { fetchBookSentences, fetchBookmark } from '../api/playerApi.ts';
import { useAudioPlayer } from '../hooks/useAudioPlayer.ts';
import { SentenceList } from '../components/Player/SentenceList.tsx';
import { ProgressBar } from '../components/Player/ProgressBar.tsx';
import { PlayerControls } from '../components/Player/PlayerControls.tsx';

interface PlayerPageProps {
  bookId: number;
  bookTitle?: string;
  onBackToLibrary: () => void;
}

export const PlayerPage: React.FC<PlayerPageProps> = ({ bookId, bookTitle, onBackToLibrary }) => {
  const [sentences, setSentences] = useState<BookSentence[]>([]);
  const [initialIndex, setInitialIndex] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadData() {
      try {
        setIsLoading(true);
        const [sentencesData, bookmarkData] = await Promise.all([
          fetchBookSentences(bookId),
          fetchBookmark(bookId).catch(() => null),
        ]);

        if (!active) return;
        setSentences(sentencesData.sentences);
        if (bookmarkData && bookmarkData.current_sentence_index > 0) {
          const idx = Math.min(bookmarkData.current_sentence_index, sentencesData.sentences.length - 1);
          setInitialIndex(idx);
        }
      } catch (err: any) {
        if (active) setError(err.message || 'Failed to load audiobook sentences');
      } finally {
        if (active) setIsLoading(false);
      }
    }

    loadData();
    return () => { active = false; };
  }, [bookId]);

  const player = useAudioPlayer({
    bookId,
    sentences,
    initialIndex,
  });

  // Global hotkeys
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      if (e.code === 'Space') {
        e.preventDefault();
        player.togglePlay();
      } else if (e.code === 'ArrowRight') {
        e.preventDefault();
        player.skipForward();
      } else if (e.code === 'ArrowLeft') {
        e.preventDefault();
        player.skipBackward();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [player]);

  if (isLoading) {
    return (
      <div className="player-loading">
        <div className="spinner" />
        <p>Loading audiobook sentences...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="player-error">
        <p>{error}</p>
        <button onClick={onBackToLibrary} className="btn-secondary">Back to Library</button>
      </div>
    );
  }

  return (
    <div className="player-page">
      <div className="player-header">
        <button onClick={onBackToLibrary} className="back-link">← Library</button>
        <h2 className="book-title">{bookTitle || `Audiobook #${bookId}`}</h2>
      </div>

      <ProgressBar
        currentIndex={player.currentIndex}
        totalSentences={sentences.length}
        onSeek={player.seekToSentence}
      />

      <SentenceList
        sentences={sentences}
        currentIndex={player.currentIndex}
        onSentenceClick={player.seekToSentence}
      />

      <PlayerControls
        isPlaying={player.isPlaying}
        isBuffering={player.isBuffering}
        speed={player.speed}
        lastLatencySec={player.lastLatencySec}
        onTogglePlay={player.togglePlay}
        onSkipForward={player.skipForward}
        onSkipBackward={player.skipBackward}
        onSpeedChange={player.setSpeed}
      />
    </div>
  );
};

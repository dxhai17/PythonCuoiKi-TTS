import { useState, useEffect, useRef, useCallback } from 'react';
import { BookSentence } from '../types/book.ts';
import { getAudioStreamUrl, updateBookmark, recordReadingSession } from '../api/playerApi.ts';

export interface UseAudioPlayerProps {
  bookId: number;
  sentences: BookSentence[];
  initialIndex?: number;
}

export function useAudioPlayer({ bookId, sentences, initialIndex = 0 }: UseAudioPlayerProps) {
  const [currentIndex, setCurrentIndex] = useState<number>(initialIndex);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isBuffering, setIsBuffering] = useState<boolean>(false);
  const [speed, setSpeedState] = useState<number>(1.0);
  const [lastLatencySec, setLastLatencySec] = useState<number>(0.0);

  const activeAudio = useRef<HTMLAudioElement | null>(null);
  const prefetchAudio = useRef<HTMLAudioElement | null>(null);

  // Session stats tracking
  const sessionStart = useRef<Date>(new Date());
  const activeSeconds = useRef<number>(0);
  const lastActiveTick = useRef<number>(Date.now());
  const sentencesReadCount = useRef<number>(0);
  const wordsReadCount = useRef<number>(0);

  // Initialize and keep index in sync
  useEffect(() => {
    if (initialIndex >= 0 && initialIndex < sentences.length) {
      setCurrentIndex(initialIndex);
    }
  }, [initialIndex, sentences.length]);

  // Pre-fetch sentence N+1
  const prefetchNext = useCallback((nextIdx: number, curSpeed: number) => {
    if (nextIdx < sentences.length) {
      const url = getAudioStreamUrl(bookId, nextIdx, curSpeed);
      if (!prefetchAudio.current) {
        prefetchAudio.current = new Audio();
      }
      prefetchAudio.current.src = url;
      prefetchAudio.current.playbackRate = curSpeed;
      prefetchAudio.current.load();
    }
  }, [bookId, sentences.length]);

  // Play a specific sentence index
  const playSentence = useCallback((index: number, curSpeed: number) => {
    if (index >= sentences.length || index < 0) {
      setIsPlaying(false);
      return;
    }

    setIsBuffering(true);
    const startReqTime = performance.now();

    // Check if prefetch audio already has this sentence loaded
    const targetUrl = getAudioStreamUrl(bookId, index, curSpeed);
    let audio = activeAudio.current;

    if (prefetchAudio.current && prefetchAudio.current.src.includes(`/api/audio/${bookId}/${index}`)) {
      audio = prefetchAudio.current;
      prefetchAudio.current = null;
    } else {
      if (audio) {
        audio.pause();
      }
      audio = new Audio(targetUrl);
    }

    activeAudio.current = audio;
    audio.playbackRate = curSpeed;

    audio.oncanplay = () => {
      setIsBuffering(false);
      const latency = (performance.now() - startReqTime) / 1000.0;
      setLastLatencySec(Number(latency.toFixed(2)));
    };

    audio.onended = () => {
      // Accumulate words read
      const words = sentences[index]?.word_count || 0;
      wordsReadCount.current += words;
      sentencesReadCount.current += 1;

      // Sync bookmark to backend
      const nextIdx = index + 1;
      const pct = sentences.length > 0 ? (nextIdx / sentences.length) * 100.0 : 0.0;
      updateBookmark({
        book_id: bookId,
        current_chapter: sentences[index]?.chapter_index || 1,
        current_sentence_index: nextIdx,
        completion_percentage: Number(pct.toFixed(1)),
      }).catch(console.error);

      if (nextIdx < sentences.length) {
        setCurrentIndex(nextIdx);
        playSentence(nextIdx, curSpeed);
      } else {
        setIsPlaying(false);
      }
    };

    audio.onerror = () => {
      setIsBuffering(false);
      setIsPlaying(false);
    };

    audio.play().then(() => {
      setIsPlaying(true);
      // Trigger pre-fetch for upcoming sentence
      prefetchNext(index + 1, curSpeed);
    }).catch(() => {
      setIsPlaying(false);
      setIsBuffering(false);
    });
  }, [bookId, sentences, prefetchNext]);

  const play = useCallback(() => {
    lastActiveTick.current = Date.now();
    playSentence(currentIndex, speed);
  }, [currentIndex, speed, playSentence]);

  const pause = useCallback(() => {
    if (activeAudio.current) {
      activeAudio.current.pause();
    }
    setIsPlaying(false);
    setIsBuffering(false);
    activeSeconds.current += (Date.now() - lastActiveTick.current) / 1000.0;
  }, []);

  const togglePlay = useCallback(() => {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }, [isPlaying, play, pause]);

  const skipForward = useCallback(() => {
    if (currentIndex + 1 < sentences.length) {
      const next = currentIndex + 1;
      setCurrentIndex(next);
      if (isPlaying) {
        playSentence(next, speed);
      }
    }
  }, [currentIndex, sentences.length, isPlaying, speed, playSentence]);

  const skipBackward = useCallback(() => {
    if (currentIndex - 1 >= 0) {
      const prev = currentIndex - 1;
      setCurrentIndex(prev);
      if (isPlaying) {
        playSentence(prev, speed);
      }
    }
  }, [currentIndex, isPlaying, speed, playSentence]);

  const seekToSentence = useCallback((index: number) => {
    if (index >= 0 && index < sentences.length) {
      setCurrentIndex(index);
      if (isPlaying) {
        playSentence(index, speed);
      }
    }
  }, [sentences.length, isPlaying, speed, playSentence]);

  const setSpeed = useCallback((newSpeed: number) => {
    setSpeedState(newSpeed);
    if (activeAudio.current) {
      activeAudio.current.playbackRate = newSpeed;
    }
  }, []);

  // Flush reading session on unmount
  useEffect(() => {
    return () => {
      if (activeAudio.current) {
        activeAudio.current.pause();
      }
      const dur = Math.max(1, Math.round(activeSeconds.current));
      if (sentencesReadCount.current > 0 || dur > 3) {
        recordReadingSession({
          book_id: bookId,
          duration_seconds: dur,
          sentences_read: sentencesReadCount.current,
          words_read: wordsReadCount.current,
          start_time: sessionStart.current.toISOString(),
          end_time: new Date().toISOString(),
        }).catch(console.error);
      }
    };
  }, [bookId]);

  return {
    currentIndex,
    isPlaying,
    isBuffering,
    speed,
    lastLatencySec,
    play,
    pause,
    togglePlay,
    skipForward,
    skipBackward,
    seekToSentence,
    setSpeed,
  };
}

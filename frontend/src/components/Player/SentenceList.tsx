import React, { useEffect, useRef } from 'react';
import { BookSentence } from '../../types/book.ts';

interface SentenceListProps {
  sentences: BookSentence[];
  currentIndex: number;
  onSentenceClick: (index: number) => void;
}

export const SentenceList: React.FC<SentenceListProps> = ({
  sentences,
  currentIndex,
  onSentenceClick,
}) => {
  const activeItemRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (activeItemRef.current) {
      activeItemRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
      });
    }
  }, [currentIndex]);

  return (
    <div className="sentence-list-container">
      {sentences.map((s, idx) => {
        const isActive = idx === currentIndex;
        return (
          <div
            key={s.sentence_index}
            ref={isActive ? activeItemRef : null}
            className={`sentence-item ${isActive ? 'active' : ''}`}
            onClick={() => onSentenceClick(idx)}
          >
            <span className="sentence-num">#{idx + 1}</span>
            <p className="sentence-text">{s.text_content}</p>
          </div>
        );
      })}
    </div>
  );
};

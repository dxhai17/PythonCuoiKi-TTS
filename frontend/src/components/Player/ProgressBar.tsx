import React from 'react';

interface ProgressBarProps {
  currentIndex: number;
  totalSentences: number;
  onSeek?: (index: number) => void;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  currentIndex,
  totalSentences,
  onSeek,
}) => {
  const percentage = totalSentences > 0 ? ((currentIndex + 1) / totalSentences) * 100 : 0;

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!onSeek || totalSentences === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickRatio = Math.max(0, Math.min(1, clickX / rect.width));
    const targetIndex = Math.min(Math.floor(clickRatio * totalSentences), totalSentences - 1);
    onSeek(targetIndex);
  };

  return (
    <div className="progress-bar-wrapper">
      <div className="progress-info">
        <span>Sentence {currentIndex + 1} of {totalSentences}</span>
        <span>{percentage.toFixed(1)}%</span>
      </div>
      <div className="progress-track" onClick={handleClick}>
        <div className="progress-fill" style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
};

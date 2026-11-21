import React from 'react';
import { Play, Pause, SkipBack, SkipForward, Activity } from 'lucide-react';

interface PlayerControlsProps {
  isPlaying: boolean;
  isBuffering: boolean;
  speed: number;
  lastLatencySec: number;
  onTogglePlay: () => void;
  onSkipForward: () => void;
  onSkipBackward: () => void;
  onSpeedChange: (speed: number) => void;
}

export const PlayerControls: React.FC<PlayerControlsProps> = ({
  isPlaying,
  isBuffering,
  speed,
  lastLatencySec,
  onTogglePlay,
  onSkipForward,
  onSkipBackward,
  onSpeedChange,
}) => {
  const speeds = [0.75, 1.0, 1.25, 1.5, 1.75, 2.0];

  return (
    <div className="player-controls">
      <div className="latency-indicator">
        <Activity size={16} />
        <span>Latency: {lastLatencySec > 0 ? `${lastLatencySec}s` : 'Ready'}</span>
      </div>

      <div className="playback-buttons">
        <button className="ctrl-btn secondary" onClick={onSkipBackward} title="Previous sentence [Left]">
          <SkipBack size={20} />
        </button>

        <button className="ctrl-btn primary" onClick={onTogglePlay} title="Play/Pause [Space]">
          {isBuffering ? (
            <span className="spinner" />
          ) : isPlaying ? (
            <Pause size={24} />
          ) : (
            <Play size={24} />
          )}
        </button>

        <button className="ctrl-btn secondary" onClick={onSkipForward} title="Next sentence [Right]">
          <SkipForward size={20} />
        </button>
      </div>

      <div className="speed-control">
        <label htmlFor="speed-select">Speed:</label>
        <select
          id="speed-select"
          value={speed}
          onChange={(e) => onSpeedChange(parseFloat(e.target.value))}
          className="speed-dropdown"
        >
          {speeds.map((s) => (
            <option key={s} value={s}>{s}x</option>
          ))}
        </select>
      </div>
    </div>
  );
};

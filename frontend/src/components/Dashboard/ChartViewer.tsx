import React, { useState } from 'react';
import { RefreshCw } from 'lucide-react';

interface ChartViewerProps {
  title: string;
  chartUrl: string;
  onRefresh?: () => void;
}

export const ChartViewer: React.FC<ChartViewerProps> = ({ title, chartUrl, onRefresh }) => {
  const [hasLoaded, setHasLoaded] = useState(false);

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h4 className="chart-title">{title}</h4>
        {onRefresh && (
          <button className="chart-refresh-btn" onClick={onRefresh} title="Refresh Chart">
            <RefreshCw size={16} />
          </button>
        )}
      </div>
      <div className="chart-image-wrapper">
        <img
          src={chartUrl}
          alt={title}
          className={`chart-img ${hasLoaded ? 'loaded' : 'loading'}`}
          onLoad={() => setHasLoaded(true)}
        />
      </div>
    </div>
  );
};

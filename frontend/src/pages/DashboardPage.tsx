import React from 'react';
import { useDashboard } from '../hooks/useDashboard.ts';
import { MetricCard } from '../components/Dashboard/MetricCard.tsx';
import { ChartViewer } from '../components/Dashboard/ChartViewer.tsx';
import { Clock, BookOpen, Activity, Wifi, Zap } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { days, setDays, summary, isLoading, error, refreshMetrics, chartReloadKey, getChartUrl } =
    useDashboard(7);

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div>
          <h2>Analytics & Telemetry</h2>
          <p className="subtitle">Reading habits and technical performance telemetry</p>
        </div>

        <div className="days-filter">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              className={`filter-btn ${days === d ? 'active' : ''}`}
              onClick={() => setDays(d)}
            >
              {d} Days
            </button>
          ))}
        </div>
      </div>

      {isLoading && !summary ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>Loading analytics metrics...</p>
        </div>
      ) : error ? (
        <div className="error-state">
          <p>{error}</p>
          <button className="btn-secondary" onClick={refreshMetrics}>Retry</button>
        </div>
      ) : (
        <>
          <div className="metrics-grid">
            <MetricCard
              label="Listening Time"
              value={`${summary?.total_listening_minutes.toFixed(1)} mins`}
              subtext={`Across ${summary?.total_sessions} completed sessions`}
              icon={<Clock size={20} className="text-blue" />}
            />

            <MetricCard
              label="Words Absorbed"
              value={summary?.total_words_absorbed.toLocaleString() || 0}
              subtext="Total processed vocabulary"
              icon={<BookOpen size={20} className="text-green" />}
            />

            <MetricCard
              label="Avg TTS Latency"
              value={`${summary?.avg_sentence_response_time_sec.toFixed(2)}s`}
              subtext="Sentence synthesis roundtrip"
              icon={<Zap size={20} className="text-amber" />}
            />

            <MetricCard
              label="LAN Latency"
              value={`${summary?.avg_lan_ping_ms.toFixed(1)} ms`}
              subtext="Local Gateway Roundtrip"
              icon={<Wifi size={20} className="text-cyan" />}
            />

            <MetricCard
              label="Tailscale Latency"
              value={`${summary?.avg_tailscale_ping_ms.toFixed(1)} ms`}
              subtext="Tailscale mesh node probe"
              icon={<Activity size={20} className="text-purple" />}
            />
          </div>

          <div className="charts-container">
            <ChartViewer
              key={`trends-${chartReloadKey}`}
              title="Daily Reading Minutes & Absorbed Words"
              chartUrl={getChartUrl('listening-trends')}
              onRefresh={refreshMetrics}
            />

            <ChartViewer
              key={`latency-${chartReloadKey}`}
              title="Speech Synthesis & Network Latency Distribution"
              chartUrl={getChartUrl('latency-metrics')}
              onRefresh={refreshMetrics}
            />
          </div>
        </>
      )}
    </div>
  );
};

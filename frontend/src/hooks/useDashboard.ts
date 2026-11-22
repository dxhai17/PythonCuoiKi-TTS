import { useState, useEffect, useCallback } from 'react';
import { AnalyticsSummary } from '../types/analytics.ts';
import { fetchAnalyticsSummary, getChartImageUrl } from '../api/analyticsApi.ts';

export function useDashboard(initialDays = 7) {
  const [days, setDays] = useState<number>(initialDays);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [chartReloadKey, setChartReloadKey] = useState<number>(Date.now());

  const refreshMetrics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchAnalyticsSummary(days);
      setSummary(data);
      setChartReloadKey(Date.now());
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics metrics');
    } finally {
      setIsLoading(false);
    }
  }, [days]);

  useEffect(() => {
    refreshMetrics();
  }, [refreshMetrics]);

  return {
    days,
    setDays,
    summary,
    isLoading,
    error,
    refreshMetrics,
    chartReloadKey,
    getChartUrl: (chartName: 'listening-trends' | 'latency-metrics') =>
      getChartImageUrl(chartName, days),
  };
}

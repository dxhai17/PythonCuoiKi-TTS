import { apiGet } from './client.ts';
import { AnalyticsSummary } from '../types/analytics.ts';

export async function fetchAnalyticsSummary(days = 7, bookId?: number): Promise<AnalyticsSummary> {
  const params: Record<string, string | number> = { days };
  if (bookId !== undefined) {
    params.book_id = bookId;
  }
  return apiGet<AnalyticsSummary>('/analytics/summary', params);
}

export function getChartImageUrl(chartName: 'listening-trends' | 'latency-metrics', days = 7): string {
  return `/api/analytics/charts/${chartName}.png?days=${days}&t=${Date.now()}`;
}

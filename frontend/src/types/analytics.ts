export interface AnalyticsSummary {
  total_listening_minutes: number;
  total_words_absorbed: number;
  total_sessions: number;
  avg_sentence_response_time_sec: number;
  avg_lan_ping_ms: number;
  avg_tailscale_ping_ms: number;
  recent_sessions_count: number;
}

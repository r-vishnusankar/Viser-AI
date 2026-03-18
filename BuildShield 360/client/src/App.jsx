import React, { useState, useEffect, useCallback } from 'react';
import { triggerBuild, getBuilds, getBuildTrend } from './api/builds';
import SummaryCards from './components/SummaryCards';
import SecuritySection from './components/SecuritySection';
import PerformanceSection from './components/PerformanceSection';
import BuildTrendAnalytics from './components/BuildTrendAnalytics';
import './App.css';

export default function App() {
  const [latestBuild, setLatestBuild] = useState(null);
  const [trendBuilds, setTrendBuilds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState(null);
  const [targetUrl, setTargetUrl] = useState('');

  const fetchData = useCallback(async () => {
    setError(null);
    try {
      const [buildsRes, trendRes] = await Promise.all([getBuilds(1, 0), getBuildTrend(10)]);
      setLatestBuild(buildsRes.builds?.[0] ?? null);
      setTrendBuilds(trendRes.builds ?? []);
    } catch (e) {
      setError(e.message);
      setLatestBuild(null);
      setTrendBuilds([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const onTrigger = async () => {
    setTriggering(true);
    setError(null);
    try {
      await triggerBuild({ triggeredBy: 'dashboard', targetUrl: targetUrl.trim() || undefined });
      await fetchData();
    } catch (e) {
      setError(e.message);
    } finally {
      setTriggering(false);
    }
  };

  const onRefresh = () => {
    setLoading(true);
    fetchData();
  };

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-logo">BuildShield <span>360</span></div>
        <div className="trigger-row">
          <label className="url-label">
            <span>URL to scan</span>
            <input
              type="url"
              className="url-input"
              placeholder="https://example.com (optional)"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              disabled={triggering}
            />
          </label>
          <button type="button" className="btn-trigger" onClick={onTrigger} disabled={triggering}>
            {triggering ? 'Running tests…' : 'Trigger new build'}
          </button>
          <button type="button" className="btn-refresh" onClick={onRefresh} disabled={loading} title="Refresh data">
            ↻
          </button>
        </div>
      </header>
      <div className="help-banner">
        <strong>Security scan:</strong> Enter URL + Trigger → runs ZAP. Leave URL empty + Trigger → uses <code>zap_report.json</code> if present. <strong>Click Trigger to load results.</strong>
      </div>
      <main className="app-main">
        {error && <div className="error-msg">API error: {error}</div>}
        {loading ? (
          <div className="loading">Loading…</div>
        ) : (
          <>
            <SummaryCards build={latestBuild} />
            <SecuritySection build={latestBuild} trendBuilds={trendBuilds} />
            <PerformanceSection build={latestBuild} />
            <BuildTrendAnalytics builds={trendBuilds} />
          </>
        )}
      </main>
    </div>
  );
}

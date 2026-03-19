import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export default function PerformanceSection({ build }) {
  const sampleData = build?.performance?.sampleData ?? [];
  const data = sampleData.map((s, i) => ({
    time: i,
    ms: s.responseTimeMs,
    rps: s.requestsPerSecond,
    err: s.errorRate,
  }));

  return (
    <>
      <div className="section-title">Performance</div>
      <div className="charts-grid">
        <div className="chart-card">
          <h3>Response time (ms)</h3>
          {data.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data}><XAxis dataKey="time" /><YAxis /><Tooltip /><Line type="monotone" dataKey="ms" stroke="#58a6ff" dot={false} /></LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">Trigger a build to see results.</div>
          )}
        </div>
        <div className="chart-card">
          <h3>Throughput (RPS)</h3>
          {data.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={data}><XAxis dataKey="time" /><YAxis /><Tooltip /><Line type="monotone" dataKey="rps" stroke="#3fb950" dot={false} /></LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">No data yet.</div>
          )}
        </div>
      </div>
    </>
  );
}

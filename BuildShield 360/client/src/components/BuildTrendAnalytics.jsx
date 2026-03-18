import React from 'react';

export default function BuildTrendAnalytics({ builds }) {
  const list = builds ?? [];

  return (
    <>
      <div className="section-title">Build trend</div>
      <div className="trend-list">
        {list.length === 0 ? (
          <div className="empty-state">No builds yet. Trigger a build to see trend.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Build ID</th>
                <th>Time</th>
                <th>Security</th>
                <th>Perf (ms)</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {[...list].reverse().map((b) => (
                <tr key={b.buildId}>
                  <td>{b.buildId}</td>
                  <td>{new Date(b.triggeredAt).toLocaleString()}</td>
                  <td>{b.security?.securityScore ?? '—'}%</td>
                  <td>{b.performance?.avgResponseTimeMs ?? '—'}</td>
                  <td><span className={`badge ${b.overallStatus === 'PASS' ? 'pass' : 'fail'}`}>{b.overallStatus}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

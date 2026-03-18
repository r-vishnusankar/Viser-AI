import React from 'react';

export default function SummaryCards({ build }) {
  if (!build) {
    return (
      <div className="cards-row">
        {['Build ID', 'Security Score', 'Performance Score', 'Overall Status'].map((l) => (
          <div key={l} className="card">
            <div className="card-label">{l}</div>
            <div className="card-value">—</div>
          </div>
        ))}
      </div>
    );
  }
  const perfScore = build.performance
    ? Math.round(Math.max(0, 100 - build.performance.avgResponseTimeMs / 20 - build.performance.errorRatePercent * 5))
    : 0;
  return (
    <div className="cards-row">
      <div className="card">
        <div className="card-label">Build ID</div>
        <div className="card-value" style={{ fontSize: '1rem' }}>{build.buildId}</div>
      </div>
      <div className="card">
        <div className="card-label">Security Score {build.security?.checks?.zapReport && <span className="badge info" title="From ZAP scan">ZAP</span>}</div>
        <div className="card-value">{build.security?.securityScore ?? 0}%</div>
        <span className={`badge ${build.security?.status === 'PASS' ? 'pass' : 'fail'}`}>{build.security?.status ?? '—'}</span>
      </div>
      <div className="card">
        <div className="card-label">Performance Score</div>
        <div className="card-value">{Math.min(100, perfScore)}%</div>
        <span className={`badge ${build.performance?.status === 'PASS' ? 'pass' : 'fail'}`}>{build.performance?.status ?? '—'}</span>
      </div>
      <div className="card">
        <div className="card-label">Overall Status</div>
        <div className="card-value"><span className={`badge ${build.overallStatus === 'PASS' ? 'pass' : 'fail'}`}>{build.overallStatus}</span></div>
      </div>
    </div>
  );
}

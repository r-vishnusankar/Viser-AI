import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'info'];
const SEVERITY_COLORS = { critical: '#f85149', high: '#da3633', medium: '#d29922', low: '#58a6ff', info: '#8b949e' };
const SEVERITY_LABELS = { critical: 'Critical', high: 'High', medium: 'Medium', low: 'Low', info: 'Informational' };

export default function SecuritySection({ build, trendBuilds }) {
  const [expandedAlert, setExpandedAlert] = useState(null);
  const security = build?.security;
  const rawReport = security?.rawReport;
  const alerts = rawReport?.alerts || [];
  const scannedUrl = rawReport?.scannedUrl || build?.metadata?.targetUrl;

  const vulnData = security
    ? [
        { name: 'Critical', count: security.critical, fill: '#f85149' },
        { name: 'High', count: security.high, fill: '#da3633' },
        { name: 'Medium', count: security.medium, fill: '#d29922' },
        { name: 'Low', count: security.low, fill: '#58a6ff' },
        { name: 'Info', count: security.info, fill: '#8b949e' },
      ].filter((d) => d.count > 0)
    : [];

  const trendData = (trendBuilds ?? []).slice(-10).map((b) => ({
    buildId: b.buildId?.slice(-8) ?? '—',
    score: b.security?.securityScore ?? 0,
  }));

  const fromZap = security?.checks?.zapReport;
  const sortedAlerts = [...alerts].sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity));

  return (
    <>
      <div className="section-title">
        Security
        {security && (fromZap ? <span className="source-badge zap">From ZAP scan</span> : <span className="source-badge simulated">Simulated</span>)}
      </div>

      {build?.metadata?.zapScanJobs?.length > 0 && (
        <div className="scan-status">
          <h4>ZAP scan jobs</h4>
          <div className="scan-jobs">
            {build.metadata.zapScanJobs.map((job, i) => (
              <div key={i} className={`scan-job ${job.status}`}>
                <span className="job-status-icon">{job.status === 'completed' ? '✓' : '○'}</span>
                <span className="job-name">{job.name}</span>
                {job.detail && <span className="job-detail">{job.detail}</span>}
                {job.duration && <span className="job-duration">{job.duration}</span>}
              </div>
            ))}
          </div>
        </div>
      )}
      {(scannedUrl || rawReport?.reportGenerated) && (
        <div className="scanned-url">
          {scannedUrl && <><strong>Target:</strong> <a href={scannedUrl} target="_blank" rel="noopener noreferrer">{scannedUrl}</a></>}
          {rawReport?.reportGenerated && <span className="report-meta"> · Report: {rawReport.reportGenerated}</span>}
          {fromZap && (
            <a href="/api/zap/report" target="_blank" rel="noopener noreferrer" className="view-full-report">
              View full ZAP report →
            </a>
          )}
        </div>
      )}

      {security && (
        <div className="priority-summary">
          <h4>Vulnerability summary</h4>
          <div className="priority-badges">
            {['critical', 'high', 'medium', 'low', 'info'].map((sev) => {
              const count = security[sev] ?? 0;
              if (count === 0) return null;
              return (
                <span key={sev} className="priority-badge" style={{ background: `${SEVERITY_COLORS[sev]}33`, color: SEVERITY_COLORS[sev] }}>
                  {SEVERITY_LABELS[sev]}: <strong>{count}</strong>
                </span>
              );
            })}
          </div>
          <div className="score-status">
            Score: <strong>{security.securityScore}%</strong> · Status: <span className={`badge ${security.status === 'PASS' ? 'pass' : 'fail'}`}>{security.status}</span>
          </div>
        </div>
      )}

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Vulnerability count by severity</h3>
          {vulnData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={vulnData}><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="count" fill="#58a6ff" /></BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              No security data yet. Click <strong>Trigger new build</strong> above to load from zap_report.json or run a new ZAP scan.
            </div>
          )}
        </div>
        <div className="chart-card">
          <h3>Security score – last 10 builds</h3>
          {trendData.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={trendData}><XAxis dataKey="buildId" /><YAxis domain={[0, 100]} /><Tooltip /><Bar dataKey="score" fill="#3fb950" /></BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">No trend data yet.</div>
          )}
        </div>
      </div>

      {sortedAlerts.length > 0 && (
        <div className="vulnerability-list">
          <h3>Findings ({alerts.length} total)</h3>
          <div className="vuln-items">
            {sortedAlerts.map((a, i) => (
              <div
                key={`${a.pluginid}-${i}`}
                className={`vuln-item severity-${a.severity}`}
                onClick={() => setExpandedAlert(expandedAlert === i ? null : i)}
              >
                <div className="vuln-header">
                  <span className="vuln-severity" style={{ background: SEVERITY_COLORS[a.severity] }}>{SEVERITY_LABELS[a.severity]}</span>
                  <span className="vuln-name">{a.alert}</span>
                  {a.count > 1 && <span className="vuln-count">×{a.count}</span>}
                </div>
                {expandedAlert === i && a.solution && (
                  <div className="vuln-solution"><strong>Fix:</strong> {a.solution}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

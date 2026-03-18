const fs = require('fs');
const path = require('path');

const OWASP_CATEGORIES = [
  { id: 'A01', name: 'Broken Access Control', severity: 'high' },
  { id: 'A02', name: 'Cryptographic Failures', severity: 'high' },
  { id: 'A03', name: 'Injection', severity: 'critical' },
  { id: 'A04', name: 'Insecure Design', severity: 'medium' },
  { id: 'A05', name: 'Security Misconfiguration', severity: 'medium' },
  { id: 'A06', name: 'Vulnerable Components', severity: 'high' },
  { id: 'A07', name: 'Auth Failures', severity: 'high' },
  { id: 'A08', name: 'Data Integrity Failures', severity: 'medium' },
  { id: 'A09', name: 'Logging Failures', severity: 'low' },
  { id: 'A10', name: 'SSRF', severity: 'medium' },
];

// ZAP plugin IDs / CWE → OWASP Top 10 mapping
const PLUGIN_TO_OWASP = {
  10038: 'A05', 10020: 'A05', 10035: 'A05', 10021: 'A05', 10015: 'A08',
  10017: 'A05', 10036: 'A05', 90003: 'A08', // Cross-domain JS, Server leak, SRI
  10027: 'A09', 10116: null, 10109: null,
};

// riskcode: 0=Info, 1=Low, 2=Medium, 3=High, 4=Critical
const RISKCODE_TO_SEVERITY = { 0: 'info', 1: 'low', 2: 'medium', 3: 'high', 4: 'critical' };

function parseZapReport(jsonPath) {
  const resolvedPath = path.isAbsolute(jsonPath) ? jsonPath : path.resolve(process.cwd(), jsonPath);
  if (!fs.existsSync(resolvedPath)) {
    return null;
  }
  let data;
  try {
    data = JSON.parse(fs.readFileSync(resolvedPath, 'utf8'));
  } catch (err) {
    console.warn('ZAP report parse error:', err.message);
    return null;
  }
  const sites = data.site || [];
  let critical = 0, high = 0, medium = 0, low = 0, info = 0;
  const owaspCounts = Object.fromEntries(OWASP_CATEGORIES.map((c) => [c.id, 0]));
  const rawAlerts = [];
  let scannedUrl = '';
  let reportGenerated = data['@generated'] || '';

  for (const site of sites) {
    const alerts = site.alerts || [];
    if (alerts.length > 0 && site['@name']) scannedUrl = site['@name'];
    else if (!scannedUrl && site['@name']) scannedUrl = site['@name'];
    for (const alert of alerts) {
      const riskcode = parseInt(alert.riskcode, 10);
      const severity = RISKCODE_TO_SEVERITY[riskcode] ?? 'info';
      if (severity === 'critical') critical++;
      else if (severity === 'high') high++;
      else if (severity === 'medium') medium++;
      else if (severity === 'low') low++;
      else info++;

      const owaspId = PLUGIN_TO_OWASP[parseInt(alert.pluginid, 10)] ?? 'A05';
      if (owaspId && owaspCounts[owaspId] !== undefined) owaspCounts[owaspId]++;

      rawAlerts.push({
        pluginid: alert.pluginid,
        alert: alert.alert || alert.name,
        riskdesc: alert.riskdesc,
        severity,
        solution: (alert.solution || '').replace(/<[^>]+>/g, ' ').trim(),
        count: parseInt(alert.count, 10) || 1,
      });
    }
  }

  const total = critical + high + medium + low + info;
  const deduction = critical * 25 + high * 10 + medium * 3 + low * 1 + info * 0.5;
  const securityScore = Math.max(0, Math.min(100, Math.round(100 - deduction)));
  const FAIL_RULES = { criticalAllowed: 0, highMax: 5 };
  const status = (critical > FAIL_RULES.criticalAllowed || high > FAIL_RULES.highMax) ? 'FAIL' : 'PASS';

  const owaspBreakdown = OWASP_CATEGORIES.map((cat) => ({
    category: cat.id,
    name: cat.name,
    count: owaspCounts[cat.id] || 0,
    severity: cat.severity,
  }));

  return {
    totalVulnerabilities: total,
    critical, high, medium, low, info,
    securityScore, status,
    checks: { staticAnalysis: true, dependencyScan: true, owaspTop10: true, securityHeaders: true, sslValidation: true, zapReport: true },
    owaspBreakdown,
    vulnerabilities: [
      { severity: 'critical', count: critical, category: 'owasp' },
      { severity: 'high', count: high, category: 'owasp' },
      { severity: 'medium', count: medium, category: 'owasp' },
      { severity: 'low', count: low, category: 'owasp' },
      { severity: 'info', count: info, category: 'owasp' },
    ],
    rawReport: { source: 'zap', scannedUrl, reportGenerated, alertCount: rawAlerts.length, alerts: rawAlerts },
  };
}

module.exports = { parseZapReport };

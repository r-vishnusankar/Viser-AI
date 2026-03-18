function buildJsonReport(buildId, security, performance, overallStatus, metadata = {}) {
  return {
    buildId,
    generatedAt: new Date().toISOString(),
    overallStatus,
    summary: {
      security: { score: security.securityScore, status: security.status, totalVulnerabilities: security.totalVulnerabilities },
      performance: { status: performance.status, avgResponseTimeMs: performance.avgResponseTimeMs, errorRatePercent: performance.errorRatePercent },
    },
    security: { ...security, rawReport: undefined },
    performance: { avgResponseTimeMs: performance.avgResponseTimeMs, p95ResponseTimeMs: performance.p95ResponseTimeMs, errorRatePercent: performance.errorRatePercent, throughputRps: performance.throughputRps, maxConcurrentUsers: performance.maxConcurrentUsers, status: performance.status, sampleData: performance.sampleData },
    metadata: { ...metadata, reportVersion: '1.0' },
  };
}

module.exports = { buildJsonReport };

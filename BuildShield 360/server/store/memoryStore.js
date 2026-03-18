const builds = [];

function add(build) {
  builds.unshift(build);
  return build;
}

function findByBuildId(buildId) {
  return builds.find((b) => b.buildId === buildId) || null;
}

function list(limit = 20, skip = 0) {
  return builds.slice(skip, skip + limit);
}

function count() {
  return builds.length;
}

function trend(limit = 10) {
  return builds.slice(0, limit).map((b) => ({
    buildId: b.buildId,
    triggeredAt: b.triggeredAt,
    overallStatus: b.overallStatus,
    security: b.security ? { securityScore: b.security.securityScore, status: b.security.status } : {},
    performance: b.performance ? { avgResponseTimeMs: b.performance.avgResponseTimeMs, errorRatePercent: b.performance.errorRatePercent, status: b.performance.status } : {},
  })).reverse();
}

module.exports = { add, findByBuildId, list, count, trend };

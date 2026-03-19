const express = require('express');
const { v4: uuidv4 } = require('uuid');
const Build = require('../models/Build');
const { isConnected } = require('../config/database');
const memoryStore = require('../store/memoryStore');
const { runSecurityScanAsync } = require('../engines/securityEngine');
const { runPerformanceTest } = require('../engines/performanceEngine');
const { buildJsonReport } = require('../modules/reporting');
const { runZapScan } = require('../integrations/zapScannerClient');
const fs = require('fs');
const path = require('path');

const router = express.Router();

function loadLastScanJobs() {
  try {
    const p = path.resolve(process.cwd(), 'zap_scanner', 'scan_progress.json');
    if (fs.existsSync(p)) {
      const data = JSON.parse(fs.readFileSync(p, 'utf8'));
      return data.scanJobs || [];
    }
  } catch (_) {}
  return [];
}

router.post('/trigger', async (req, res) => {
  const buildId = `BSH-${Date.now()}-${uuidv4().slice(0, 8)}`;
  const triggeredBy = req.body?.triggeredBy || req.query?.triggeredBy || 'api';
  const startTime = Date.now();

  try {
    const targetUrl = req.body?.targetUrl ?? req.query?.targetUrl;
    const zapReportPath = req.body?.zapReportPath ?? req.query?.zapReportPath ?? process.env.ZAP_REPORT_PATH;

    let zapScanJobs = [];
    if (targetUrl) {
      try {
        const zapResult = await runZapScan(targetUrl);
        zapScanJobs = zapResult.scanJobs || [];
      } catch (zapErr) {
        console.warn('ZAP scanner unreachable or failed:', zapErr.message);
        return res.status(503).json({
          success: false,
          error: `ZAP scan failed: ${zapErr.message}. Ensure zap_scanner is running (python zap_scanner/app.py) and ZAP is installed.`,
        });
      }
    }

    const effectiveZapPath = zapReportPath ?? 'zap_scanner/zap_report.json';
    if (zapScanJobs.length === 0 && !targetUrl) {
      zapScanJobs = loadLastScanJobs();
    }
    const [security, performance] = await Promise.all([
      runSecurityScanAsync({ zapReportPath: effectiveZapPath }),
      Promise.resolve(runPerformanceTest()),
    ]);

    const overallStatus = (security.status === 'FAIL' || performance.status === 'FAIL') ? 'FAIL' : 'PASS';
    const durationMs = Date.now() - startTime;

    const jsonReport = buildJsonReport(buildId, security, performance, overallStatus, {
      durationMs,
      branch: req.body?.branch || 'main',
      commit: req.body?.commit || 'simulated',
    });

    const buildPayload = {
      buildId,
      triggeredAt: new Date(),
      triggeredBy,
      overallStatus,
      security,
      performance,
      jsonReport,
      metadata: {
        branch: req.body?.branch || 'main',
        commit: req.body?.commit || 'simulated',
        durationMs,
        targetUrl: targetUrl || security?.rawReport?.scannedUrl,
        zapScanJobs,
      },
    };

    if (isConnected()) {
      const build = new Build(buildPayload);
      await build.save();
    } else {
      memoryStore.add(buildPayload);
    }

    res.status(201).json({
      success: true,
      buildId,
      overallStatus,
      security: { score: security.securityScore, status: security.status },
      performance: { status: performance.status, avgResponseTimeMs: performance.avgResponseTimeMs },
      durationMs,
      reportUrl: `/api/builds/${buildId}`,
    });
  } catch (err) {
    console.error('Build trigger error:', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

router.get('/', async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit, 10) || 20, 100);
  const skip = parseInt(req.query.skip, 10) || 0;
  try {
    if (isConnected()) {
      const builds = await Build.find().sort({ triggeredAt: -1 }).skip(skip).limit(limit).lean();
      const total = await Build.countDocuments();
      return res.json({ builds, total, limit, skip });
    }
    res.json({ builds: memoryStore.list(limit, skip), total: memoryStore.count(), limit, skip });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/trend', async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit, 10) || 10, 50);
  try {
    if (isConnected()) {
      const builds = await Build.find().sort({ triggeredAt: -1 }).limit(limit).select('buildId triggeredAt overallStatus security performance').lean();
      return res.json({ builds: builds.reverse() });
    }
    res.json({ builds: memoryStore.trend(limit) });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/:buildId', async (req, res) => {
  try {
    if (isConnected()) {
      const build = await Build.findOne({ buildId: req.params.buildId }).lean();
      if (!build) return res.status(404).json({ error: 'Build not found' });
      return res.json(build);
    }
    const build = memoryStore.findByBuildId(req.params.buildId);
    if (!build) return res.status(404).json({ error: 'Build not found' });
    res.json(build);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

router.get('/:buildId/report', async (req, res) => {
  try {
    if (isConnected()) {
      const build = await Build.findOne({ buildId: req.params.buildId }).lean();
      if (!build) return res.status(404).json({ error: 'Build not found' });
      return res.json(build.jsonReport || build);
    }
    const build = memoryStore.findByBuildId(req.params.buildId);
    if (!build) return res.status(404).json({ error: 'Build not found' });
    res.json(build.jsonReport || build);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;

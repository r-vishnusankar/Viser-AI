/**
 * Calls the ZAP scanner (zap_scanner Flask app) to run a scan against a URL.
 * Requires zap_scanner to be running (e.g. python zap_scanner/app.py on port 5001).
 */

async function runZapScan(targetUrl) {
  const baseUrl = process.env.ZAP_SCANNER_URL || 'http://localhost:5001';
  const res = await fetch(`${baseUrl}/api/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url: targetUrl }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `ZAP scanner returned ${res.status}`);
  }
  if (!data.success) {
    throw new Error(data.error || 'ZAP scan failed');
  }
  return data;
}

module.exports = { runZapScan };

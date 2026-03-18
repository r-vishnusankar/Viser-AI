# ZAP Scanner & BuildShield 360 Integration Analysis

## 1. ZAP Scanner Overview

### Location & Stack
- **Path:** `zap_scanner/`
- **Stack:** Flask (Python), OWASP ZAP CLI, Matplotlib
- **ZAP Version:** 2.16.1 (ZAP by Checkmarx)

### How It Works
| Component | Description |
|----------|-------------|
| **Entry** | `app.py` – Flask app with `/`, `/report`, `/scan` |
| **Trigger** | `POST /scan` with form field `url` |
| **Automation** | Generates `zap.yaml` dynamically with target URL |
| **Scan Flow** | Spider (5 min) → Spider Ajax (5 min) → Passive scan wait (5 min) → Active scan → Reports |
| **Output** | `zap_report.json` (traditional-json), `zap_report.html` (traditional-html) |
| **Visualization** | Matplotlib bar chart of risk levels → `static/zap_risk_levels.png` |

### ZAP Report JSON Structure
```json
{
  "@programName": "ZAP",
  "@version": "2.16.1",
  "site": [{
    "@name": "https://target.com",
    "alerts": [{
      "pluginid": "10038",
      "alert": "Content Security Policy (CSP) Header Not Set",
      "riskcode": "2",        // 0=Info, 1=Low, 2=Medium, 3=High, 4=Critical
      "riskdesc": "Medium (High)",
      "instances": [{ "uri": "...", "method": "GET" }],
      "solution": "...",
      "cweid": "693",
      "wascid": "15"
    }]
  }]
}
```

### Sample Alerts from Your Report
| Plugin ID | Alert | Risk | OWASP Category |
|-----------|-------|------|----------------|
| 10038 | Content Security Policy (CSP) Header Not Set | Medium | A05 Security Misconfiguration |
| 10020 | Missing Anti-clickjacking Header | Medium | A05 |
| 10035 | Strict-Transport-Security Header Not Set | Low | A05 |
| 10021 | X-Content-Type-Options Header Missing | Low | A05 |
| 10116 | ZAP is Out of Date | Low | — |
| 10027 | Information Disclosure - Suspicious Comments | Info | A09 Logging |
| 10109 | Modern Web Application | Info | — |
| 10015 | Re-examine Cache-control Directives | Info | A08 Data Integrity |

---

## 2. BuildShield 360 Overview

### Current Security Engine
- **File:** `server/engines/securityEngine.js`
- **Behavior:** Simulated/random data only – no real ZAP integration
- **Output shape:** `{ critical, high, medium, low, info, securityScore, status, owaspBreakdown, vulnerabilities }`
- **Fail rules:** Critical > 0 or High > 5 → FAIL

### Expected Security Payload (for dashboard)
```javascript
{
  totalVulnerabilities, critical, high, medium, low, info,
  securityScore,      // 0–100
  status,             // 'PASS' | 'FAIL'
  owaspBreakdown,    // [{ category, name, count, severity }]
  vulnerabilities,   // [{ severity, count, category }]
  checks: { staticAnalysis, dependencyScan, owaspTop10, securityHeaders, sslValidation }
}
```

### ZAP in Documentation vs Code
- **BUILDSHIELD-360.md** describes ZAP integration via `USE_OWASP_ZAP`, `ZAP_API_URL`, `ZAP_TARGET_URL`
- **Reality:** No ZAP-related code in `server/` – no `/api/zap/status`, no ZAP API client, no report parsing

---

## 3. Integration Options

### Option A: ZAP Report File Integration (Recommended First Step)

**Idea:** Parse `zap_report.json` and feed it into BuildShield 360’s security engine.

| Pros | Cons |
|------|------|
| Uses existing ZAP scanner output | Requires ZAP scan to run before build trigger |
| No ZAP daemon needed | Report path must be configurable |
| Same format as current ZAP scanner | Two-step flow (scan → trigger) |

**Flow:**
1. User runs ZAP scan (via `zap_scanner` or manually) → `zap_report.json`
2. Build trigger accepts optional `zapReportPath` or reads from env `ZAP_REPORT_PATH`
3. If report exists → parse and use real data; else → fallback to simulated scan

---

### Option B: ZAP API Integration (As Documented)

**Idea:** Use ZAP REST API when ZAP runs in daemon mode.

| Pros | Cons |
|------|------|
| Real-time scan on trigger | Needs ZAP daemon (Docker or installed) |
| Single-step flow | Scan can take 10–15+ minutes |
| Matches documented design | Need to handle long-running scans (async/job queue) |

**Flow:**
1. ZAP daemon: `docker run -p 8080:8080 owasp/zap2docker-stable zap.sh -daemon`
2. Build trigger → call ZAP API to start scan on `ZAP_TARGET_URL`
3. Poll for completion or use webhooks
4. Fetch alerts via `/json/view/alerts/` and map to BuildShield format

---

### Option C: Unified ZAP CLI from BuildShield (Full Automation)

**Idea:** BuildShield triggers ZAP CLI directly (similar to `zap_scanner`).

| Pros | Cons |
|------|------|
| One system, one trigger | Requires ZAP installed on server |
| No separate Flask app | Long scan blocks build (or needs async) |
| Full control over scan config | Platform-specific (e.g. `zap.bat` on Windows) |

**Flow:**
1. `POST /api/builds/trigger` with `{ targetUrl: "https://..." }`
2. Server spawns ZAP CLI with automation YAML
3. Waits for scan (or runs async and stores result when done)
4. Parses `zap_report.json` and stores build with real security data

---

## 4. Recommended Implementation Path

### Phase 1: Report File Parser (Low Effort)
1. Add `server/integrations/zapReportParser.js`:
   - `parseZapReport(jsonPath)` → returns `{ critical, high, medium, low, info, owaspBreakdown, rawAlerts }`
   - Map ZAP `riskcode` (0–4) to severity
   - Map plugin IDs / CWE to OWASP Top 10 where possible
2. Update `securityEngine.js`:
   - If `ZAP_REPORT_PATH` is set and file exists → use parser output
   - Else → keep current simulated scan
3. Add env: `ZAP_REPORT_PATH=./zap_scanner/zap_report.json`

### Phase 2: Trigger with Report Path
1. Extend `POST /api/builds/trigger` body: `{ zapReportPath?: string }`
2. If provided, parse that file instead of default path
3. Enables: run ZAP scan → trigger build with path to latest report

### Phase 3: ZAP API Integration (Optional)
1. Add `server/integrations/zapApi.js`:
   - `startScan(targetUrl)`, `getAlerts()`, `getStatus()`
2. Add `GET /api/zap/status` as documented
3. When `USE_OWASP_ZAP=true`, security engine calls ZAP API instead of using report file

---

## 5. ZAP → BuildShield Data Mapping

### Severity Mapping
| ZAP riskcode | ZAP riskdesc | BuildShield severity |
|--------------|--------------|----------------------|
| 4 | Critical | critical |
| 3 | High | high |
| 2 | Medium | medium |
| 1 | Low | low |
| 0 | Informational | info |

### Score Calculation (align with current engine)
```javascript
const deduction = critical * 25 + high * 10 + medium * 3 + low * 1 + info * 0.5;
const securityScore = Math.max(0, Math.min(100, Math.round(100 - deduction)));
```

### OWASP Top 10 Mapping (Plugin ID / CWE → Category)
| OWASP | Category | ZAP Indicators |
|-------|----------|----------------|
| A01 | Broken Access Control | pluginid 40014, 40018, etc. |
| A02 | Cryptographic Failures | HSTS, TLS-related alerts |
| A03 | Injection | XSS, SQLi, command injection |
| A05 | Security Misconfiguration | 10038 (CSP), 10020 (X-Frame), 10035 (HSTS), 10021 (X-Content-Type) |
| A08 | Data Integrity | 10015 (Cache-Control) |
| A09 | Logging | 10027 (Suspicious Comments) |

---

## 6. Summary

| Aspect | ZAP Scanner | BuildShield 360 | Integration Gap |
|--------|-------------|-----------------|-----------------|
| **Purpose** | Run ZAP, produce JSON/HTML | Build quality dashboard | No link between them |
| **Security data** | Real (from ZAP) | Simulated (random) | Need parser + wiring |
| **Report format** | `site[].alerts[]` | `critical, high, medium, low, info` | Straightforward mapping |
| **Best first step** | — | — | Parse `zap_report.json` in security engine |

**Next step:** Implement Phase 1 (report file parser) so BuildShield 360 can consume real ZAP results from `zap_scanner` or any `traditional-json` report.

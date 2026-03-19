# ZAP Security Report: practicetestautomation.com

**Target URL:** https://practicetestautomation.com/practice-test-login/  
**Report generated:** 2026-03-18  
**Tool:** OWASP ZAP (BuildShield 360 integration)

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total findings** | 6 |
| **Critical** | 0 |
| **High** | 0 |
| **Medium** | 2 |
| **Low** | 2 |
| **Informational** | 2 |
| **Security score** | ~85% |
| **Status** | PASS |

---

## Findings by Priority

### Medium (2)

| # | Finding | Solution |
|---|---------|----------|
| 1 | **Content Security Policy (CSP) Header Not Set** | Ensure that your web server is configured to set the Content-Security-Policy header to mitigate XSS and data injection attacks. |
| 2 | **Missing Anti-clickjacking Header** | Set X-Frame-Options or Content-Security-Policy frame-ancestors to prevent clickjacking. |

### Low (2)

| # | Finding | Solution |
|---|---------|----------|
| 3 | **Strict-Transport-Security Header Not Set** | Configure HSTS header to enforce HTTPS connections. |
| 4 | **X-Content-Type-Options Header Missing** | Set X-Content-Type-Options: nosniff to prevent MIME-sniffing. |

### Informational (2)

| # | Finding | Solution |
|---|---------|----------|
| 5 | **Re-examine Cache-control Directives** | For login pages, set cache-control: no-cache, no-store, must-revalidate to prevent credential caching. |
| 6 | **Modern Web Application** | Informational only - no action required. |

---

## Recommendations

1. **Add security headers** – Configure your web server (or CDN) to send:
   - `Content-Security-Policy`
   - `X-Frame-Options: DENY` or `SAMEORIGIN`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `X-Content-Type-Options: nosniff`

2. **Login page caching** – Ensure the login page and any pages with sensitive data use `Cache-Control: no-cache, no-store, must-revalidate`.

3. **Re-scan after fixes** – Run ZAP again after applying changes to verify remediation.

---

## What Was Tested

- **Spider** – Crawled the login page and linked resources
- **Passive scan** – Analyzed responses for security headers, information disclosure
- **Active scan** – Tested for common vulnerabilities (XSS, injection, etc.)

The page is a simple login form (Practice Test Automation). No critical or high-severity issues were found. The findings are primarily missing or weak security headers.

# BuildShield 360

**Automated Build Quality Intelligence System** — DevSecOps POC for executive visibility.

When a new build is triggered, the system automatically runs **security** and **performance** tests, stores results (MongoDB or in-memory), and displays them in a modern dark-themed dashboard.

---

## Features

- **CI/CD trigger** — Simulate build via API or dashboard button; runs security + performance tests and stores results.
- **Security testing** — Simulated: static analysis, dependency scan, OWASP Top 10, security headers, SSL validation.  
  **Real (optional):** OWASP ZAP — set `USE_OWASP_ZAP=true` and `ZAP_TARGET_URL` to use live ZAP alerts.  
  - **Fail rules:** Build fails if any **Critical** exists or **High** > 5.
- **Performance testing (simulated)** — Load test metrics: avg/p95 response time, error rate, throughput, max concurrent users.  
  - **Fail rules:** Build fails if avg response time > 1000 ms or error rate > 2%.
- **Dashboard** — Summary cards (Build ID, Security Score, Performance Score, Overall Status), vulnerability charts, OWASP breakdown, response time and load graphs, trend analytics with regression detection.
- **Future-ready placeholders** — Slack, email, JMeter, real security tool integrations in `server/integrations/`.

---

## Tech Stack

| Layer    | Stack                  |
|----------|------------------------|
| Backend  | Node.js, Express       |
| Database | MongoDB (optional; in-memory fallback) |
| Frontend | React (Vite), Recharts |

---

## Quick Start

### Prerequisites

- **Node.js** 18+
- **MongoDB** (optional) — if not running, app uses in-memory store

### 1. Install dependencies

```bash
npm run install:all
```

### 2. Start backend and frontend

```bash
npm run dev
```

- **API:** http://localhost:5000  
- **Dashboard:** http://localhost:3000  

### 3. Trigger a build

- Click **Trigger new build** in the dashboard, or  
- `POST /api/builds/trigger` with optional body: `{ "triggeredBy": "api", "branch": "main", "commit": "abc123" }`

---

## Project Structure

```
BuildShield 360/
├── server/
│   ├── config/         # DB connection (optional MongoDB)
│   ├── engines/        # Security & performance engines
│   ├── integrations/   # OWASP ZAP, Slack, email, JMeter placeholders
│   ├── models/         # Mongoose Build model
│   ├── modules/        # Reporting (JSON report generation)
│   ├── store/          # In-memory store when MongoDB unavailable
│   ├── routes/         # /api/builds
│   └── index.js        # Express app
├── client/             # React + Vite + Recharts
│   └── src/
│       ├── api/        # Build API client
│       ├── components/ # SummaryCards, Security, Performance, Trend
│       ├── App.jsx
│       └── index.css   # Dark theme variables
├── package.json
├── .env.example
└── BUILDSHIELD-360.md  # This file
```

---

## API

| Method | Endpoint                      | Description                          |
|--------|-------------------------------|--------------------------------------|
| POST   | `/api/builds/trigger`         | Run security + perf tests, store build |
| GET    | `/api/builds`                 | List builds (`?limit=&skip=`)        |
| GET    | `/api/builds/trend`           | Last N builds for trends             |
| GET    | `/api/builds/:buildId`        | Single build + full report           |
| GET    | `/api/builds/:buildId/report` | JSON report only                     |
| GET    | `/api/zap/status`             | ZAP configured + reachable           |
| GET    | `/health`                     | Health check                         |

---

## Environment

Copy `.env.example` to `.env` and set:

| Variable        | Description                                      | Default                          |
|----------------|--------------------------------------------------|----------------------------------|
| PORT           | API port                                        | 5000                             |
| MONGODB_URI    | MongoDB connection string                       | mongodb://localhost:27017/buildshield360 |
| USE_OWASP_ZAP  | Use real OWASP ZAP for security                 | —                                |
| ZAP_API_URL    | ZAP API base URL                                | http://127.0.0.1:8080            |
| ZAP_TARGET_URL | Target URL to scan (when USE_OWASP_ZAP=true)    | —                                |
| ZAP_REPORT_PATH | Path to ZAP JSON report (traditional-json)     | zap_scanner/zap_report.json      |

---

## OWASP ZAP (Real Security Scan)

1. **Run ZAP** (API mode), e.g. Docker:
   ```bash
   docker run -u zap -p 8080:8080 owasp/zap2docker-stable zap.sh -daemon
   ```
2. **Scan your target** so ZAP has alerts for that URL (ZAP Desktop/CLI or API).
3. **Configure** in `.env`:
   ```env
   USE_OWASP_ZAP=true
   ZAP_API_URL=http://127.0.0.1:8080
   ZAP_TARGET_URL=https://your-app.com
   ```
4. **Trigger a build** — security result uses ZAP alerts (High/Medium/Low/Informational) and OWASP category mapping.

**Check status:** `GET http://localhost:5000/api/zap/status` → `{ configured, reachable, zapApiUrl }`. If ZAP is unreachable, the engine falls back to the simulated scan.

### ZAP Integration (Implemented)

**Two ways to get security data:**

| Mode | What you do | Result |
|------|-------------|--------|
| **Real ZAP scan** | 1. Start zap_scanner: `python zap_scanner/app.py` (port 5001) 2. Enter URL in dashboard 3. Click Trigger | BuildShield calls ZAP scanner → runs ZAP against URL → uses real report |
| **Existing report** | `zap_report.json` already exists in `zap_scanner/` (from prior scan) | BuildShield uses that file; no URL needed |
| **Simulated** | No URL, no report file | Random demo data |

**API:** `POST /api/builds/trigger` body: `{ "targetUrl": "https://example.com" }` to run ZAP scan. Omit for report-file or simulated.

---

## How It Works

1. **Trigger** — Dashboard or `POST /api/builds/trigger` runs security and performance engines (parallel).
2. **Security** — Either real ZAP (if configured) or simulated checks; outputs vulnerability counts, score %, PASS/FAIL.
3. **Performance** — Simulated load metrics; outputs response time, RPS, error rate, PASS/FAIL.
4. **Store** — Build document saved to MongoDB or in-memory store; JSON report generated.
5. **Dashboard** — Fetches latest build + trend; shows summary cards, security charts, performance charts, trend table and regression notice.

---

## License

MIT (POC — use as reference only).

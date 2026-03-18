# ZAP Scanner Troubleshooting

## Why the ZAP scanner might not be working

### 1. **zap_scanner Flask app is not running**

BuildShield 360 calls the ZAP scanner at `http://localhost:5001`. If the Flask app isn't running, you get **"Unable to connect"** or **"ECONNREFUSED"**.

**Fix:** Start the scanner in a **separate terminal** before triggering a build with a URL:

```powershell
cd "c:\Users\Vishnu\Desktop\AI_Product_Lab\03_Research\BuildShield 360"
python zap_scanner/app.py
```

You should see: `Running on http://127.0.0.1:5001`

---

### 2. **ZAP is not installed or wrong path**

The app expects ZAP at: `C:\Program Files\ZAP\Zed Attack Proxy\zap.bat`

**Check:** Does this file exist?
```powershell
Test-Path "C:\Program Files\ZAP\Zed Attack Proxy\zap.bat"
```

**Fix:** 
- Install [OWASP ZAP](https://www.zaproxy.org/download/) if missing
- If ZAP is elsewhere, edit `zap_scanner/app.py` and set `ZAP_PATH` and the `cwd` in `subprocess.run` to your ZAP install folder

---

### 3. **Report written to wrong folder**

ZAP may write `zap_report.json` to its own install directory instead of `zap_scanner/`. The app was updated to use an absolute path for `reportDir` in the YAML.

**Check:** After a scan, look for:
- `zap_scanner/zap_report.json` (correct)
- `C:\Program Files\ZAP\Zed Attack Proxy\zap_report.json` (wrong – old behavior)

---

### 4. **Chrome/Chromium for AJAX spider**

The spider job uses `browserId: chrome-headless`. ZAP needs Chrome or Chromium for this.

**Fix:** Install Chrome, or change the YAML to use `firefox-headless` if you have Firefox.

---

### 5. **Port 5001 in use**

If another app uses port 5001, the Flask app will fail to start.

**Fix:** Edit `zap_scanner/app.py` and change the port, then set `ZAP_SCANNER_URL=http://localhost:NEW_PORT` in your environment when running BuildShield.

---

## Quick diagnostic

Run this to verify your setup:

```powershell
# 1. ZAP installed?
Test-Path "C:\Program Files\ZAP\Zed Attack Proxy\zap.bat"

# 2. Python + Flask?
python -c "import flask; print('Flask OK')"

# 3. Start zap_scanner (in one terminal)
python zap_scanner/app.py

# 4. In another terminal, test the API
Invoke-RestMethod -Uri "http://localhost:5001/api/scan" -Method POST -ContentType "application/json" -Body '{"url":"https://example.com"}' -TimeoutSec 120
```

---

## Workflow summary

| Step | Action |
|------|--------|
| 1 | Start **BuildShield 360**: `npm run dev` |
| 2 | Start **zap_scanner**: `python zap_scanner/app.py` (separate terminal) |
| 3 | Enter URL in dashboard, click **Trigger new build** |
| 4 | Wait 5–15 min for ZAP scan to finish |

Without a URL, BuildShield uses `zap_report.json` if it exists, or simulated data.

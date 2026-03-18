# app.py
from flask import Flask, render_template, request, jsonify, send_from_directory
import subprocess
import json
import os

app = Flask(__name__)

ZAP_PATH = os.environ.get('ZAP_PATH', r"C:\Program Files\ZAP\Zed Attack Proxy\zap.bat")
ZAP_CWD = os.environ.get('ZAP_CWD', r"C:\Program Files\ZAP\Zed Attack Proxy")
SCAN_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check for BuildShield 360."""
    zap_ok = os.path.exists(ZAP_PATH)
    return jsonify({"status": "ok", "zap_installed": zap_ok, "zap_path": ZAP_PATH})


@app.route('/report')
def serve_report():
    return send_from_directory(SCAN_DIR, 'zap_report.html')

def _parse_zap_output(output):
    """Parse ZAP automation output into job status list."""
    import re
    jobs = []
    lines = output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        # Job X started
        m = re.match(r"Job (\S+) started", line, re.I)
        if m:
            name = m.group(1)
            status = "completed"
            detail = ""
            duration = ""
            for j in range(i + 1, min(i + 8, len(lines))):
                if re.match(rf"Job {re.escape(name)} finished", lines[j], re.I):
                    tm = re.search(r"time taken: (\S+)", lines[j])
                    if tm:
                        duration = tm.group(1)
                    break
                u = re.search(r"found (\d+) URLs?", lines[j], re.I)
                if u:
                    detail = f"{u.group(1)} URLs"
            jobs.append({"name": name, "status": status, "detail": detail, "duration": duration})
        i += 1
    # Report generation lines
    for line in lines:
        m = re.search(r"Job report generated report (.+)", line)
        if m:
            fname = m.group(1).replace("\\", "/").split("/")[-1]
            jobs.append({"name": "report", "status": "completed", "detail": fname, "duration": ""})
    if not jobs:
        jobs = [{"name": "automation", "status": "completed", "detail": "Plan succeeded", "duration": ""}]
    return jobs


def _run_zap_scan(base_url):
    """Run ZAP scan against base_url. Returns { error: str } on failure, {} on success."""
    # Use absolute path so report is written to zap_scanner folder (not ZAP install dir)
    report_dir = SCAN_DIR.replace('\\', '/')
    zap_yaml_content = f"""
env:
  contexts:
  - name: Default Context
    urls:
    - {base_url}/
    includePaths:
    - {base_url}/.*

jobs:
- type: spider
  parameters:
    maxDuration: 5

- type: spiderAjax
  parameters:
    browserId: chrome-headless
    maxDuration: 5

- type: passiveScan-wait
  parameters:
    maxDuration: 5

- type: activeScan

- type: report
  parameters:
    template: traditional-json
    reportDir: {report_dir}
    reportFile: zap_report.json

- type: report
  parameters:
    template: traditional-html
    reportDir: {report_dir}
    reportFile: zap_report.html
"""

    zap_yaml_file = os.path.join(SCAN_DIR, "zap.yaml")
    with open(zap_yaml_file, "w") as f:
        f.write(zap_yaml_content)

    if not os.path.exists(ZAP_PATH):
        return {"error": f"ZAP not found at {ZAP_PATH}. Install OWASP ZAP or set ZAP_PATH env var."}

    try:
        result = subprocess.run(
            [ZAP_PATH, "-cmd", "-autorun", zap_yaml_file],
            cwd=ZAP_CWD,
            check=True,
            capture_output=True,
            text=True,
            timeout=600,
        )
        output = (result.stdout or "") + (result.stderr or "")
    except subprocess.TimeoutExpired:
        return {"error": "ZAP scan timed out after 10 minutes"}
    except subprocess.CalledProcessError as e:
        return {"error": f"ZAP scan failed: {e}"}

    json_report = os.path.join(SCAN_DIR, "zap_report.json")
    if not os.path.exists(json_report):
        return {"error": "ZAP scan did not produce JSON report"}

    # Parse ZAP output for job status and save for BuildShield (when using existing report)
    scan_jobs = _parse_zap_output(output)
    progress_file = os.path.join(SCAN_DIR, "scan_progress.json")
    with open(progress_file, "w") as f:
        json.dump({"scanJobs": scan_jobs, "targetUrl": base_url, "completedAt": __import__("datetime").datetime.utcnow().isoformat() + "Z"}, f)
    return {"scanJobs": scan_jobs}


@app.route('/api/scan', methods=['POST'])
def api_scan():
    """JSON API for BuildShield 360 - accepts JSON body { "url": "https://..." }"""
    data = request.get_json() or {}
    base_url = data.get('url') or request.form.get('url')
    if not base_url:
        return jsonify({"error": "No URL provided", "success": False}), 400
    result = _run_zap_scan(base_url)
    if result.get('error'):
        return jsonify({"error": result['error'], "success": False}), 500
    return jsonify({
        "success": True,
        "reportPath": "zap_report.json",
        "targetUrl": base_url,
        "scanJobs": result.get("scanJobs", []),
    })


@app.route('/scan', methods=['POST'])
def scan():
    base_url = request.form.get('url')
    if not base_url:
        return jsonify({"error": "No URL provided"}), 400

    result = _run_zap_scan(base_url)
    if result.get('error'):
        return jsonify({"error": result['error']}), 500

    json_report = os.path.join(SCAN_DIR, "zap_report.json")
    with open(json_report) as f:
        data = json.load(f)

    risk_count = {"High": 0, "Medium": 0, "Low": 0, "Informational": 0}

    for site in data.get("site", []):
        alerts = site.get("alerts", [])
        for alert in alerts:
            riskdesc = alert.get("riskdesc", "").split()[0]  # e.g., "Medium (High)" → "Medium"
            if riskdesc in risk_count:
                risk_count[riskdesc] += 1

    # Generate bar chart (matplotlib only needed for /scan HTML route, not /api/scan)
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return render_template('index.html', report=True)  # Skip graph if matplotlib missing

    graph_file = os.path.join(SCAN_DIR, "static", "zap_risk_levels.png")
    os.makedirs(os.path.dirname(graph_file), exist_ok=True)
    plt.figure(figsize=(6,4))
    plt.bar(risk_count.keys(), risk_count.values(), color=['red','orange','yellow','blue'])
    plt.title("ZAP Risk Levels")
    plt.xlabel("Risk Level")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(graph_file)
    plt.close()

    # Return page with HTML report and graph
    return render_template('index.html', graph="static/zap_risk_levels.png", report=True)


if __name__ == '__main__':
    app.run(debug=True, port=5001)  # 5001 to avoid conflict with BuildShield API (5000)
#!/usr/bin/env python3
"""
Viser AI — Combined Launcher  (Core Engine 2.0 only)
Starts both Core Engine servers:

  • web_ui_v2.py  → http://localhost:5000  (Core Engine dashboard — standalone)
  • app.py        → http://localhost:8080  (splash/landing page, optional)

NOTE: The recommended way to run the FULL Viser AI stack is:
      python ../flask_server.py          (port 8000 — everything in one server)
      http://localhost:8000              → main Viser AI
      http://localhost:8000/automation   → Core Engine 2.0 dashboard (embedded)

Usage:
    python launch.py               # Core Engine only (dashboard + splash)
    python web_ui_v2.py            # Core Engine dashboard only
"""

import subprocess
import sys
import time
import signal
from pathlib import Path

BASE_DIR = Path(__file__).parent
processes: list[tuple[str, subprocess.Popen]] = []


def start_server(script: str, port: int, label: str) -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, str(BASE_DIR / script)],
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    processes.append((label, proc))
    print(f"  [{label}] Started (pid={proc.pid}) → http://localhost:{port}")
    return proc


def stream_output(label: str, proc: subprocess.Popen) -> None:
    import threading

    def _read():
        for line in iter(proc.stdout.readline, ''):
            print(f"  [{label}] {line}", end='')

    threading.Thread(target=_read, daemon=True).start()


def shutdown(sig=None, frame=None) -> None:
    print("\n🛑 Shutting down all servers...")
    for label, proc in processes:
        if proc.poll() is None:
            proc.terminate()
            print(f"  [{label}] Terminated")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("=" * 55)
    print("  🚀 Viser AI — Full Stack Launcher")
    print("=" * 55)

    # Main AI dashboard (port 5000) — start first
    p1 = start_server("web_ui_v2.py", 5000, "Dashboard")
    stream_output("Dashboard", p1)
    time.sleep(2)

    # Optional splash page (port 8080)
    p2 = start_server("app.py", 8080, "Splash")
    stream_output("Splash", p2)
    time.sleep(1)

    print()
    print("  ✅ Core Engine servers running:")
    print("     🤖 Dashboard  → http://localhost:5000")
    print("     🏠 Splash     → http://localhost:8080")
    print("     📋 Full UI    → http://localhost:8080/main   (embeds dashboard)")
    print()
    print("  💡 For the FULL Viser AI (recommended):")
    print("     Run: python ../flask_server.py")
    print("     Main UI      → http://localhost:8000")
    print("     Automation   → http://localhost:8000/automation")
    print()
    print("  Press Ctrl+C to stop.")
    print("=" * 55)

    # Monitor and auto-restart crashed processes
    try:
        while True:
            for i, (label, proc) in enumerate(processes):
                if proc.poll() is not None:
                    script = "web_ui_v2.py" if label == "Dashboard" else "app.py"
                    port   = 5000            if label == "Dashboard" else 8080
                    print(f"\n  ⚠️  [{label}] crashed — restarting...")
                    new_proc = start_server(script, port, label)
                    stream_output(label, new_proc)
                    processes[i] = (label, new_proc)
            time.sleep(3)
    except KeyboardInterrupt:
        shutdown()

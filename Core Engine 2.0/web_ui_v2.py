#!/usr/bin/env python3
"""
Viser AI — Web UI v2  (single, authoritative server)
Runs on port 5000. Handles planning, execution, plan enhancement,
live logging, page-info tracking, and browser-use / Playwright routing.

Start:  python web_ui_v2.py
        python launch.py          (full stack with splash)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

# ── Python path ───────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent / "src"))

from spec2.ai_planner import AIPlanner, compare
from spec2.intent_router import infer_intent
from settings import settings

# ── Flask + SocketIO ──────────────────────────────────────────────────────────

app = Flask(__name__, template_folder='templates_webui_v2')
app.config['SECRET_KEY'] = 'viser-ai-core-engine-v2-secret'

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
)

# ── State ─────────────────────────────────────────────────────────────────────

_is_running: bool = False          # concurrency guard
_last_page_info: dict | None = None  # replayed to reconnecting clients


# ── Logger ────────────────────────────────────────────────────────────────────

class WebUILogger:
    """Forwards structured log entries to all connected WebSocket clients."""

    def __init__(self, sio: SocketIO) -> None:
        self._sio = sio

    def log(self, level: str, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self._sio.emit('log_message', {'timestamp': ts, 'level': level, 'message': message})
        print(f"[{ts}] {level}: {message}")


ui_logger = WebUILogger(socketio)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _valid_url(url: str) -> bool:
    return url.startswith(('http://', 'https://'))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── Socket: lifecycle ─────────────────────────────────────────────────────────

@socketio.on('connect')
def on_connect():
    ui_logger.log('INFO', '🔗 Client connected')
    # Confirm connection to the client
    emit('status', {'connected': True, 'server': 'Viser AI v2'})
    # Replay last known page state for reconnecting clients
    if _last_page_info:
        emit('page_info', _last_page_info)


@socketio.on('disconnect')
def on_disconnect():
    ui_logger.log('INFO', '👋 Client disconnected')


@socketio.on('test_connection')
def on_test():
    emit('log_message', {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'level': 'INFO',
        'message': '🔗 Connection OK',
    })


# ── Socket: plan_task ─────────────────────────────────────────────────────────

@socketio.on('plan_task')
def on_plan(data):
    """
    Dry-run: generate a plan without executing.
    Runs in a background task to keep the SocketIO thread free during
    the blocking Groq / Gemini API call.
    """
    prompt = (data or {}).get('prompt', '').strip()
    url    = (data or {}).get('url',    '').strip()
    provider = (data or {}).get('provider', 'groq')

    if not prompt:
        emit('error', {'message': 'Please provide a task prompt'})
        return

    socketio.start_background_task(_plan_bg, prompt, url, provider)


def _plan_bg(prompt: str, url: str, provider: str) -> None:
    try:
        ui_logger.log('INFO', f'🎯 Planning: {prompt}')
        if url:
            ui_logger.log('INFO', f'🌐 Target URL: {url}')
        ui_logger.log('INFO', f'🤖 Provider: {provider}')

        intent = infer_intent(prompt)
        ui_logger.log('INFO', f'📋 Intent: {intent}')

        if provider == 'compare':
            _plan_compare(prompt, url, intent)
            return

        planner = AIPlanner(provider)
        plan = planner.plan(prompt, url)

        if plan.get('error'):
            ui_logger.log('ERROR', f'❌ Planning failed: {plan["error"]}')
            socketio.emit('error', {'message': f'Planning failed: {plan["error"]}'})
            return

        steps_count = len(plan.get('steps', []))
        ui_logger.log('SUCCESS', f'✅ Plan ready: {steps_count} steps')

        if plan.get('saved_to'):
            ui_logger.log('INFO', f'📁 Saved: {plan["saved_to"]}')
        else:
            ui_logger.log('WARNING', '⚠️ Plan could not be saved to file')

        socketio.emit('plan_ready', {'type': 'single', 'plan': plan, 'intent': intent})

    except Exception as exc:
        ui_logger.log('ERROR', f'💥 Planning error: {exc}')
        socketio.emit('error', {'message': f'Planning failed: {exc}'})


def _plan_compare(prompt: str, url: str, intent: str) -> None:
    try:
        ui_logger.log('INFO', '🔄 Comparing Groq vs Gemini...')
        results = compare(prompt, url)

        for prov, result in results.items():
            if result.get('error'):
                ui_logger.log('ERROR', f'❌ {prov.upper()}: {result["error"]}')
            else:
                n = len(result.get('steps', []))
                ui_logger.log('INFO', f'✅ {prov.upper()}: {n} steps')

        socketio.emit('plan_ready', {'type': 'compare', 'results': results, 'intent': intent})

    except Exception as exc:
        ui_logger.log('ERROR', f'💥 Compare failed: {exc}')
        socketio.emit('error', {'message': f'Compare failed: {exc}'})


# ── Socket: execute_task ──────────────────────────────────────────────────────

@socketio.on('execute_task')
def on_execute(data):
    """
    Execute a task in the browser.
    Guarded against concurrent runs (_is_running flag).
    """
    global _is_running

    if _is_running:
        emit('error', {'message': '⚠️ A task is already running — please wait for it to finish'})
        return

    url      = (data or {}).get('url',      '').strip()
    prompt   = (data or {}).get('prompt',   '').strip()
    provider = (data or {}).get('provider', 'groq')

    if not url or not prompt:
        emit('error', {'message': 'Please provide both URL and task description'})
        return

    if not _valid_url(url):
        emit('error', {'message': 'Invalid URL — must start with http:// or https://'})
        return

    socketio.emit('task_started', {'url': url, 'prompt': prompt, 'provider': provider})
    socketio.start_background_task(_run_task_bg, url, prompt, provider)


def _run_task_bg(url: str, prompt: str, provider: str) -> None:
    """Background thread: owns its own asyncio event loop."""
    global _is_running
    _is_running = True
    try:
        asyncio.run(_run_task_async(url, prompt, provider))
    except Exception as exc:
        ui_logger.log('ERROR', f'💥 Task failed: {exc}')
        socketio.emit('task_error', {'error': str(exc)})
    finally:
        _is_running = False
        socketio.emit('task_completed')


async def _run_task_async(url: str, prompt: str, provider: str) -> None:
    """Core async execution: plan → show plan → run in browser."""
    global _last_page_info
    from spec2.executor import run_async, run_with_browser_use

    ui_logger.log('INFO', f'🚀 Starting Viser AI...')
    ui_logger.log('INFO', f'📍 URL: {url}')
    ui_logger.log('INFO', f'🎯 Task: {prompt}')
    ui_logger.log('INFO', f'🤖 Provider: {provider}')

    intent = infer_intent(prompt)
    ui_logger.log('INFO', f'📋 Intent detected: {intent}')
    ui_logger.log('INFO', '🗂️ Planning objectives...')

    planner = AIPlanner(provider)

    # Groq → browser-use AI agent  |  Gemini → step-by-step Playwright
    if provider == 'groq':
        plan = planner.plan_for_browser_use(prompt, url)
    else:
        plan = planner.plan(prompt, url)

    if plan.get('error'):
        ui_logger.log('ERROR', f'❌ Planning failed: {plan["error"]}')
        socketio.emit('task_error', {'error': plan['error']})
        return

    if plan.get('saved_to'):
        ui_logger.log('INFO', f'📁 Plan saved: {plan["saved_to"]}')

    # Log what was planned
    if plan.get('execution_type') == 'browser_use':
        ui_logger.log('SUCCESS', f'✅ Agent task: {plan.get("task_description", "N/A")}')
    else:
        ui_logger.log('SUCCESS', f'✅ Plan ready: {len(plan.get("steps", []))} steps')

    # Push plan to frontend before execution begins
    socketio.emit('plan_ready', {'type': 'single', 'plan': plan, 'intent': intent})

    # Broadcast current page target so the UI can display it
    page_info = {'url': url, 'title': f'Target: {url}', 'status': 'loading'}
    socketio.emit('page_info', page_info)
    _last_page_info = page_info

    # ── Execute ───────────────────────────────────────────────────────────
    if plan.get('execution_type') == 'browser_use':
        ui_logger.log('INFO', '🤖 Executing with browser-use AI agent...')
        await run_with_browser_use(url, plan.get('task_description', prompt), socketio, ui_logger)
        ui_logger.log('SUCCESS', '✅ Browser-use task completed!')
        socketio.emit('task_success', {
            'message': 'Browser-use task completed successfully!',
            'steps_completed': 'AI Agent',
        })
    else:
        steps = plan.get('steps', [])
        ui_logger.log('INFO', f'🔄 Executing {len(steps)} steps with Playwright...')
        await run_async(url, steps, socketio, ui_logger)

        # Check per-step outcomes and report accurately
        failed = [s for s in steps if s.get('status') == 'failed']
        if not failed:
            ui_logger.log('SUCCESS', f'✅ All {len(steps)} steps completed!')
            socketio.emit('task_success', {
                'message': 'Task completed successfully!',
                'steps_completed': len(steps),
            })
        else:
            ui_logger.log('WARNING', f'⚠️ {len(failed)} of {len(steps)} steps failed')
            socketio.emit('task_warning', {
                'message': f'Task partially completed — {len(failed)} step(s) failed',
                'steps_completed': len(steps) - len(failed),
                'steps_failed': len(failed),
            })

    # Update page status to done
    _last_page_info = {**page_info, 'status': 'done'}
    socketio.emit('page_info', _last_page_info)


# ── Socket: enhance_plan ──────────────────────────────────────────────────────

@socketio.on('enhance_plan')
def on_enhance_plan(data):
    """
    Enhance an uploaded plan file via AI.
    Runs in a background task to avoid blocking the SocketIO thread.
    """
    raw      = (data or {}).get('raw',      '').strip()
    filename = (data or {}).get('filename', 'uploaded_plan.txt')
    provider = (data or {}).get('provider', 'groq')
    url      = (data or {}).get('url',      '').strip()

    if not raw:
        emit('error', {'message': 'No plan content received'})
        return

    socketio.start_background_task(_enhance_bg, raw, filename, provider, url)


def _enhance_bg(raw: str, filename: str, provider: str, url: str) -> None:
    try:
        ui_logger.log('INFO', f'📂 Enhancing plan: {filename}')
        planner = AIPlanner(provider)
        prompt = (
            "Please read and improve this execution plan. Convert it into specific, "
            "actionable browser automation steps. Fix structure, rephrase steps, and "
            f"return detailed JSON with a steps list.\n\nFile: {filename}\n\nContent:\n\n{raw}"
        )
        plan = planner.plan(prompt, url)

        if plan.get('error'):
            ui_logger.log('ERROR', f'❌ Enhancement failed: {plan["error"]}')
            socketio.emit('error', {'message': f'Enhancement failed: {plan["error"]}'})
            return

        if plan.get('saved_to'):
            ui_logger.log('INFO', f'📁 Enhanced plan saved: {plan["saved_to"]}')

        socketio.emit('plan_ready', {'type': 'single', 'plan': plan, 'intent': 'uploaded'})
        ui_logger.log('SUCCESS', f'✅ Plan enhanced: {filename}')

    except Exception as exc:
        ui_logger.log('ERROR', f'💥 Enhancement error: {exc}')
        socketio.emit('error', {'message': f'Failed to enhance plan: {exc}'})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    settings.print_status()

    if not settings.has_groq_key() and not settings.has_gemini_key():
        print("⚠️  No API keys configured.")
        print("    Run: python setup_api_keys.py")

    print()
    print("🚀 Viser AI Web UI v2")
    print("   → http://localhost:5000")
    print()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)

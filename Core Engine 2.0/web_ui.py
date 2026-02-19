#!/usr/bin/env python3
"""
Simple Web UI for Core Engine 2.0
Real-time chat interface with URL input and live logging
"""

import asyncio
import sys
import os
import json
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import logging

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from viser_core.ai_planner import AIPlanner, compare
from viser_core.intent_router import infer_intent
from viser_core.executor import run, run_with_browser_use_sync
from settings import settings

# Setup Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'viser-ai-core-engine-secret'
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    ping_timeout=60,
    ping_interval=25,
)

# Global variables
is_running = False
current_plan = None
last_page_info = None

class WebUILogger:
    """Custom logger that sends logs to web UI"""
    
    def __init__(self, socketio):
        self.socketio = socketio
    
    def log(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_data = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.socketio.emit('log_message', log_data)
        print(f"[{timestamp}] {level}: {message}")

# Initialize logger
ui_logger = WebUILogger(socketio)

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    ui_logger.log('INFO', 'Client connected to Core Engine 2.0')
    emit('status', {'connected': True})
    # Re-send last known state on reconnect
    global last_page_info
    if last_page_info:
        emit('page_info', last_page_info)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    ui_logger.log('INFO', 'Client disconnected')

@socketio.on('test_connection')
def handle_test_connection():
    """Simple ping/pong to verify connectivity"""
    ui_logger.log('INFO', 'Received test_connection from client')
    emit('log_message', {
        'timestamp': datetime.now().strftime("%H:%M:%S"),
        'level': 'INFO',
        'message': '🔗 Connection OK'
    })

@socketio.on('plan_task')
def handle_plan_task(data):
    """Handle task planning request (dry run)"""
    global current_plan
    
    prompt = data.get('prompt', '').strip()
    provider = data.get('provider', 'groq')
    
    if not prompt:
        emit('error', {'message': 'Please provide a task prompt'})
        return
    
    try:
        ui_logger.log('INFO', f'🎯 Planning task: {prompt}')
        ui_logger.log('INFO', f'🤖 Using provider: {provider}')
        
        # Detect intent
        intent = infer_intent(prompt)
        ui_logger.log('INFO', f'📋 Detected intent: {intent}')
        
        if provider == 'compare':
            # Compare both providers
            ui_logger.log('INFO', '🔄 Comparing providers...')
            results = compare(prompt)
            
            for prov, result in results.items():
                if result.get('error'):
                    ui_logger.log('ERROR', f'❌ {prov.upper()}: {result["error"]}')
                else:
                    steps_count = len(result.get('steps', []))
                    ui_logger.log('INFO', f'✅ {prov.upper()}: {steps_count} steps planned')
            
            current_plan = results
            emit('plan_ready', {
                'type': 'compare',
                'results': results,
                'intent': intent
            })
        else:
            # Single provider
            planner = AIPlanner(provider)
            plan = planner.plan(prompt)
            
            if plan.get('error'):
                ui_logger.log('ERROR', f'❌ Planning failed: {plan["error"]}')
                emit('error', {'message': f'Planning failed: {plan["error"]}'})
                return
            
            steps_count = len(plan.get('steps', []))
            ui_logger.log('SUCCESS', f'✅ Plan created: {steps_count} steps')
            
            current_plan = plan
            emit('plan_ready', {
                'type': 'single',
                'plan': plan,
                'intent': intent
            })
            
    except Exception as e:
        ui_logger.log('ERROR', f'💥 Planning failed: {str(e)}')
        emit('error', {'message': f'Planning failed: {str(e)}'})

@socketio.on('execute_task')
def handle_execute_task(data):
    """Handle task execution request"""
    global is_running, current_plan
    
    if is_running:
        emit('error', {'message': 'Task already running'})
        return
    
    url = data.get('url', '').strip()
    prompt = data.get('prompt', '').strip()
    provider = data.get('provider', 'groq')
    
    if not url or not prompt:
        emit('error', {'message': 'Please provide both URL and prompt'})
        return
    
    # Start task in background
    socketio.start_background_task(run_ai_task, url, prompt, provider)

def run_ai_task(url, prompt, provider):
    """Run AI task in background"""
    global is_running, current_plan, last_page_info
    
    try:
        is_running = True
        socketio.emit('task_started', {'url': url, 'prompt': prompt, 'provider': provider})
        
        # Run the async task
        asyncio.run(execute_ai_task_async(url, prompt, provider))
        
    except Exception as e:
        ui_logger.log('ERROR', f'Task failed: {str(e)}')
        socketio.emit('task_error', {'error': str(e)})
    finally:
        is_running = False
        socketio.emit('task_completed')

async def execute_ai_task_async(url, prompt, provider):
    """Execute the AI DOM task with async browser automation"""
    global current_plan, last_page_info
    
    try:
        ui_logger.log('INFO', f'🚀 Starting Core Engine 2.0...')
        ui_logger.log('INFO', f'📍 Target URL: {url}')
        ui_logger.log('INFO', f'🎯 Task: {prompt}')
        ui_logger.log('INFO', f'🤖 Provider: {provider}')
        
        # Detect intent
        intent = infer_intent(prompt)
        ui_logger.log('INFO', f'📋 Detected intent: {intent}')
        
        # Plan the task
        ui_logger.log('INFO', '🗂️ Planning objectives...')
        planner = AIPlanner(provider)
        
        # Use browser-use planning by default (Groq + browser-use)
        if provider == 'groq':
            plan = planner.plan_for_browser_use(prompt)
        else:
            plan = planner.plan(prompt)
        
        if plan.get('error'):
            ui_logger.log('ERROR', f'❌ Planning failed: {plan["error"]}')
            return
        
        current_plan = plan
        
        if plan.get('execution_type') == 'browser_use':
            ui_logger.log('SUCCESS', f'✅ Browser-use task planned: {plan.get("task_description", "N/A")}')
        else:
            steps_count = len(plan.get('steps', []))
            ui_logger.log('SUCCESS', f'✅ Plan created: {steps_count} steps')
        
        # Send plan to UI
        socketio.emit('plan_ready', {
            'type': 'single',
            'plan': plan,
            'intent': intent
        })
        
        # Page info will be updated by the browser automation
        page_info = {
            'url': url,
            'title': f'Target Page - {url}',
            'status': 'loading'
        }
        socketio.emit('page_info', page_info)
        last_page_info = page_info
        
        # Execute with browser-use or traditional steps
        if plan.get('execution_type') == 'browser_use':
            ui_logger.log('INFO', f'🔄 Executing with browser-use agent...')
            task_description = plan.get('task_description', prompt)
            
            # Use browser-use for execution
            from viser_core.executor import run_with_browser_use
            await run_with_browser_use(url, task_description, socketio, ui_logger)
        else:
            # Execute steps with traditional browser automation
            ui_logger.log('INFO', f'🔄 Executing {steps_count} steps with real browser...')
            
            # Use traditional browser automation
            from viser_core.executor import run_async
            await run_async(url, plan.get('steps', []), socketio, ui_logger)
        
        # Check if all steps completed successfully
        if plan.get('execution_type') == 'browser_use':
            # For browser-use, assume success if no error was thrown
            ui_logger.log('SUCCESS', '✅ Browser-use task completed successfully!')
            socketio.emit('task_success', {
                'message': 'Browser-use task completed successfully!',
                'steps_completed': 'AI Agent'
            })
        else:
            # For traditional step execution
            all_ok = True
            for step in plan.get('steps', []):
                if step.get('status') == 'failed':
                    all_ok = False
                    break
            
            # Finalize
            if all_ok:
                ui_logger.log('SUCCESS', '✅ All steps completed successfully!')
                socketio.emit('task_success', {
                    'message': 'Task completed successfully!',
                    'steps_completed': len(plan.get('steps', []))
                })
            else:
                ui_logger.log('WARNING', '⚠️ Some steps failed')
                socketio.emit('task_warning', {
                    'message': 'Task partially completed - some steps failed'
                })
        
    except Exception as e:
        ui_logger.log('ERROR', f'💥 Task execution failed: {str(e)}')
        raise

if __name__ == '__main__':
    # Print configuration status
    settings.print_status()
    
    if not settings.has_groq_key() and not settings.has_gemini_key():
        print("⚠️ No API keys configured.")
        print("   Run 'python setup_api_keys.py' to configure API keys.")
        print("   The UI will still work for planning with mock data.")
    
    print(f"🌐 Starting web server...")
    print(f"📱 Open browser to: http://localhost:5000")
    print("=" * 50)
    
    # Run Flask app
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)

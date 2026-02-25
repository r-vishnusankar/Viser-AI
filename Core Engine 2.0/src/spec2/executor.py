import asyncio
import os
from typing import List, Dict, Any
from loguru import logger

# Import settings
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from settings import settings

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_OK = True
except Exception:
    PLAYWRIGHT_OK = False

async def run_with_browser_use(url: str, task_description: str, socketio=None, ui_logger=None) -> None:
    """Run browser automation using browser-use with OpenAI API"""
    # Import Agent lazily to avoid stale availability checks
    try:
        from browser_use import Agent  # type: ignore
        from browser_use.llm.openai.chat import ChatOpenAI  # type: ignore
    except Exception:
        error_msg = "⚠️ browser-use not installed. pip install browser-use"
        if ui_logger:
            ui_logger.log('ERROR', error_msg)
        else:
            print(error_msg)
        return
    
    # Check if OpenAI API key is available
    openai_key = settings.openai_api_key
    if not openai_key:
        error_msg = "⚠️ OpenAI API key not configured. Run 'python setup_api_keys.py' to configure."
        if ui_logger:
            ui_logger.log('ERROR', error_msg)
        else:
            print(error_msg)
        return
    
    try:
        if ui_logger:
            ui_logger.log('INFO', f'🌐 Opening browser to: {url}')
            ui_logger.log('INFO', f'🎯 Task: {task_description}')
        else:
            print(f"🌐 Opening: {url}")
            print(f"🎯 Task: {task_description}")
        
        # Set OpenAI API key for browser-use
        os.environ['OPENAI_API_KEY'] = openai_key
        
        # Initialize browser-use with proper LLM instance and a dedicated profile
        from browser_use.browser.profile import BrowserProfile  # type: ignore
        llm = ChatOpenAI(model="gpt-4o-mini", api_key=openai_key)
        profile_dir = str(Path.cwd() / "browser_use_profile")
        os.makedirs(profile_dir, exist_ok=True)
        browser_profile = BrowserProfile(user_data_dir=profile_dir, headless=False)
        # Include URL in the task so the agent navigates first
        full_task = f"Open {url} and then {task_description}"
        agent = Agent(task=full_task, llm=llm, browser_profile=browser_profile)
        
        if ui_logger:
            ui_logger.log('SUCCESS', '✅ Browser-use initialized')
        else:
            print("✅ Browser-use initialized")
        
        # Run agent
        result = await agent.run()
        
        if ui_logger:
            ui_logger.log('SUCCESS', '✅ Browser task completed')
            ui_logger.log('INFO', f'Result: {result}')
        else:
            print("✅ Browser task completed")
            print(f"Result: {result}")
            
    except Exception as e:
        error_msg = f'Browser-use execution failed: {str(e)}'
        if ui_logger:
            ui_logger.log('ERROR', f'💥 {error_msg}')
        else:
            print(f"❌ {error_msg}")
        raise
    finally:
        try:
            if 'agent' in locals():
                await agent.close()
                if ui_logger:
                    ui_logger.log('INFO', '🧹 Browser agent closed')
                else:
                    print("🧹 Browser agent closed")
        except Exception as e:
            if ui_logger:
                ui_logger.log('WARNING', f'⚠️ Error closing browser agent: {e}')
            else:
                print(f"⚠️ Error closing browser agent: {e}")

async def run_async(url: str, steps: List[Dict[str, Any]], socketio=None, ui_logger=None) -> None:
    """Run browser automation with real browser actions using Playwright"""
    if not PLAYWRIGHT_OK:
        error_msg = "⚠️ Playwright not installed. pip install playwright && playwright install"
        if ui_logger:
            ui_logger.log('ERROR', error_msg)
        else:
            print(error_msg)
        return
    
    browser = None
    page = None
    try:
        if ui_logger:
            ui_logger.log('INFO', f'🌐 Opening browser to: {url}')
        else:
            print(f"🌐 Opening: {url}")
        
        # Initialize Playwright browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=False)  # Set to True for headless mode
        page = await browser.new_page()
        
        if ui_logger:
            ui_logger.log('SUCCESS', '✅ Browser started')
        else:
            print("✅ Browser started")
        
        # Navigate to URL
        await page.goto(url)
        
        if ui_logger:
            ui_logger.log('SUCCESS', '✅ Navigation successful')
        else:
            print("✅ Navigation successful")
        
        # Execute each step
        for i, step in enumerate(steps, 1):
            step_id = step.get('id', i)
            action = step.get('action', 'UNKNOWN')
            target = step.get('target', 'unknown')
            value = step.get('value', '')
            instruction = step.get('instruction', '')
            
            if ui_logger:
                ui_logger.log('INFO', f'🧭 Step {step_id}: {action} -> {target}')
                if value:
                    ui_logger.log('INFO', f'   Value: {value}')
            else:
                print(f"→ Step {step_id}: {action} target={target} value={value}")
            
            try:
                # Map actions to Playwright methods
                if action == 'SEARCH':
                    # Search for text in search field
                    search_selector = 'input[type="search"], input[name*="search"], input[placeholder*="search"]'
                    await page.fill(search_selector, value)
                    await page.press(search_selector, 'Enter')
                elif action == 'CLICK':
                    # Click on element
                    await page.click(target)
                elif action == 'FILL':
                    # Fill input field
                    await page.fill(target, value)
                elif action == 'SELECT':
                    # Select option
                    await page.select_option(target, value)
                elif action == 'NAVIGATE':
                    # Navigate to URL
                    if target == 'URL':
                        await page.goto(value)
                    else:
                        await page.click(target)
                elif action == 'WAIT':
                    wait_ms = int(value) * 1000 if value and str(value).isdigit() else 2000
                    await page.wait_for_timeout(wait_ms)
                elif action == 'VERIFY':
                    # Verify element/text exists on page
                    if target and target != 'page':
                        try:
                            await page.wait_for_selector(target, timeout=5000)
                            if ui_logger:
                                ui_logger.log('SUCCESS', f'✅ Verified: {target} found on page')
                        except Exception:
                            if value:
                                found = await page.locator(f'text={value}').count()
                                if not found:
                                    if ui_logger:
                                        ui_logger.log('WARNING', f'⚠️ Verify failed: "{value}" not found')
                                    else:
                                        print(f"⚠️ Verify failed: '{value}' not found")
                    elif value:
                        found = await page.locator(f'text={value}').count()
                        if ui_logger:
                            ui_logger.log('SUCCESS' if found else 'WARNING',
                                f'{"✅ Verified" if found else "⚠️ Not found"}: "{value}"')
                else:
                    # Generic instruction - use targeted text-based selectors
                    if 'login' in instruction.lower() or 'sign in' in instruction.lower():
                        await page.click('button:has-text("Login"), button:has-text("Sign in"), a:has-text("Login"), a:has-text("Sign in")')
                    elif 'search' in instruction.lower():
                        search_selector = 'input[type="search"], input[name*="search"], input[placeholder*="earch"]'
                        await page.fill(search_selector, value or target)
                        await page.press(search_selector, 'Enter')
                    elif 'submit' in instruction.lower() or 'confirm' in instruction.lower():
                        await page.click('button[type="submit"], input[type="submit"]')
                    else:
                        if ui_logger:
                            ui_logger.log('WARNING', f'⚠️ Step {step_id}: Unhandled action "{action}" - skipping')
                        else:
                            print(f"⚠️ Step {step_id}: Unhandled action '{action}' - skipping")
                
                if ui_logger:
                    ui_logger.log('SUCCESS', f'✅ Step {step_id} completed')
                else:
                    print(f"✅ Step {step_id} completed")
                
                # Update step status in UI
                if socketio:
                    socketio.emit('step_update', {
                        'step_id': step_id,
                        'status': 'completed',
                        'action': action,
                        'target': target
                    })
                
                # Small delay between steps
                await asyncio.sleep(1)
                
            except Exception as step_err:
                error_msg = f'Step {step_id} error: {step_err}'
                if ui_logger:
                    ui_logger.log('ERROR', f'💥 {error_msg}')
                else:
                    print(f"❌ {error_msg}")
                
                # Update step status in UI
                if socketio:
                    socketio.emit('step_update', {
                        'step_id': step_id,
                        'status': 'failed',
                        'action': action,
                        'target': target,
                        'error': str(step_err)
                    })
                
                # Continue with next step
                continue
        
        # Take screenshot of final result
        try:
            screenshot_path = "browser_result.png"
            await page.screenshot(path=screenshot_path)
            if ui_logger:
                ui_logger.log('SUCCESS', f'📸 Screenshot saved: {screenshot_path}')
            else:
                print(f"📸 Screenshot saved: {screenshot_path}")
        except Exception as e:
            if ui_logger:
                ui_logger.log('WARNING', f'⚠️ Could not take screenshot: {e}')
            else:
                print(f"⚠️ Could not take screenshot: {e}")
        
        if ui_logger:
            ui_logger.log('SUCCESS', '✅ All browser actions completed!')
        else:
            print("✅ Browser execution complete")
            
    except Exception as e:
        error_msg = f'Browser execution failed: {str(e)}'
        if ui_logger:
            ui_logger.log('ERROR', f'💥 {error_msg}')
        else:
            print(f"❌ {error_msg}")
        raise
    finally:
        if browser:
            if ui_logger:
                ui_logger.log('INFO', '🧹 Closing browser...')
            else:
                print("🧹 Closing browser...")
            await browser.close()
        try:
            await playwright.stop()
        except Exception:
            pass

def run(url: str, steps: List[Dict[str, Any]], socketio=None, ui_logger=None) -> None:
    """Synchronous wrapper for browser automation"""
    if not PLAYWRIGHT_OK:
        error_msg = "⚠️ Playwright not installed. pip install playwright && playwright install"
        if ui_logger:
            ui_logger.log('ERROR', error_msg)
        else:
            print(error_msg)
        return
    
    # Run async function
    asyncio.run(run_async(url, steps, socketio, ui_logger))

def run_with_browser_use_sync(url: str, task_description: str, socketio=None, ui_logger=None) -> None:
    """Synchronous wrapper for browser-use automation"""
    # Run async function
    asyncio.run(run_with_browser_use(url, task_description, socketio, ui_logger))
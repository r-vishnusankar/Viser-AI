import os, json
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger
from pathlib import Path

# Groq
from groq import Groq
# Gemini
import google.generativeai as genai

# Import settings
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from settings import settings

# Use env-overridable model names
GROQ_MODEL   = os.getenv("GROQ_MODEL",   "llama-3.3-70b-versatile")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = '''You are an AI objective planner. Break natural language into specific, actionable browser automation steps.

Step types: 
- NAVIGATE: Go to a specific URL or page section
- SEARCH: Use search functionality 
- CLICK: Click on buttons, links, or elements
- FILL: Fill input fields with text
- SELECT: Select options from dropdowns
- WAIT: Wait for elements to load
- VERIFY: Check if something exists or is correct

Each step must be specific and actionable. Include exact selectors, text content, or element descriptions.

IMPORTANT: Use the provided target URL as the base for all navigation steps. Do not use example.com or generic URLs.

Return ONLY a JSON array of steps:
[
  { "step": 1, "action": "NAVIGATE", "target": "search page", "value": "", "description": "Navigate to the website's search or product listing page" },
  { "step": 2, "action": "SEARCH", "target": "search input field", "value": "blue t-shirt", "description": "Enter 'blue t-shirt' in the search field" },
  { "step": 3, "action": "CLICK", "target": "search button", "value": "", "description": "Click the search button or press Enter to search" },
  { "step": 4, "action": "CLICK", "target": "first blue t-shirt product", "value": "", "description": "Click on the first blue t-shirt product from search results" },
  { "step": 5, "action": "CLICK", "target": "Add to Cart button", "value": "", "description": "Click the 'Add to Cart' button on the product page" },
  { "step": 6, "action": "VERIFY", "target": "cart confirmation", "value": "", "description": "Verify that the product was added to cart (check for success message or cart icon)" }
]

Make steps specific and detailed. Break complex actions into smaller, actionable steps.'''

BROWSER_USE_PROMPT = '''You are an AI task planner for browser automation. Convert natural language requests into clear, actionable task descriptions.

IMPORTANT: Use the provided target URL as the base for all navigation and actions. Do not use example.com or generic URLs.

Return a JSON object with a "task_description" field containing a clear, step-by-step description of what needs to be done.

Example:
{
  "task_description": "Navigate to the website, search for 'blue t-shirt', click on the first result, and add it to the cart"
}'''

def _now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

class AIPlanner:
    def __init__(self, provider: str = "groq"):
        self.provider = provider.lower()
        if self.provider == "groq":
            key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
            if not key:
                raise RuntimeError("GROQ_API_KEY not set. Configure it in Settings or .env file.")
            self.client = Groq(api_key=key)
            self.model = GROQ_MODEL
        elif self.provider == "gemini":
            key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
            if not key:
                raise RuntimeError("GEMINI_API_KEY not set. Configure it in Settings or .env file.")
            genai.configure(api_key=key)
            self.client = genai.GenerativeModel(GEMINI_MODEL)
            self.model = GEMINI_MODEL
        elif self.provider == "openai":
            key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not key:
                raise RuntimeError("OPENAI_API_KEY not set. Configure it in Settings or .env file.")
            from openai import OpenAI
            self.client = OpenAI(api_key=key)
            self.model = OPENAI_MODEL
        else:
            raise ValueError(f"Unsupported provider '{provider}'. Choose from: groq, gemini, openai")

    def _ask(self, user_request: str, target_url: str = "") -> str:
        context_prompt = SYSTEM_PROMPT
        if target_url:
            context_prompt += f"\n\nTarget URL: {target_url}\nUse this URL as the base for navigation steps."

        if self.provider in ("groq", "openai"):
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": context_prompt},
                          {"role": "user",   "content": user_request}],
                temperature=0.1, max_tokens=1500
            )
            return resp.choices[0].message.content.strip()
        else:  # gemini
            prompt = f"{context_prompt}\nUser Request: {user_request}"
            resp = self.client.generate_content(prompt)
            return resp.text.strip()

    def _save_plan(self, plan_data: Dict[str, Any]) -> str:
        """Save plan to JSON file and return the file path"""
        try:
            # Create plans directory if it doesn't exist
            plans_dir = Path(__file__).parent.parent.parent / "plans"
            plans_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp and request
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Clean the request for filename (remove special chars, limit length)
            clean_request = "".join(c for c in plan_data.get("user_request", "plan")[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_request = clean_request.replace(' ', '_')
            filename = f"plan_{timestamp}_{clean_request}.json"
            
            filepath = plans_dir / filename
            
            # Save the plan
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📁 Plan saved: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Failed to save plan: {e}")
            return ""

    def plan_for_browser_use(self, user_request: str, target_url: str = "") -> Dict[str, Any]:
        """Plan task for browser-use execution"""
        rid = _now_id()
        try:
            # Create context-aware prompt with target URL
            context_prompt = BROWSER_USE_PROMPT
            if target_url:
                context_prompt += f"\n\nTarget URL: {target_url}\nUse this URL as the base for all navigation and actions."
            
            if self.provider in ("groq", "openai"):
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": context_prompt},
                              {"role": "user",   "content": user_request}],
                    temperature=0.1, max_tokens=1000
                )
                raw = resp.choices[0].message.content.strip()
            else:  # gemini
                prompt = f"{context_prompt}\nUser Request: {user_request}"
                resp = self.client.generate_content(prompt)
                raw = resp.text.strip()
            
            try:
                task_data = json.loads(raw)
                task_description = task_data.get("task_description", user_request)
            except json.JSONDecodeError:
                import re
                m = re.search(r'"task_description"\s*:\s*"([^"]+)"', raw)
                task_description = m.group(1) if m else user_request
            
            result = {
                "request_id": rid,
                "timestamp": datetime.now().isoformat(),
                "ai_model": f"{self.provider}/{self.model}",
                "user_request": user_request,
                "target_url": target_url,
                "task_description": task_description,
                "execution_type": "browser_use",
                "status": "planned"
            }
            
            # Save the plan
            saved_path = self._save_plan(result)
            if saved_path:
                result["saved_to"] = saved_path
            
            return result
        except Exception as e:
            logger.exception("AI planning failed")
            return {
                "request_id": rid, 
                "timestamp": datetime.now().isoformat(),
                "ai_model": f"{self.provider}/{self.model}",
                "user_request": user_request,
                "target_url": target_url,
                "error": str(e),
                "task_description": user_request,
                "execution_type": "browser_use",
                "status":"error"
            }

    def plan(self, user_request: str, target_url: str = "") -> Dict[str, Any]:
        rid = _now_id()
        try:
            raw = self._ask(user_request, target_url)
            try:
                steps = json.loads(raw)
            except json.JSONDecodeError:
                import re
                m = re.search(r"\[.*\]", raw, re.DOTALL)
                steps = json.loads(m.group(0)) if m else [{
                    "step": 1, "action": "INSTRUCTION", "target": "page",
                    "value": "", "description": user_request
                }]
            objectives = [{"type": s["action"], "target": s["target"], "description": s["description"]} for s in steps]
            result = {
                "request_id": rid,
                "timestamp": datetime.now().isoformat(),
                "ai_model": f"{self.provider}/{self.model}",
                "user_request": user_request,
                "target_url": target_url,
                "objectives": objectives,
                "steps": [{
                    "id": s["step"], "action": s["action"], "target": s["target"],
                    "value": s.get("value",""), "instruction": s["description"], "status": "planned"
                } for s in steps],
                "status": "planned"
            }
            
            # Save the plan
            saved_path = self._save_plan(result)
            if saved_path:
                result["saved_to"] = saved_path
            
            return result
        except Exception as e:
            logger.exception("AI planning failed")
            return {
                "request_id": rid, 
                "timestamp": datetime.now().isoformat(),
                "ai_model": f"{self.provider}/{self.model}",
                "user_request": user_request,
                "target_url": target_url,
                "error": str(e),
                "objectives": [],
                "steps": [],
                "status":"error"
            }

def compare(user_request: str, target_url: str = "") -> Dict[str, Dict[str, Any]]:
    """Compare planning results from all available providers."""
    results = {}
    # Only include providers that have keys configured
    candidates = []
    if settings.groq_api_key   or os.getenv("GROQ_API_KEY"):   candidates.append("groq")
    if settings.gemini_api_key or os.getenv("GEMINI_API_KEY"): candidates.append("gemini")
    if settings.openai_api_key or os.getenv("OPENAI_API_KEY"): candidates.append("openai")
    if not candidates:
        candidates = ["groq"]  # fallback, will error gracefully

    for provider in candidates:
        try:
            planner = AIPlanner(provider)
            plan = planner.plan(user_request, target_url)
            results[provider] = plan
        except Exception as e:
            results[provider] = {
                "request_id": _now_id(),
                "timestamp": datetime.now().isoformat(),
                "ai_model": f"{provider}/unknown",
                "user_request": user_request,
                "target_url": target_url,
                "error": str(e),
                "objectives": [],
                "steps": [],
                "status": "error"
            }

    return results
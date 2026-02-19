import os, json
from datetime import datetime
from typing import Dict, Any, List
from loguru import logger

# Groq
from groq import Groq
# Gemini
import google.generativeai as genai

# Import settings
import sys
from pathlib import Path

# Get the Core Engine 2.0 root directory (parent.parent.parent from this file)
_core_engine_root = Path(__file__).parent.parent.parent
if str(_core_engine_root) not in sys.path:
    sys.path.insert(0, str(_core_engine_root))

from settings import settings

GROQ_MODEL = "llama-3.1-8b-instant"
GEMINI_MODEL = "gemini-pro"

SYSTEM_PROMPT = '''You are an AI objective planner. Break natural language into steps.
Step types: FILL, CLICK, SEARCH, SELECT, NAVIGATE, WAIT
Return ONLY a JSON array of steps:
[{ "step": 1, "action": "SEARCH", "target": "search field", "value": "blue tshirt", "description": "Search for blue tshirt" }]
'''

BROWSER_USE_PROMPT = '''You are an AI task planner for browser automation. 
Convert the user request into a clear, detailed task description that a browser automation agent can understand and execute.
Focus on the end goal and provide context about what the user wants to accomplish.
Return ONLY a JSON object with the task description:
{ "task_description": "Detailed task description for browser automation" }
'''

def _now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

class AIPlanner:
    def __init__(self, provider: str = "groq"):
        self.provider = provider.lower()
        if self.provider == "groq":
            key = settings.groq_api_key
            if not key: raise RuntimeError("GROQ_API_KEY not set. Run 'python setup_api_keys.py' to configure.")
            self.client = Groq(api_key=key)
            self.model = GROQ_MODEL
        elif self.provider == "gemini":
            key = settings.gemini_api_key
            if not key: raise RuntimeError("GEMINI_API_KEY not set. Run 'python setup_api_keys.py' to configure.")
            genai.configure(api_key=key)
            self.client = genai.GenerativeModel(GEMINI_MODEL)
            self.model = GEMINI_MODEL
        else:
            raise ValueError("provider must be 'groq' or 'gemini'")

    def _ask(self, user_request: str) -> str:
        if self.provider == "groq":
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role":"system","content":SYSTEM_PROMPT},
                          {"role":"user","content":user_request}],
                temperature=0.1, max_tokens=1000
            )
            return resp.choices[0].message.content.strip()
        else:
            prompt = f"{SYSTEM_PROMPT}\nUser Request: {user_request}"
            resp = self.client.generate_content(prompt)
            return resp.text.strip()

    def plan_for_browser_use(self, user_request: str) -> Dict[str, Any]:
        """Plan task for browser-use execution"""
        rid = _now_id()
        try:
            if self.provider == "groq":
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role":"system","content":BROWSER_USE_PROMPT},
                              {"role":"user","content":user_request}],
                    temperature=0.1, max_tokens=1000
                )
                raw = resp.choices[0].message.content.strip()
            else:
                prompt = f"{BROWSER_USE_PROMPT}\nUser Request: {user_request}"
                resp = self.client.generate_content(prompt)
                raw = resp.text.strip()
            
            try:
                task_data = json.loads(raw)
                task_description = task_data.get("task_description", user_request)
            except:
                # Fallback if JSON parsing fails
                task_description = user_request
            
            result = {
                "request_id": rid,
                "timestamp": datetime.now().isoformat(),
                "ai_model": f"{self.provider}/{self.model}",
                "user_request": user_request,
                "task_description": task_description,
                "execution_type": "browser_use",
                "status": "planned"
            }
            return result
        except Exception as e:
            logger.exception("AI planning failed")
            return {
                "request_id": rid, 
                "timestamp": datetime.now().isoformat(),
                "ai_model": f"{self.provider}/{self.model}",
                "user_request": user_request, 
                "error": str(e),
                "task_description": user_request,
                "execution_type": "browser_use",
                "status":"error"
            }

    def plan(self, user_request: str) -> Dict[str, Any]:
        rid = _now_id()
        try:
            raw = self._ask(user_request)
            try:
                steps = json.loads(raw)
            except:
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
                "objectives": objectives,
                "steps": [{
                    "id": s["step"], "action": s["action"], "target": s["target"],
                    "value": s.get("value",""), "instruction": s["description"], "status": "planned"
                } for s in steps],
                "status": "planned"
            }
            return result
        except Exception as e:
            logger.exception("AI planning failed")
            return {
                "request_id": rid, "timestamp": datetime.now().isoformat(),
                "ai_model": f"{self.provider}/{self.model}",
                "user_request": user_request, "error": str(e),
                "objectives":[{"type":"INSTRUCTION","target":"page","description":user_request}],
                "steps":[{"id":1,"action":"INSTRUCTION","target":"page","value":"","instruction":user_request,"status":"planned"}],
                "status":"error"
            }

def compare(user_request: str) -> Dict[str, Any]:
    out = {}
    for p in ("groq","gemini"):
        try:
            out[p] = AIPlanner(p).plan(user_request)
        except Exception as e:
            out[p] = {"error": str(e)}
    return out
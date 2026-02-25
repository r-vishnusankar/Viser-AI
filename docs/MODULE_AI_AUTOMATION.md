# AI Automation Module Documentation

## Overview

The **AI Automation Module** enables browser-based task automation driven by natural language. Users provide a URL and a task description; the system plans the task, optionally executes it using either browser-use (AI agent) or Playwright (step-based), and streams progress via WebSocket.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        viser-ai-modern.html (SPA)                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ setupAutomation(), setupSocketIO()                                 │  │
│  │  • execute_task, plan_task, enhance_plan, test_connection          │  │
│  │  • automationLogContainer, automationPlanSection                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ Socket.IO
┌─────────────────────────────────────────────────────────────────────────┐
│                         flask_server.py                                  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ handle_execute_task, handle_plan_task, handle_enhance_plan         │  │
│  │ run_core_engine_task() → spec2.ai_planner, spec2.executor          │  │
│  │ WebUILogger → ui_logger.log() → emit('log_message')                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Core Engine 2.0/src/spec2/                            │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ ai_planner.py   → AIPlanner, plan(), plan_for_browser_use()         │  │
│  │ intent_router.py → infer_intent()                                   │  │
│  │ executor.py     → run_with_browser_use(), run_async()               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌─────────────────────────────┐   ┌─────────────────────────────────────┐
│ browser-use (Agent)         │   │ Playwright (async_api)                │
│ • OpenAI gpt-4o-mini        │   │ • NAVIGATE, CLICK, FILL, SEARCH, etc. │
│ • BrowserProfile            │   │ • step_update via Socket.IO           │
└─────────────────────────────┘   └─────────────────────────────────────┘
```

---

## Backend Components

### Location
- **Flask + Socket.IO:** `flask_server.py` (lines ~284–523)
- **Core Engine:** `Core Engine 2.0/src/spec2/`
- **Config:** `Core Engine 2.0/settings.py`

### Socket.IO Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `connect` | Client→Server | Connection established |
| `disconnect` | Client→Server | Client disconnected |
| `execute_task` | Client→Server | Run full automation (plan + execute) |
| `plan_task` | Client→Server | Generate plan only (dry run) |
| `enhance_plan` | Client→Server | Improve uploaded plan with AI |
| `test_connection` | Client→Server | Connection test |
| `status` | Server→Client | Connection confirmation |
| `plan_ready` | Server→Client | Plan result (single or compare) |
| `task_started` | Server→Client | Task started |
| `step_update` | Server→Client | Step status (completed/failed) |
| `task_success` | Server→Client | Task completed successfully |
| `task_warning` | Server→Client | Task completed with warnings |
| `task_error` | Server→Client | Task failed |
| `task_completed` | Server→Client | Task finished (always) |
| `log_message` | Server→Client | Logs (timestamp, level, message) |
| `error` | Server→Client | Error message |
| `page_info` | Server→Client | Current page info |

---

## Core Engine Components

### 1. ai_planner.py

**AIPlanner** — Converts natural language into executable plans.

| Method | Purpose |
|--------|---------|
| `plan(user_request, target_url)` | Step-based plan (NAVIGATE, SEARCH, CLICK, FILL, SELECT, WAIT, VERIFY) |
| `plan_for_browser_use(user_request, target_url)` | Task description for browser-use agent |
| `_save_plan(plan_data)` | Save plan to `plans/plan_<timestamp>_<request>.json` |

**compare(user_request, target_url)** — Returns plans from all available providers (Groq, Gemini, OpenAI) for comparison.

**Provider support:** Groq, Gemini, OpenAI (via `settings.py` or env)

**Models:** `GROQ_MODEL`, `GEMINI_MODEL`, `OPENAI_MODEL` (env-overridable)

### 2. intent_router.py

**infer_intent(request)** — Returns `"search" | "auth" | "cart" | "navigate" | "generic"` based on keywords.

| Intent | Keywords |
|--------|----------|
| search | search, find, look for |
| auth | login, sign in, username, password |
| cart | cart, wishlist |
| navigate | go to, navigate, open |
| generic | (default) |

### 3. executor.py

| Function | Purpose |
|----------|---------|
| `run_with_browser_use(url, task_description, socketio, ui_logger)` | Uses browser-use Agent + OpenAI gpt-4o-mini |
| `run_async(url, steps, socketio, ui_logger)` | Playwright step execution |

**Supported actions (Playwright):** `NAVIGATE`, `SEARCH`, `CLICK`, `FILL`, `SELECT`, `WAIT`, `VERIFY` (and generic instruction fallbacks)

**Browser profile:** `browser_use_profile/` (persistent)

---

## Execution Flow

1. User enters **URL** and **prompt** in automation view.
2. Client emits `execute_task` or `plan_task` with `{ url, prompt, provider }`.
3. `handle_execute_task` / `handle_plan_task` in `flask_server.py`.
4. `run_core_engine_task`:
   - `infer_intent(prompt)`
   - `AIPlanner(provider).plan_for_browser_use(prompt, url)` (or `plan()` for Gemini step-based)
   - Emit `plan_ready`
   - If `execution_type == 'browser_use'` → `run_with_browser_use()`
   - Else → `run_async()` with Playwright steps
5. Emit `step_update` during execution.
6. Emit `task_success` / `task_error` / `task_completed` at end.

---

## Frontend Components

### setupAutomation()

| Button | ID | Action |
|--------|-----|--------|
| Execute | `startAutomationBtn` | Emit `execute_task` |
| Plan | `automationPlanBtn` | Emit `plan_task` |
| Enhance | `automationEnhanceBtn` | Upload plan file → `enhance_plan` |
| Test | `automationTestBtn` | Emit `test_connection` |

### Inputs

| Input | ID | Purpose |
|-------|-----|---------|
| URL | `automationUrl` | Target URL |
| Prompt | `automationPrompt` | Task description |
| Provider | `automationProvider` | groq, gemini, openai, compare |
| Plan upload | `automationPlanUpload` | File for enhance |

### UI Elements

| Element | ID | Purpose |
|---------|-----|---------|
| Log container | `automationLogContainer` | Log entries |
| Plan section | `automationPlanSection` | Plan display |
| Plan content | `automationPlanContent` | Steps or task description |
| Loading overlay | `automationLoadingOverlay` | Loading state |

### Methods

- `setupSocketIO()` — Connect to Socket.IO, listen for `plan_ready`, `step_update`, `task_success`, `task_error`, `task_completed`, `log_message`, `error`, `status`
- `displayAutomationPlan(data)` — Render single plan or compare view
- `renderAutomationSteps(steps)` — Render step list
- `updateAutomationStepStatus(stepId, status)` — Update step badge
- `addAutomationLog(message, level)` — Append log entry

---

## Configuration

- **API keys:** `~/.viser_ai/config.json` or `~/.spec2/config.json`
- **Settings:** `Core Engine 2.0/settings.py` — `groq_api_key`, `gemini_api_key`, `openai_api_key`
- **Browser-use:** Requires `OPENAI_API_KEY` (gpt-4o-mini)
- **CORE_ENGINE_AVAILABLE:** Set from successful import of `spec2` modules

---

## Dependencies

- `browser-use` — AI agent for browser automation
- `playwright` — Step-based execution
- `openai` — For browser-use Agent
- `groq`, `google.generativeai` — For planning
- `loguru` — Logging in spec2

---

## Related Files

| File | Role |
|------|------|
| `flask_server.py` | Socket.IO handlers, `run_core_engine_task` |
| `viser-ai-modern.html` | `setupAutomation()`, `setupSocketIO()` |
| `Core Engine 2.0/src/spec2/ai_planner.py` | AIPlanner, compare |
| `Core Engine 2.0/src/spec2/executor.py` | run_with_browser_use, run_async |
| `Core Engine 2.0/src/spec2/intent_router.py` | infer_intent |
| `Core Engine 2.0/settings.py` | API keys |
| `Core Engine 2.0/plans/` | Saved plans (JSON) |

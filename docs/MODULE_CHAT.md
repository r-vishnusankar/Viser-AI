# 💬 Chat Module Documentation

<p align="center">
  <strong>🟣 AI-Powered Conversational Interface</strong>
</p>

---

## 📋 Overview

> **💜 The Chat Module** provides an AI-powered conversational interface within Viser-AI. It supports multiple AI providers (Groq, OpenAI, Gemini), streaming responses, session persistence, file uploads for context, and smart conversation summarization.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🌐 viser-ai-modern.html (SPA)                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 💬 ViseAIChat Class                                               │  │
│  │  • chatMessages, messageInput, sendBtn, uploadBtn                    │  │
│  │  • sessionId, uploadedFiles, slash commands                        │  │
│  │  • callAPIStreaming() → /api/chat/stream                           │  │
│  │  • loadConversationContext() → /api/context                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  🐍 flask_server.py                                                      │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 📦 ContextManager                                                 │  │
│  │  • get_session(), add_message(), add_file_context()                │  │
│  │  • get_conversation_context(), cleanup_old_sessions()              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 🗄️ SQLite: data/chat_history.db                                   │  │
│  │  • chat_messages(session_id, role, content, ts)                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Backend Components

### 📍 Location
- **📄 File:** `flask_server.py`
- **📏 Lines:** ~1655–2440 (chat routes), ~150–282 (ContextManager)

### 📦 ContextManager

> Manages per-session conversation state and file context.

| Method | Purpose |
|--------|---------|
| `get_session(session_id)` | Get or create session; restore from DB if not in memory |
| `add_message(session_id, role, content)` | Append message to history and persist to SQLite |
| `add_file_context(session_id, file_info)` | Add uploaded file metadata to session |
| `get_conversation_context(session_id, include_files)` | Build messages array for API (system + history + file context) |
| `mark_file_analyzed(session_id, filename)` | Mark file as analyzed |
| `cleanup_old_sessions()` | Remove sessions inactive for 24+ hours |

### 🧠 Smart Summarization

> **💡 When conversation history exceeds 30 messages** (`_SUMMARIZE_THRESHOLD`):
> - Older messages (except last 10) are summarized via AI
> - Summary is injected as a system message
> - Keeps context manageable for long conversations

### 🗄️ Database

- **📂 Path:** `data/chat_history.db`
- **📊 Table:** `chat_messages(session_id, role, content, ts)`
- **🔧 Functions:** `db_save_message()`, `db_load_session()`, `db_all_sessions()`

---

## 🔌 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/chat` | `POST` | Non-streaming chat (OpenAI, Groq, Gemini) |
| `/api/chat/stream` | `POST` | **⚡ Streaming chat** (SSE) — primary for UI |
| `/api/chat/history` | `GET` | List all persisted sessions |
| `/api/chat/history/<session_id>` | `GET` | Messages for a specific session |
| `/api/context` | `GET` | Get conversation context + uploaded files |
| `/api/settings/provider` | `GET/POST` | Get or set AI provider |
| `/api/clear-context` | `POST` | Clear session context |
| `/api/summarize-files` | `POST` | Summarize uploaded files and inject into context |
| `/api/key-status` | `GET` | Masked API key status for UI |

---

## 🤖 AI Provider Support

| Provider | Model (default) | Notes |
|----------|-----------------|-------|
| **🟢 Groq** | `llama-3.3-70b-versatile` | Default, fast |
| **🔵 OpenAI** | `gpt-3.5-turbo` / `gpt-4o-mini` | Throttled (5s gap between calls) |
| **🟡 Gemini** | `gemini-2.0-flash` | Uses `convert_messages_for_gemini()` |
| **⚪ fallback** | — | Returns static message (no API call) |

### ⚙️ Provider Configuration

- **🌍 Environment:** `AI_PROVIDER` (groq, gemini, openai, fallback)
- **📁 Config file:** `~/.viser_ai/config.json` or `~/.spec2/config.json`
- **🔑 API keys:** `.env` or config file (`GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENAI_API_KEY`)

---

## ✨ Special Features

### 📊 Table Handling

> - If user message contains "table", response is validated for Markdown table format
> - On invalid table: auto-retry with stricter prompt
> - Structural repair (`fix_table_hallucination`) for common AI table mistakes

### 📧 Email Command

> - Detects patterns like "send to user@example.com" or "email user@example.com: message"
> - Sends previous AI response or custom message via SMTP
> - Uses `detect_email_command()` and `send_email()`

### ⌨️ Slash Commands

> - `/files` — Load multi-file context
> - Handled in `handleSlashCommand()` in frontend

---

## 🖥️ Frontend Components

### 💬 ViseAIChat Class

| Property | Purpose |
|----------|---------|
| `chatMessages` | Container for message bubbles |
| `messageInput` | Text input |
| `sendBtn`, `uploadBtn` | Action buttons |
| `sessionId` | Unique session ID (e.g. `session_<timestamp>_<random>`) |
| `uploadedFiles` | Files for analysis/context |

### 🔄 Flow

1. User types message → `sendMessage()`
2. Slash commands: `handleSlashCommand()`
3. Analysis request + file: `analyzeLatestFile()`
4. Otherwise: `callAPIStreaming()` → `POST /api/chat/stream`
5. SSE chunks rendered in real-time via `_createStreamingBubble()`
6. On completion: `ContextManager.add_message()` persists

### 🔀 Provider Switcher

- `chatProviderSelect` dropdown → `POST /api/settings/provider`
- `_updateProviderUI(prov)` updates UI state

---

## 📦 Dependencies

- `requests` — REST API calls
- `openai`, `groq`, `google.generativeai` — AI providers
- `convert_messages_for_gemini()` — Message format conversion
- TOON (optional): `toon_encode` for compact context representation

---

## 📁 Related Files

| File | Role |
|------|------|
| `flask_server.py` | Backend routes, ContextManager, DB |
| `viser-ai-modern.html` | ViseAIChat, chat UI, provider switching |
| `data/chat_history.db` | SQLite persistence |
| `.env` | API keys |

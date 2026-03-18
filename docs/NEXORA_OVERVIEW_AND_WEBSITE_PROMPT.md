# Nexora — Complete Overview & Website Build Prompt

---

## Part 1: What is Nexora?

**Nexora** is an AI-powered productivity platform that combines conversational AI, QA intelligence, HR automation, business analysis, security testing, and browser automation into a single unified workspace. It is branded as "Nexora - AI Assistant" and serves as a multi-role assistant for QA engineers, HR teams, and business analysts.

### Core Identity

- **Product name:** Nexora  
- **Tagline / positioning:** AI Assistant for QA, HR, and BA  
- **Persona:** "Hi, I'm Nexora. How can I help you today?"  
- **Workspace model:** Role-based — QA, HR, BA — each with its own sidebar and tools  

---

## Part 2: Architecture & Tech Stack

### Frontend

- **Single-page app:** `viser-ai-modern.html` (HTML + CSS + vanilla JS)
- **Fonts:** DM Sans, Plus Jakarta Sans
- **Icons:** Font Awesome 6
- **Libraries:** Marked (Markdown), GridJS, XLSX, PapaParse, Socket.IO, Mermaid
- **Deployment:** Netlify (static hosting)

### Backend

- **Framework:** Flask + Flask-SocketIO
- **Database:** SQLite (`data/chat_history.db`) for chat history, saved items, analytics
- **AI providers:** Groq (default), OpenAI, Gemini
- **Deployment:** Render (Python web service)

### Design System

- **Theme:** Bella Kitchenware-inspired — Oatmilk (#DEDACD), Plum (#6B4C71), Surf (#00A6A6)
- **Primary accent:** Plum (#6B4C71)
- **Secondary accent:** Surf teal (#00A6A6)
- **Background:** Warm off-white (#EBEAE1)
- **Cards:** White with subtle shadows, 12px radius
- **Gradients:** `linear-gradient(135deg, #6B4C71 0%, #00A6A6 100%)` for buttons and highlights

---

## Part 3: Modules & Features

### 3.1 Chat (Core)

- AI conversation with streaming responses
- Multi-provider: Groq, OpenAI, Gemini
- File uploads for context (PDF, DOCX, TXT, images)
- Document analysis (`/api/analyze`) — extract and summarize
- Slash commands: `/help`, `/files`, `/resume`, `/screen`, `/mail`
- Session persistence in SQLite
- Smart summarization when history exceeds 30 messages

### 3.2 QA Workspace

| View | Description |
|------|-------------|
| **Chat** | Main AI chat with New Chat + history in sidebar |
| **Testcases** | Test case repository — Excel/Google Sheets import, filter, search, export |
| **Automation** | AI Automation Workbench — URL + task → plan → execute with browser-use (AI agent) or Playwright; final screenshot on completion |
| **QA Intelligence** | 9 AI tools in 3 groups: Test (Test Case, API Test, Test Data), Bug (Bug Log, Screenshot, Root Cause), Strategy (Regression Impact, Risk Advisor) |
| **Security** | 5 AI tools: OWASP Threat Modeler, Security Test Cases, Vulnerability Advisor, Auth Flow Reviewer, API Security Checker |
| **Saved** | Saved results from QA/Security/BA tools — filter, search, view, delete |
| **Analytics** | Dashboard: stat cards (Test Cases, Documents, etc.), tool usage bars, category breakdown, recent activity |
| **Documents** | User-uploaded documents — view, analyze, delete |
| **History** | Conversation history — search, filter, clear |
| **Help** | Feature overview |
| **Settings** | API keys, repository config, theme |

### 3.3 HR Workspace

| View | Description |
|------|-------------|
| **Resume Analyzer** | Upload PDF/DOCX/TXT → AI extracts name, email, skills, experience, education |
| **Candidate Screening** | Job description + resumes → AI ranks with match %, skill coding; bulk accept/reject emails |
| **Mail Automation** | Templates: Interview Invite, Rejection, Follow-up, Offer — generate and send |
| **Employee Documents** | (Coming soon) |

### 3.4 BA Workspace

| View | Description |
|------|-------------|
| **Requirement Analyzer** | Upload or paste requirements → AI extracts features, acceptance criteria, dependencies, risks |
| **User Story Generator** | Requirements → user stories, use cases, or epics |
| **Flow Diagram Builder** | Process description → Mermaid flowchart |

### 3.5 Saved Items & Analytics

- **Saved:** Save any QA/Security/BA tool result with optional title; filter by QA/Security/BA; view, delete
- **Analytics:** Total saved, this week, chat messages, tools used; tool usage bars; category tiles; recent activity with relative timestamps

---

## Part 4: User Flow & Auth

- **Login:** Email + password + workspace (qa/hr/ba) — users are restricted to their workspace
- **Session:** Stored in sessionStorage; sidebar loads workspace-specific nav
- **API auth:** `X-User-Id` header (email) for user-scoped data

---

## Part 5: Key API Groups

| Prefix | Purpose |
|--------|---------|
| `/api/chat`, `/api/chat/stream` | Chat + streaming |
| `/api/analyze` | Document analysis |
| `/api/upload` | File uploads |
| `/api/qa/*` | QA Intelligence (test-case, test-data, bug-log, screenshot, root-cause, regression, risk) |
| `/api/security/*` | Security (threat-model, test-cases, vulnerability-advisor, auth-review, api-security-check) |
| `/api/hr/*` | HR (resume-analyze, screen, mail-draft, send-mail) |
| `/api/ba-*` | BA (requirement-analyze, user-story-generate, flow-diagram-generate) |
| `/api/items/*` | Saved items (save, list, get, delete) |
| `/api/analytics/summary` | Analytics dashboard data |
| `/api/documents` | User documents |
| `/api/repo/*` | Test case repository (Excel, Google Sheets) |
| Socket.IO | Automation (execute_task, plan_task, step_update, task_success, log_message) |

---

## Part 6: Website Build Prompt

Use the following prompt when instructing an AI or developer to build a **marketing/landing website** for Nexora:

---

```
You are building a marketing/landing website for **Nexora** — an AI-powered productivity platform.

## Product Summary

Nexora is an AI Assistant that combines:
- **QA Intelligence:** Test case generation, bug analysis, regression planning, risk assessment
- **Security Intelligence:** OWASP threat modeling, security test cases, vulnerability analysis, auth review, API security checks
- **HR Automation:** Resume analysis, candidate screening, interview/rejection/offer email generation
- **Business Analysis:** Requirement analysis, user story generation, flow diagram creation
- **AI Automation:** Natural-language browser automation (e.g., "test the cart scenario") with AI agent
- **Unified Chat:** Multi-provider AI (Groq, OpenAI, Gemini) with document analysis and context awareness

## Brand

- **Name:** Nexora
- **Tagline:** AI Assistant for QA, HR & BA (or similar)
- **Colors:** Plum (#6B4C71), Surf teal (#00A6A6), Oatmilk off-white (#DEDACD), warm background (#EBEAE1)
- **Typography:** DM Sans, Plus Jakarta Sans — clean, modern
- **Tone:** Professional, helpful, AI-powered — "Hi, I'm Nexora. How can I help you today?"

## Target Audiences

1. **QA Engineers** — test case generation, bug analysis, automation, security testing
2. **HR Teams** — resume screening, candidate ranking, email automation
3. **Business Analysts** — requirement analysis, user stories, flow diagrams

## Website Requirements

Build a modern, responsive landing/marketing site that:

1. **Hero section** — Clear value proposition: "Nexora — AI Assistant for QA, HR & Business Analysis"
2. **Feature sections** — Highlight the 5 pillars: QA Intelligence, Security Intelligence, HR Automation, BA Tools, AI Automation
3. **Use cases** — Short scenarios: "Generate test cases from a PRD", "Screen 50 resumes in minutes", "Threat model your API"
4. **Design** — Use Nexora's color palette (plum, teal, oatmilk), clean cards, subtle gradients
5. **CTA** — "Try Nexora" or "Get Started" linking to the app URL
6. **Footer** — Links to docs, support, or contact

## Technical Notes

- The actual app is a SPA served at a separate URL (e.g., Netlify + Render backend)
- The marketing site can be static HTML/CSS/JS or a simple framework (React, Next, etc.)
- Ensure mobile responsiveness and fast load times
```

---

## Part 7: Quick Reference — Module Map

```
Nexora
├── Chat (core)
├── QA Workspace
│   ├── Testcases (repository)
│   ├── Automation (browser-use / Playwright)
│   ├── QA Intelligence (9 tools)
│   ├── Security (5 tools)
│   ├── Saved
│   ├── Analytics
│   ├── Documents
│   ├── History
│   ├── Help
│   └── Settings
├── HR Workspace
│   ├── Resume Analyzer
│   ├── Candidate Screening
│   ├── Mail Automation
│   └── Employee Documents (coming soon)
└── BA Workspace
    ├── Requirement Analyzer
    ├── User Story Generator
    └── Flow Diagram Builder
```

---

*Generated from Nexora.ai codebase — use this document to onboard developers or instruct AI to build a Nexora marketing website.*

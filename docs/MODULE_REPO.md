# 📁 Repo Module (Testcase Repository) Documentation

<p align="center">
  <strong>🟢 Excel-Based Test Case Management</strong>
</p>

---

## 📋 Overview

> **💚 The Repo Module** (Testcase Repository) manages test case data stored in Excel (`.xlsx`) files. It provides listing, loading, filtering, pagination, and export (CSV/Excel) functionality. Data can be loaded from the server or imported directly by the user.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🌐 viser-ai-modern.html (SPA)                                          │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ 📁 ViseAIChat.setupRepository()                                    │  │
│  │  • allRepoData, currentRepoFile, filteredRepoData                  │  │
│  │  • repoPage, repoItemsPerPage (25)                                  │  │
│  │  • loadRepositoryData() → /api/repo/files, /api/repo/load/<file>    │  │
│  │  • populateRepoFilters(), applyFilters(), renderRepoTable()         │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  🐍 flask_server.py                                                      │  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ /api/repo/files     → List .xlsx files in Test Archive/            │  │
│  │ /api/repo/load/<fn> → Return raw file for client-side parsing     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  📂 Test Archive/                                                        │
│  • *.xlsx files (test case repositories)                                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Backend Components

### 📍 Location
- **📄 File:** `flask_server.py`
- **📏 Lines:** ~525–550

### 🔌 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/repo/files` | `GET` | List all `.xlsx` files in `Test Archive/` |
| `/api/repo/load/<filename>` | `GET` | Serve raw file for client-side parsing |

### 📤 Response Format

**`/api/repo/files`**
```json
{
  "success": true,
  "files": ["file1.xlsx", "file2.xlsx"],
  "count": 2
}
```

**`/api/repo/load/<filename>`**
- Returns raw file bytes (via `send_from_directory`)
- Client parses with SheetJS (XLSX)

---

## 📂 Data Source

- **📁 Directory:** `Test Archive/` (relative to project root)
- **📊 Format:** Excel `.xlsx` files
- **🔧 Parsing:** Client-side via SheetJS (`XLSX.read()`, `XLSX.utils.sheet_to_json()`)

---

## 📊 Data Model

> Test cases are parsed from Excel rows. Supported column names (case-insensitive):

| Field | Aliases |
|-------|---------|
| `Module` | Sheet name (auto-assigned) |
| `TC ID` | TCID, ID, Test ID |
| `Priority` | priority, PRIORITY |
| `Test Type` | Type, type, TYPE |
| `Test Scenario` | Scenario, Title |
| `Test steps` | Steps |
| `Expected Result` | Expected |

---

## 🖥️ Frontend Components

### 📦 State Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `allRepoData` | `{ [filename]: row[] }` | All loaded file data |
| `currentRepoFile` | string | Currently selected file |
| `filteredRepoData` | `row[]` | Data after filters |
| `repoPage` | number | Current page (1-based) |
| `repoItemsPerPage` | number | 25 (default) |

### 🔍 Filters

| Filter | Element ID | Behavior |
|--------|------------|----------|
| 📌 Module | `repoModuleFilter` | Exact match (from sheet name) |
| ⚡ Priority | `repoPriorityFilter` | Case-insensitive |
| 📋 Type | `repoTypeFilter` | Case-insensitive |
| 🔎 Search | `repoSearch` | Searches TC ID, Scenario, Steps, Expected, Module |

### 🎬 Actions

| Action | Button ID | Behavior |
|--------|-----------|----------|
| 📤 Import | `repoUpload` | File input → parse XLSX in browser |
| 🔄 Refresh | `repoRefreshBtn` | Reload from server via `loadRepositoryData()` |
| 📄 Export CSV | `repoExportCsvBtn` | Export `filteredRepoData` as CSV |
| 📊 Export Excel | `repoExportExcelBtn` | Export `filteredRepoData` as XLSX |
| 🧹 Clear Filters | `repoClearFiltersBtn` | Reset all filters |

### 📑 Pagination

- **⬅️ Prev / ➡️ Next:** `prevPageBtn`, `nextPageBtn`
- **📏 Page size:** 25 items
- **🖼️ Display:** `renderRepoTable()` shows current page slice

---

## 🔄 Frontend Flow

1. **📥 Initial load:** `loadRepositoryData()` (if server files exist)
   - `GET /api/repo/files` → list files
   - For each file: `GET /api/repo/load/<file>` → parse with XLSX
   - Populate `allRepoData`, `fileSelector`, filters

2. **📤 User import:** `repoUpload` change → FileReader → XLSX.read → `allRepoData[file.name]`

3. **📂 File selection:** `fileSelector` change
   - If in `allRepoData`: use cached
   - Else: fetch from server, parse, cache

4. **🔍 Filter change:** `applyFilters()` → update `filteredRepoData` → `renderRepoTable()`

5. **📤 Export:** Uses `filteredRepoData` for CSV/Excel download

---

## 📦 Dependencies

- **SheetJS (XLSX):** Client-side Excel parsing
- **Flask:** `send_from_directory` for file serving

---

## 📁 Related Files

| File | Role |
|------|------|
| `flask_server.py` | `/api/repo/files`, `/api/repo/load/<filename>` |
| `viser-ai-modern.html` | `setupRepository()`, `loadRepositoryData()`, `renderRepoTable()` |
| `Test Archive/` | Directory containing `.xlsx` files |

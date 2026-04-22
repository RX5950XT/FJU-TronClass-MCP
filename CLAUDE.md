# FJU TronClass MCP — 專案指引

## 專案概述

輔仁大學 TronClass e-learning 系統的 MCP Server + CLI 工具。
讓 Claude Desktop / Claude Code 能直接操作課程管理，並提供 `fjumcp` CLI 供終端機使用。

## 開發環境

```powershell
# 安裝依賴
uv sync

# 執行測試（含覆蓋率）
uv run pytest --cov

# Lint
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Type check
uv run mypy src/

# 執行 CLI
uv run fjumcp <command>
# 或直接用 venv
.venv/Scripts/fjumcp.exe <command>
```

## 架構

```
src/fju_tronclass/
├── client/          # HTTP 層（TronClassHttp + TronClassClient）
├── models/          # Pydantic models（Course、Todo、Bulletin、Activity）
├── services/        # 業務邏輯（courses、todos、bulletins、search、video）
├── mcp_server/      # FastMCP server + tools
│   └── tools/       # 各功能 MCP tool 定義
├── cli/             # Typer CLI
│   └── commands/    # 子指令（courses、todos、bulletins、activities、download、video）
├── auth/            # Cookie 管理（keyring + env）
└── config.py        # pydantic-settings（讀 .env）
```

## 真實 API 端點（已驗證）

| 功能 | 端點 |
|------|------|
| 課程清單 | `GET /api/my-courses?page=1&page_size=20` |
| 待辦事項 | `GET /api/todos` |
| 課程公告 | `GET /api/course-bulletins?course_id={id}` |
| 課程活動 | `GET /api/courses/{id}/activities` ← 注意複數 |
| 取得活動 | `GET /api/course/{id}/learning-activity/{activity_id}` |
| 取得 Upload URL | `GET /api/uploads/{id}/url` |
| 取得 Upload Meta | `GET /api/uploads/{id}` |
| 標記影片進度 | `POST /api/course/activities-read/{activity_id}` |

## API Response Key 對照（已驗證）

| Model | 實際 key | 錯誤假設 |
|-------|----------|----------|
| CourseListResponse | `courses` | ~~`list`~~ |
| TodoListResponse | `todo_list` | ~~`list`~~ |
| BulletinListResponse | `bulletins` | ~~`list`~~ |
| ActivityListResponse | `activities` | ~~`list`~~ |

## 學期格式

- API 回傳：`academic_year.name + "-" + semester.real_name`（例：`"114-2"`）
- 目前學期（2026-04-23）：`114-2`

## 重要注意事項

- `Activity.name`、`Activity.completeness`、`Activity.completenessTip` 可為 `null`
- `Todo.due_time` 對應 API 的 `end_time`（alias）
- `post_activity_read` 每次 end-start 不可超過 125 秒（伺服器限制）
- Cookie 優先順序：環境變數 > `.env` 檔 > Windows Credential Manager

## 測試策略

- 單元測試：mock client，不需真實 server
- 整合測試：`tests/integration/` — 只驗證 MCP tool contract（不呼叫真實 API）
- 覆蓋率閾值：80%（src 層，排除 cli/auth/config）
- 不要 mock 真實 HTTP；`pytest-httpx` 用於攔截 httpx 請求

## Git 提交格式

```
<type>: <description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

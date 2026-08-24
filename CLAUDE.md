# FJU TronClass MCP — 專案指引

## 專案概述

輔仁大學 TronClass e-learning 系統的 MCP Server + CLI 工具。
讓 Claude Desktop / Claude Code 能直接操作課程管理，並提供 `fjumcp` CLI 供終端機使用。

## 開發環境

```bash
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
# Windows venv
.venv/Scripts/fjumcp.exe <command>
# Linux / WSL venv
.venv/bin/fjumcp <command>
```

## 架構

```
src/fju_tronclass/
├── client/          # HTTP 層（TronClassHttp + TronClassClient）
├── models/          # Pydantic models（Course、Todo、Bulletin、Activity、Person、catalog）
├── services/        # 業務邏輯（courses、todos、people、downloads、search、video）
├── mcp_server/      # FastMCP server + tools
│   └── tools/       # 各功能 MCP tool 定義
├── cli/             # Typer CLI
│   └── commands/    # courses/todos/people/groups/homework/scores/forums/digest…
├── auth/            # Cookie 管理（keyring + XDG 檔案 + env）
└── config.py        # pydantic-settings（讀 .env）
```

## 真實 API 端點（已驗證）

| 功能 | 端點 |
|------|------|
| 課程清單 | `GET /api/my-courses?page=1&page_size=20` |
| 待辦事項 | `GET /api/todos` |
| 課程公告 | `GET /api/course-bulletins?course_id={id}` |
| 課程活動 | `GET /api/courses/{id}/activities` ← 注意複數 |
| 活動詳情 | `GET /api/activities/{id}`（learning-activity 路徑常 404） |
| 取得 Upload URL | `GET /api/uploads/{id}/url` |
| 取得 Upload Meta | `GET /api/uploads/{id}` |
| 標記影片進度 | `POST /api/course/activities-read/{activity_id}` |
| 個人檔案 | `GET /api/profile` |
| 課程詳情 / 大綱 / 模組 | `GET /api/courses/{id}`、`/outline`、`/modules` |
| 修課名單 | `GET /api/course/{id}/students` |
| 分組集合 | `GET /api/courses/{id}/group-sets`（學生通常只看到自己組名） |
| 作業 | `GET /api/courses/{id}/homework-activities` |
| 討論主題 | `GET /api/activities/{id}/topics` |
| 成績組成 | `GET /api/courses/{id}/score-items` |

## API Response Key 對照（已驗證）

| Model | 實際 key | 錯誤假設 |
|-------|----------|----------|
| CourseListResponse | `courses` | ~~`list`~~ |
| TodoListResponse | `todo_list` | ~~`list`~~ |
| BulletinListResponse | `bulletins` | ~~`list`~~ |
| ActivityListResponse | `activities` | ~~`list`~~ |

## 學期格式

- API 回傳：`academic_year.name + "-" + semester.real_name`（例：`"114-2"`）
- 2026-08-24：課表仍是 114-2；115-1 尚未出現

## 重要注意事項

- `Activity.name`、`Activity.completeness`、`Activity.completenessTip` 可為 `null`
- `Todo.due_time` 對應 API 的 `end_time`（alias）
- `post_activity_read` 每次 end-start 不可超過 125 秒（伺服器限制）
- Cookie 優先順序：keyring > `~/.config/fju-tronclass/session` > 環境變數 / `.env`
- Session 效期 24 小時滑動；伺服器每次回應 rotate cookie，`TronClassHttp.session_cookie` 追蹤最新值。`whoami` / `keepalive` / CLI+MCP factory 成功結束時自動存回（持續使用即持續延長）
- Linux / WSL 沒有 Credential Manager 時走本機 0600 檔案；`fjumcp keepalive` 給排程用（成功安靜）
- Session 過期實測回 401；cookie 非 HttpOnly，可從已登入瀏覽器的 `document.cookie` 取得
- API 呼叫維持 `follow_redirects=False`：被 302 導向登入頁 = session 過期（映射為 `SessionExpiredError`）；`stream_download` 例外，per-request 跟隨 redirect 到 CDN
- session cookie 已綁定 base_url host domain，不會送往外部下載主機

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

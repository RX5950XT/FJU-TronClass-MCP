# FJU TronClass MCP — Agent 指引

本檔內容與 `CLAUDE.md` 同步，供支援 `AGENTS.md` 的工具使用。

## 專案用途

- 提供 `fjumcp` CLI 操作輔大 TronClass
- 提供 MCP server 給 Claude Desktop / Claude Code 使用
- Hermes 本體走 CLI，不要把這個 server 掛進 `hermes mcp add`

## 啟動方式

```bash
uv sync
uv run fjumcp --help
uv run fjumcp serve
```

## 目前可用 CLI 指令

```text
fjumcp
├── whoami [--quiet] [--verbose]
├── keepalive [--verbose]
├── serve
├── courses list [--semester] [--json]
├── todos list [--include-done] [--json]
├── bulletins list [--limit] [--json]
├── activities list [--videos] [--materials] [--json]
├── download upload
├── download search
├── download course
├── people list
├── video mark-complete
├── video batch-complete
├── login [--cookie V2-...]
├── login cookie [--cookie V2-...]
└── login logout
```

## 驗證指令

```bash
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/
uv run fjumcp --help
```

## 認證

- session cookie 優先順序：keyring > `~/.config/fju-tronclass/session`（0600）> 環境變數 / `.env`
- Linux / WSL / headless 沒有可用 keyring 時，自動走本機檔案，rotation 仍會回寫
- 登入：`fjumcp login --cookie 'V2-...'` 或互動式 `fjumcp login`
- session 效期 24 小時滑動：伺服器每次回應 rotate cookie；`whoami` / `keepalive` / CLI factory / MCP factory 成功時寫回最新值
- 閒置超過一天會過期；排程跑 `fjumcp keepalive`（`scripts/keepalive.sh`）可維持
- cookie 非 HttpOnly，過期時可從已登入瀏覽器的 `document.cookie` 取得新值
- session 過期時伺服器回 401（已映射為 `SessionExpiredError`）

## 重要路徑

- CLI 入口：`src/fju_tronclass/cli/app.py`
- MCP 入口：`src/fju_tronclass/__main__.py`
- 設定：`src/fju_tronclass/config.py`
- Cookie 儲存：`src/fju_tronclass/auth/cookie_store.py`
- 驗證 + 回存：`src/fju_tronclass/auth/session.py`

## 規則

- 不要把 cookie 寫進 git / README / skill
- 不要做 group ID 暴力掃描
- 下載教材只供本人學習
- `video mark-complete` 會改觀看進度，先 `--dry-run`

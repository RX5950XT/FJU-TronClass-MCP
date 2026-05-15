# FJU TronClass MCP — Agent 指引

本檔內容與 `AGENT.md` 同步，供支援 `AGENTS.md` 的工具使用。

## 專案用途

- 提供 `fjumcp` CLI 操作輔大 TronClass
- 提供 MCP server 給 Claude Desktop / Claude Code 使用

## 啟動方式

```powershell
uv sync
uv run fjumcp --help
uv run fjumcp serve
```

## 目前可用 CLI 指令

```text
fjumcp
├── whoami
├── serve
├── courses list
├── todos list
├── bulletins list
├── activities list
├── download upload
├── download search
├── video mark-complete
├── video batch-complete
├── login cookie
└── login logout
```

## 驗證指令

```powershell
uv run pytest
uv run fjumcp --help
```

## 認證

- session cookie 優先讀取 Windows Credential Manager
- 若沒有 keyring，退回 `.env` 的 `TRONCLASS_SESSION_COOKIE`
- 目前登入指令是 `uv run fjumcp login cookie`

## 重要路徑

- CLI 入口：`src/fju_tronclass/cli/app.py`
- MCP 入口：`src/fju_tronclass/__main__.py`
- 設定：`src/fju_tronclass/config.py`
- Cookie 儲存邏輯：`src/fju_tronclass/auth/cookie_store.py`

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
├── whoami / keepalive / serve / login
├── profile
├── digest [--semester]
├── courses list|show|outline|modules
├── todos list
├── bulletins list [--full]
├── activities list [--type] / show
├── download upload|search|course|semester
├── people list / groups list
├── homework list|show
├── scores list / exams list
├── forums topics|topic
└── video mark-complete|batch-complete
```

所有 `list` / `show` 幾乎都有 `--json`。

## 驗證指令

```bash
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/
uv run fjumcp --help
```

## 認證

- session cookie 優先順序：keyring > `~/.config/fju-tronclass/session`（0600）> 環境變數 / `.env`
- 登入：`fjumcp login --cookie 'V2-...'`
- 24h 滑動；`keepalive` cron 維持
- 過期回 401

## 規則

- 不要把 cookie 寫進 git / README / skill
- 不要做 group ID 暴力掃描
- 不要代繳作業、改成績、代發討論
- 下載教材只供本人學習
- `video mark-complete` 先 `--dry-run`

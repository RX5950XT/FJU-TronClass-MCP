# FJU TronClass MCP

輔仁大學 TronClass 工具包。

- `fjumcp` CLI：查課程、看待辦、下載教材、看分組、看討論
- MCP Server：給 Claude Desktop / Claude Code
- Agent 手冊：[skills/SKILL.md](skills/SKILL.md)

自己用會 `fjumcp` 就夠。Agent 請讀 `skills/SKILL.md`。

## 能做什麼

- 課表、大綱、週次模組、個人檔案
- 待辦、公告（含內文）、作業說明與成績
- 教材搜尋 / 單課 / 整學期下載
- 修課名單、分組（官方 roster，不掃 ID）
- 討論主題與回覆、成績組成、考試
- 影片觀看進度標記（先 `--dry-run`）

## 安裝

需要 Python 3.11+ 與 [uv](https://docs.astral.sh/uv/)。

```bash
git clone https://github.com/RX5950XT/FJU-TronClass-MCP.git
cd FJU-TronClass-MCP
uv sync
uv tool install -e .    # 可選，裝成全域 fjumcp
```

## 登入

TronClass 有 CAS + CAPTCHA，這個工具吃 `session cookie`，不吃帳密。

1. 瀏覽器登入 https://elearn2.fju.edu.tw/
2. F12 → Application → Cookies → `session`（`V2-` 開頭）
3. 執行：

```bash
fjumcp login cookie
# 或給 agent / 腳本
fjumcp login --cookie 'V2-你的cookie值'
```

Cookie 存 keyring（Windows Credential Manager）。Linux / WSL 沒有可用 keyring 時寫到 `~/.config/fju-tronclass/session`（0600）。

`.env` 的 `TRONCLASS_SESSION_COOKIE` 是靜態備援，不會隨 rotate 更新。

Session 是 24 小時滑動制：每次成功 API 會換發新 cookie 並寫回。24 小時內用過（CLI、MCP 或 `keepalive`）就會延長。

```bash
fjumcp whoami
fjumcp keepalive          # 成功安靜、失敗非零
./scripts/keepalive.sh
```

## 常用指令

```bash
fjumcp --help
fjumcp digest
fjumcp courses list --semester 114-2
fjumcp courses show <course_id>
fjumcp todos list
fjumcp bulletins list <course_id> --full
fjumcp activities list <course_id> --type forum
fjumcp groups list <course_id> --json
fjumcp people list <course_id>
fjumcp homework list <course_id>
fjumcp scores list <course_id>
fjumcp forums topics <forum_activity_id>
fjumcp download course <course_id> --dry-run
fjumcp download semester 114-2 --dry-run
```

幾乎所有 `list` / `show` 都有 `--json`。

### 下載

```bash
fjumcp download upload <upload_id> --dest ~/Downloads/TronClass
fjumcp download search "講義" --course <course_id> --dry-run
fjumcp download course <course_id> --dry-run
fjumcp download semester 114-2 --dry-run
```

### 影片標記

```bash
fjumcp video mark-complete <activity_id> <duration_seconds> --dry-run
fjumcp video batch-complete <course_id> --dry-run
```

## 指令一覽

```text
fjumcp
├── whoami [--quiet] [--verbose]
├── keepalive [--verbose]
├── serve
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
├── video mark-complete|batch-complete
├── login [--cookie V2-...]
└── login logout
```

## MCP

```bash
fjumcp serve
# 或
python -m fju_tronclass
```

Claude Desktop `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "fju-tronclass": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/FJU-TronClass-MCP",
        "run",
        "python", "-m", "fju_tronclass"
      ]
    }
  }
}
```

Claude Code：

```bash
claude mcp add fju-tronclass -- uv --directory "/path/to/FJU-TronClass-MCP" run python -m fju_tronclass
```

已 `fjumcp login` 過就不用再塞 cookie。不要用靜態 `TRONCLASS_SESSION_COOKIE` 當主力。

| Tool | 說明 |
|------|------|
| `fju_check_auth` | 驗證 session（會回存 rotate cookie） |
| `fju_list_courses` | 列出課程 |
| `fju_list_todos` | 列出待辦 |
| `fju_list_course_bulletins` | 列出公告 |
| `fju_list_course_activities` | 列出活動 |
| `fju_get_activity` | 單一活動詳情 |
| `fju_get_upload_info` | 教材 metadata |
| `fju_download_upload` | 下載教材 |
| `fju_search_and_download` | 關鍵字搜尋下載 |
| `fju_mark_video_complete` | 標記單支影片 |
| `fju_batch_mark_videos_complete` | 批次標記影片 |

CLI 比 MCP 新（分組、討論、成績、digest 等目前以 CLI 為準）。

## 開發

```bash
uv run pytest
uv run pytest --cov=src --cov-report=term-missing
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
```

## 注意

- 只管理你自己的 TronClass 帳號
- 不要掃 group ID、不要打別組 submission
- `video mark-complete` 會改觀看進度
- 下載教材只作個人學習，不要散布

## 授權

MIT License

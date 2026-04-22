# FJU TronClass MCP

輔仁大學 TronClass e-learning 系統的 MCP Server + CLI 工具。

讓 AI（Claude Desktop / Claude Code）能直接操作課程管理，同時提供 `fjumcp` CLI 供終端機使用。

## 功能

- **列出課程**：取得本學期（或指定學期）的課程清單
- **待辦事項**：查看尚未完成的作業、影片等待辦項目
- **課程公告**：取得各課程的最新公告
- **下載教材**：下載課程 upload（即使設為不允許下載的教材也可下載）
- **標記影片完成**：更新影片觀看進度至 100%

## 安裝

### 前置需求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 套件管理器

### 安裝步驟

```powershell
git clone https://github.com/RX5950XT/FJU-TronClass-MCP.git
cd FJU-TronClass-MCP
uv sync
```

## 登入設定

TronClass 使用 CAS + CAPTCHA 登入，需先取得 session cookie：

### 方法一：手動複製 Cookie（推薦）

1. 在瀏覽器登入 https://elearn2.fju.edu.tw/
2. 開啟 DevTools（F12）→ Application → Cookies → `elearn2.fju.edu.tw`
3. 複製 **session** 欄位的值（以 `V2-` 開頭）
4. 執行：
   ```powershell
   uv run fjumcp login
   ```
   並貼上 cookie 值，確認後會儲存至 Windows Credential Manager。

### 方法二：環境變數 / .env

在專案根目錄建立 `.env` 檔：
```
TRONCLASS_SESSION_COOKIE=V2-你的cookie值
```

## CLI 使用

```powershell
# 驗證連線
uv run fjumcp whoami

# 列出課程（學期格式：114-2、114-1、113-2…）
uv run fjumcp courses list
uv run fjumcp courses list --semester 114-2

# 待辦事項
uv run fjumcp todos list
uv run fjumcp todos list --include-done

# 課程公告
uv run fjumcp bulletins list <course_id>

# 課程活動（教材 & 影片清單，含 upload ID）
uv run fjumcp activities list <course_id>
uv run fjumcp activities list <course_id> --videos-only

# 下載教材（upload ID 從 activities list 取得）
uv run fjumcp download upload <upload_id>
uv run fjumcp download upload <upload_id> --dest D:/Downloads

# 以關鍵字搜尋並下載（不需要知道 upload ID）
uv run fjumcp download search "關鍵字" --course <course_id>
uv run fjumcp download search "關鍵字" --all --dry-run   # 跨所有課程搜尋

# 標記單支影片完成（--dry-run 只顯示計畫，不實際執行）
uv run fjumcp video mark-complete <activity_id> <duration_seconds> --dry-run
uv run fjumcp video mark-complete <activity_id> <duration_seconds>

# 批次標記課程所有影片完成
uv run fjumcp video batch-complete <course_id> --dry-run
uv run fjumcp video batch-complete <course_id>

# 啟動 MCP server
uv run fjumcp serve
# 或
uv run python -m fju_tronclass
```

## Claude Desktop / Claude Code 設定

### Claude Desktop

在 `claude_desktop_config.json` 中加入：

```json
{
  "mcpServers": {
    "fju-tronclass": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/FJU-TronClass-MCP",
        "run",
        "python", "-m", "fju_tronclass"
      ],
      "env": {
        "TRONCLASS_SESSION_COOKIE": "V2-你的cookie值"
      }
    }
  }
}
```

將 `/path/to/FJU-TronClass-MCP` 替換為實際的 clone 路徑（例如 `C:/Users/yourname/FJU-TronClass-MCP`）。

### Claude Code

```powershell
claude mcp add fju-tronclass -- uv --directory "/path/to/FJU-TronClass-MCP" run python -m fju_tronclass
```

## MCP Tools

| Tool | 說明 |
|------|------|
| `fju_check_auth` | 驗證 session 是否有效 |
| `fju_list_courses` | 列出我的課程清單（可依學期過濾） |
| `fju_list_todos` | 列出待辦事項 |
| `fju_list_course_bulletins` | 列出課程公告 |
| `fju_list_course_activities` | 列出課程活動（教材 & 影片），含 upload ID |
| `fju_get_activity` | 取得單一活動詳情 |
| `fju_get_upload_info` | 取得教材 metadata |
| `fju_download_upload` | 下載課程教材 |
| `fju_search_and_download` | 以關鍵字搜尋教材並下載（不需 upload ID） |
| `fju_mark_video_complete` | 標記單支影片為完整觀看 |
| `fju_batch_mark_videos_complete` | 批次標記課程中所有影片為完整觀看 |

## 開發

```powershell
# 執行測試
uv run pytest

# 執行測試（含覆蓋率）
uv run pytest --cov=src --cov-report=term-missing

# Lint
uv run ruff check src/
uv run ruff format --check src/

# Type check
uv run mypy src/
```

## 聲明

本工具僅供作者本人學習、管理自身輔大 TronClass 帳號使用。
`fju_mark_video_complete` 相關功能會繞過觀看驗證機制，請自行評估是否違反課程與校方規定，使用者須為自己的學業誠信負責。
下載的課程教材僅供本人學習使用，請勿散佈。
本專案作者不承擔任何使用結果。

## 授權

MIT License

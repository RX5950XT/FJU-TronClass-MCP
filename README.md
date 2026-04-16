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
git clone <此 repo>
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

# 列出課程
uv run fjumcp courses list
uv run fjumcp courses list --semester 113-2

# 待辦事項
uv run fjumcp todos list
uv run fjumcp todos list --include-done

# 課程公告
uv run fjumcp bulletins list 10001

# 下載教材
uv run fjumcp download upload 30001
uv run fjumcp download upload 30001 --dest D:/Downloads

# 標記影片完成（--dry-run 只顯示計畫，不實際執行）
uv run fjumcp video mark-complete 40001 850 --dry-run
uv run fjumcp video mark-complete 40001 850

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
        "--directory", "D:/Workspace_cloud/Personal_Project/FJU-TronClass-MCP",
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

### Claude Code

```powershell
claude mcp add fju-tronclass -- uv --directory "D:/Workspace_cloud/Personal_Project/FJU-TronClass-MCP" run python -m fju_tronclass
```

## MCP Tools

| Tool | 說明 |
|------|------|
| `fju_check_auth` | 驗證 session 是否有效 |
| `fju_list_courses` | 列出我的課程清單 |
| `fju_list_todos` | 列出待辦事項 |
| `fju_list_course_bulletins` | 列出課程公告 |
| `fju_get_upload_info` | 取得教材 metadata |
| `fju_download_upload` | 下載課程教材 |
| `fju_get_activity` | 取得活動詳情 |
| `fju_mark_video_complete` | 標記影片為完整觀看 |

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

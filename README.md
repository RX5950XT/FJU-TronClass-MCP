# FJU TronClass MCP

這是一個給輔仁大學 TronClass 用的工具包。

你可以把它當成兩種東西：

- `fjumcp` CLI：在終端機查課程、看待辦、下載教材
- MCP Server：讓 Claude Desktop / Claude Code 直接操作 TronClass

如果你只是想自己用，通常只要會用 `fjumcp` 就夠了。
如果你是拿來給 agent 用，專案裡也有配套的 [skills\SKILL.md](D:\Workspace_cloud\Personal_Project\FJU-TronClass-MCP\skills\SKILL.md)，讓 agent 知道該怎麼登入、查資料、下載教材。

## 這個工具可以做什麼

- 看這學期有哪些課
- 看還沒完成的待辦事項
- 看課程公告
- 找教材、下載教材
- 列出課程活動與附件
- 把影片觀看進度標記完成

## 快速開始

### 1. 安裝

前置需求：

- Python 3.11 以上
- [uv](https://docs.astral.sh/uv/)

安裝步驟：

```powershell
git clone https://github.com/RX5950XT/FJU-TronClass-MCP.git
cd FJU-TronClass-MCP
uv sync
```

如果你想直接在任何地方輸入 `fjumcp`，可以再裝成全域 CLI：

```powershell
uv tool install -e .
```

## 2. 登入

TronClass 有 CAS + CAPTCHA，所以這個工具不是直接吃帳密，而是吃 `session cookie`。

最簡單的做法：

1. 先去瀏覽器登入 https://elearn2.fju.edu.tw/
2. 按 `F12` 打開 DevTools
3. 到 `Application -> Cookies -> elearn2.fju.edu.tw`
4. 找到 `session`，把值複製出來
5. 執行：

```powershell
fjumcp login cookie
```

貼上後，cookie 會存進 Windows Credential Manager。

你也可以放在專案根目錄的 `.env`：

```env
TRONCLASS_SESSION_COOKIE=V2-你的cookie值
```

注意：`session cookie` 不是永久有效，會隨時間失效。
如果你重新登入 TronClass、太久沒用，或伺服器那邊更新 session，舊 cookie 就可能不能用了。

## 3. 先確認有沒有連上

```powershell
fjumcp whoami
```

如果看到 `Session 已過期`，通常代表 cookie 失效了，重新抓一次新的即可。

## 常用指令

先看全部指令：

```powershell
fjumcp --help
```

### 課程

```powershell
fjumcp courses list
fjumcp courses list --semester 114-2
```

### 待辦事項

```powershell
fjumcp todos list
fjumcp todos list --include-done
```

### 課程公告

```powershell
fjumcp bulletins list <course_id>
fjumcp bulletins list <course_id> --limit 10
```

### 課程活動

```powershell
fjumcp activities list <course_id>
fjumcp activities list <course_id> --videos
fjumcp activities list <course_id> --materials
```

這個指令會幫你把課程裡的活動列出來。  
如果是教材，還會順便顯示 `upload ID`，後面下載時會用到。

### 下載教材

如果你已經知道 `upload ID`：

```powershell
fjumcp download upload <upload_id>
fjumcp download upload <upload_id> --dest D:/Downloads
```

如果你只記得關鍵字：

```powershell
fjumcp download search "期中"
fjumcp download search "講義" --course <course_id>
fjumcp download search "講義" --all --dry-run
```

`--dry-run` 很適合先確認搜尋結果，不會真的下載。

### 影片標記完成

單支影片：

```powershell
fjumcp video mark-complete <activity_id> <duration_seconds> --dry-run
fjumcp video mark-complete <activity_id> <duration_seconds>
```

整門課批次處理：

```powershell
fjumcp video batch-complete <course_id> --dry-run
fjumcp video batch-complete <course_id>
```

## 目前可用指令

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

## MCP 用法

如果你想讓 Claude 直接操作 TronClass，可以把這個專案當 MCP Server 啟動。

### 啟動 MCP Server

```powershell
fjumcp serve
```

或：

```powershell
python -m fju_tronclass
```

### Claude Desktop 設定

在 `claude_desktop_config.json` 加入：

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

把 `/path/to/FJU-TronClass-MCP` 換成你實際的專案路徑。

### Claude Code 設定

```powershell
claude mcp add fju-tronclass -- uv --directory "/path/to/FJU-TronClass-MCP" run python -m fju_tronclass
```

## MCP Tools

| Tool | 說明 |
|------|------|
| `fju_check_auth` | 驗證 session 是否有效 |
| `fju_list_courses` | 列出課程清單，可依學期過濾 |
| `fju_list_todos` | 列出待辦事項 |
| `fju_list_course_bulletins` | 列出課程公告 |
| `fju_list_course_activities` | 列出課程活動與附件 |
| `fju_get_activity` | 取得單一活動詳情 |
| `fju_get_upload_info` | 取得教材 metadata |
| `fju_download_upload` | 下載教材 |
| `fju_search_and_download` | 以關鍵字搜尋並下載教材 |
| `fju_mark_video_complete` | 標記單支影片完成 |
| `fju_batch_mark_videos_complete` | 批次標記課程影片完成 |

## 開發

```powershell
uv run pytest
uv run pytest --cov=src --cov-report=term-missing
uv run ruff check src/
uv run ruff format --check src/
uv run mypy src/
```

## 注意事項

- 這個工具只適合拿來管理你自己的 TronClass 帳號
- `session cookie` 會過期，失效時請重新從瀏覽器抓新的 `session`
- `video mark-complete` / `video batch-complete` 會直接更新觀看進度，請自己評估風險
- 下載下來的教材請只作個人學習使用，不要散布

## 授權

MIT License

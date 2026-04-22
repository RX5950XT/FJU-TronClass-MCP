---
name: fju-tronclass-mcp
description: 操作輔仁大學 TronClass MCP Server 與 CLI（fjumcp）的完整指引：課程查詢、教材下載、公告瀏覽、影片標記。觸發時機：使用者提到 TronClass、輔大課程、fjumcp、下載教材、影片完成。
version: 1.0.0
---

# FJU TronClass MCP — 操作技能

執行 CLI 前先確認 `.env` 存在且有效：
```powershell
# 在 clone 下來的專案目錄中執行
uv run fjumcp whoami
```

---

## 認證設定

Cookie 儲存方式（三選一，優先順序依序）：
1. 環境變數：`TRONCLASS_SESSION_COOKIE=V2-...`
2. `.env` 檔（專案根目錄）：`TRONCLASS_SESSION_COOKIE=V2-...`
3. Windows Credential Manager：`uv run fjumcp login`

**取得 Cookie**：瀏覽器登入 https://elearn2.fju.edu.tw → F12 → Application → Cookies → 複製 `session` 欄位（`V2-` 開頭）

---

## CLI 完整指令

### 連線驗證

```powershell
fjumcp whoami
# 輸出：已連線 — 本學期共 N 門課程
```

### 課程查詢

```powershell
# 列出所有課程（含歷史學期）
fjumcp courses list

# 過濾特定學期（格式：學年-學期，如 114-2、114-1、113-2）
fjumcp courses list --semester 114-2
```

**輸出欄位**：`ID | 課程名稱 | 代碼 | 學期 | 授課教師`
→ 記住 `ID` 欄位，後續所有指令都需要 `course_id`

### 待辦事項

```powershell
fjumcp todos list               # 只列未完成
fjumcp todos list --include-done  # 含已完成
```

### 課程公告

```powershell
fjumcp bulletins list <course_id>
```

### 課程活動（教材與影片）

```powershell
# 列出課程所有活動，附件清單會顯示 upload ID
fjumcp activities list <course_id>

# 只顯示影片類型
fjumcp activities list <course_id> --videos-only
```

**輸出說明**：
- `type=教材`：有「upload ID」→ 用於 `download upload`
- `type=影片`：有「activity ID + 時長」→ 用於 `video mark-complete`

### 下載教材

```powershell
# 用 upload ID 直接下載（從 activities list 取得）
fjumcp download upload <upload_id>
fjumcp download upload <upload_id> --dest D:/Downloads

# 用關鍵字搜尋後下載（不需要知道 ID）
fjumcp download search "關鍵字" --course <course_id>
fjumcp download search "關鍵字" --all          # 跨所有課程搜尋
fjumcp download search "關鍵字" --all --dry-run  # 預覽，不實際下載
```

### 影片完成標記

```powershell
# 標記單支影片（先用 dry-run 確認）
fjumcp video mark-complete <activity_id> <duration_seconds> --dry-run
fjumcp video mark-complete <activity_id> <duration_seconds>

# 批次標記課程中所有影片
fjumcp video batch-complete <course_id> --dry-run
fjumcp video batch-complete <course_id>
fjumcp video batch-complete <course_id> --include-completed  # 含已完成
```

---

## 常見工作流程

### 工作流程 A：下載特定課程的所有教材

```powershell
# 1. 找到 course_id
fjumcp courses list --semester 114-2

# 2. 查看該課程的活動和 upload ID
fjumcp activities list <course_id>

# 3. 下載需要的 upload
fjumcp download upload <upload_id> --dest ~/Downloads
```

### 工作流程 B：關鍵字搜尋下載

```powershell
# 不知道 ID，只知道檔案名稱關鍵字
fjumcp download search "期中" --course <course_id>
fjumcp download search "講義" --all --dry-run  # 先 dry-run 確認
```

### 工作流程 C：查看所有課程待辦

```powershell
fjumcp todos list  # 列出所有未繳交的作業，含截止時間
```

---

## MCP Tools（供 Claude 使用）

| Tool | 對應 CLI | 說明 |
|------|----------|------|
| `fju_check_auth` | `whoami` | 驗證 session |
| `fju_list_courses` | `courses list` | 列出課程，可傳 `semester` |
| `fju_list_todos` | `todos list` | 列出待辦 |
| `fju_list_course_bulletins` | `bulletins list` | 列出公告 |
| `fju_list_course_activities` | `activities list` | 列出活動 + upload ID |
| `fju_get_activity` | — | 取得單一活動詳情 |
| `fju_get_upload_info` | — | 取得教材 metadata |
| `fju_download_upload` | `download upload` | 下載教材 |
| `fju_search_and_download` | `download search` | 關鍵字搜尋並下載 |
| `fju_mark_video_complete` | `video mark-complete` | 標記單支影片 |
| `fju_batch_mark_videos_complete` | `video batch-complete` | 批次標記影片 |

---

## 重要技術細節

- **學期格式**：`學年-學期`，如 `114-2`（民國 114 年第 2 學期）
- **API 限制**：`post_activity_read` 每段最多 125 秒，超過會自動分段
- **影片 activity_id**：從 `activities list --videos-only` 取得，不是 upload_id
- **Cookie 有效期**：session 可能過期，過期時 `whoami` 會顯示認證失敗
- **下載路徑預設**：`~/Downloads/TronClass/`，可用 `--dest` 覆蓋

---

## 環境資訊

- **執行檔**：`uv run fjumcp`（或 `.venv/Scripts/fjumcp.exe`）
- **MCP Server**：`uv run python -m fju_tronclass`
- **GitHub**：https://github.com/RX5950XT/FJU-TronClass-MCP
- **安裝**：`git clone https://github.com/RX5950XT/FJU-TronClass-MCP.git && uv sync`

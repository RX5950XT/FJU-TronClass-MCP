---
name: fju-tronclass-mcp
description: 操作輔仁大學 TronClass 的 fjumcp CLI：課程、待辦、公告、教材下載、分組名單、作業、成績組成、討論區、影片標記。觸發：TronClass、輔大課程、fjumcp、下載教材、分組、影片完成。
version: 1.2.0
---

# FJU TronClass — Agent 操作手冊

任務碰到輔大 TronClass、`fjumcp`、教材、待辦、分組、作業、討論、影片完成時，依這份操作。

先確認 session：

```bash
fjumcp whoami
```

所有 `list` / `show` 幾乎都有 `--json`，agent 優先加 `--json` 再解析。

---

## 認證

優先順序（與程式碼一致）：

1. keyring（Windows Credential Manager）
2. `~/.config/fju-tronclass/session`（0600；Linux / WSL 主力）
3. 環境變數 / 專案 `.env`：`TRONCLASS_SESSION_COOKIE`（靜態，不會 rotate）

```bash
fjumcp login --cookie 'V2-...'
printf '%s' "$TRONCLASS_SESSION_COOKIE" | fjumcp login
fjumcp keepalive          # 成功安靜、失敗非零
```

Cookie 從 https://elearn2.fju.edu.tw → F12 → Application → Cookies → `session`（`V2-` 開頭）。

24 小時滑動制：每次成功 API 會 rotate 並寫回。閒置超過一天要重新登入。不要把 cookie 寫進 git / skill / README。

---

## CLI

```text
fjumcp
├── whoami [-q] [-v]
├── keepalive [-v]
├── profile [--json]
├── digest [--semester] [--json]
├── courses list [--semester] [--json]
├── courses show|outline|modules <course_id>
├── todos list [--include-done] [--json]
├── bulletins list <course_id> [--full] [--json]
├── activities list <course_id> [--type T] [--videos] [--materials] [--json]
├── activities show <activity_id>
├── download upload <upload_id> [--dest]
├── download search "關鍵字" --course ID | --all [--dry-run]
├── download course <course_id> [--dry-run]
├── download semester 114-2 [--dry-run]
├── people list <course_id> [--role student|instructor] [--json]
├── groups list <course_id> [--json]
├── homework list|show
├── scores list <course_id>
├── exams list <course_id>
├── forums topics <forum_activity_id>
├── forums topic <topic_id>
├── video mark-complete / batch-complete   # 先 --dry-run
├── login [--cookie V2-...]
└── serve
```

`course_id` 一律先從 `fjumcp courses list` 拿。

活動 `type`：`material` / `online_video` / `homework` / `forum` / `web_link` / `page`

---

## 工作流程

### 查分組（互評看每組成員）

```bash
fjumcp courses list --semester 114-2 --json
fjumcp groups list <course_id> --json
```

用官方 `students.group_ids` 聚合，不掃 group ID。看得到全班誰在哪一組；看不到別組交的作業檔。

114-2 有分組：電子學(二) `374430`、人生哲學 `378195`。115-1 尚未進課表。

### 下載教材

```bash
fjumcp download course <course_id> --dry-run
fjumcp download semester 114-2 --dry-run
fjumcp download search "講義" --course <course_id> --dry-run
```

### 討論 / 作業說明

```bash
fjumcp activities list <course_id> --type forum --json
fjumcp forums topics <activity_id> --json
fjumcp forums topic <topic_id>
fjumcp homework show <homework_id>
```

### 待辦與摘要

```bash
fjumcp digest
fjumcp todos list --json
```

---

## 禁止

- 不要把 cookie 寫進 git / README / skill
- 不要做 group ID 暴力掃描、不要打別組 submission
- 不要代繳作業、改成績、代發討論
- `video mark-complete` 先 `--dry-run`
- Hermes 本體走 CLI，不要 `hermes mcp add`

學生權限沒有：inbox、calendar、notifications、點名明細、未公布的逐項成績。

---

## 環境

- 執行檔：`fjumcp`（`uv tool install -e .`）或 `uv run fjumcp`
- clone：`~/workspace/github/FJU-TronClass-MCP`
- cookie：`~/.config/fju-tronclass/session`
- GitHub：https://github.com/RX5950XT/FJU-TronClass-MCP

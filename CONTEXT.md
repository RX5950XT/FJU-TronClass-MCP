# CONTEXT — 開發交接紀錄

> 給下一個 AI Agent 的接手文件。專案規範見 `CLAUDE.md` / `AGENTS.md`。

## 專案狀態（2026-08-24）

- 版本：0.4.0
- 測試：143+ passed
- 新增：profile / digest / courses show·outline·modules / scores / exams / forums / activities show / homework show / bulletin --full
- 分組用官方 `students.group_ids` 聚合，不掃 group ID
- 已探測無 inbox / calendar / 逐項已公布成績 API

## 2026-08-24：WSL 檔案庫 + keepalive + whoami 回存

先前 CONTEXT 寫「whoami 跑過會自動更新 cookie」是錯的——`whoami` / `fju_check_auth` 自己開 `TronClassHttp`，沒走 factory，rotate 後的值直接丟掉。
Linux / WSL 也沒有 Windows Credential Manager；keyring 常直接炸，cookie 落地失敗。

這次修：

1. `cookie_store`：keyring 包 try/except；失敗改寫 `~/.config/fju-tronclass/session`（0600）
2. `auth/session.py:verify_and_persist`：whoami / keepalive / login / `fju_check_auth` 共用
3. `fjumcp keepalive`：成功安靜、失敗非零，給 cron
4. `fjumcp login --cookie` / stdin：給 agent 非互動登入
5. `probe_session` 改讀 API `total`（以前 `page_size=1` 再 `len()`，whoami 永遠顯示 0 或 1）

## 2026-07-17：bug 修復 + cookie 過期問題

TronClass 伺服器每次回應會 rotate session cookie（Set-Cookie 新值延長效期），
但舊程式從未把新值存回 keyring → keyring 裡永遠是登入當下那顆，放著就過期。

修復鏈（`client/http.py` → 兩個 client factory）：

1. `TronClassHttp._request_with_retry` 從每個 response 擷取 rotated cookie，存於 `_session_cookie`
2. `TronClassHttp.session_cookie` property 曝露最新值
3. `cli/_helpers.py:build_client` 與 `mcp_server/_client_factory.py:get_client` 在 context manager **成功結束**時，若 cookie 有變就 `save_cookie()`（失敗時不存，避免把匿名 session 蓋掉好 cookie）

### 同批修復的其他 bug

- **302 導向登入頁**：API 呼叫 `follow_redirects=False`，session 過期若回 302 會拋 JSONDecodeError；現在 `_raise_for_status` 將 redirect 映射為 `SessionExpiredError`
- **下載 302 靜默損壞**：`stream_download` 不跟隨 redirect，會把空 redirect body 寫入檔案還回報成功；現在 per-request `follow_redirects=True`
- **Cookie 洩漏**：cookie 原以 dict 傳入（domain-less，會送往任何 host 含外部 CDN）；現在綁定 base_url host
- **stream 錯誤訊息**：stream response 在 4xx/5xx 時先 `aread()`，否則 `.json()/.text` 拋 `ResponseNotRead`
- **mypy**：`run_async_command` 參數型別 `Awaitable` → `Coroutine`（`asyncio.run` 要求）
- **文件錯誤**：CLAUDE.md 的 cookie 優先順序與程式碼相反，已修正為 keyring 優先
- 移除 `session_probe.py` 無效的 try/except（純 re-raise）

## 真實環境驗證結果

- Session 過期時伺服器回 **401**（實測，非 302；302 映射為額外防護）
- Session 效期為 **24 小時滑動**（cookie 第三段為到期 ms timestamp）；rotation 回存後每次使用自動延長 24h
- session cookie **非 HttpOnly**，可從瀏覽器 `document.cookie` 直接取得
- `.env` 的 `TRONCLASS_SESSION_COOKIE` 是靜態值，不會 rotate，只當備援

## 已知限制 / 未做的事

- Cookie rotation 只能「滑動延長」；session 若閒置到絕對過期仍需重新登入
- `stream_download` 不追蹤 cookie rotation（下載走 CDN，不會 rotate session）
- Playwright 半自動登入函式存在但未掛上 CLI 指令

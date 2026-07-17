# CONTEXT — 開發交接紀錄

> 給下一個 AI Agent 的接手文件。專案規範見 `CLAUDE.md` / `AGENTS.md`。

## 專案狀態（2026-07-17）

- 測試：126 passed，覆蓋率 93.77%（閾值 80%）
- Lint / mypy：全部通過
- 驗證指令：`uv run pytest --cov` + `uv run ruff check src/ tests/` + `uv run mypy src/`
- 注意：venv 可能被執行中的 MCP server 鎖住導致 `uv run` 失敗（os error 5），此時改用 `.venv/Scripts/python.exe -m <tool>`

## 最近一次任務：bug 修復 + cookie 過期問題（2026-07-17）

### Cookie 一直過期的根因與修法

TronClass 伺服器每次回應會 rotate session cookie（Set-Cookie 新值延長效期），
但舊程式從未把新值存回 keyring → keyring 裡永遠是登入當下那顆，放著就過期。

修復鏈（`client/http.py` → 兩個 client factory）：

1. `TronClassHttp._request_with_retry` 從每個 response 擷取 rotated cookie，存於 `_session_cookie`
2. `TronClassHttp.session_cookie` property 曝露最新值
3. `cli/_helpers.py:build_client` 與 `mcp_server/_client_factory.py:get_client` 在 context manager **成功結束**時，若 cookie 有變就 `save_cookie()` 回 keyring（失敗時不存，避免把匿名 session 蓋掉好 cookie）

### 同批修復的其他 bug

- **302 導向登入頁**：API 呼叫 `follow_redirects=False`，session 過期若回 302 會拋 JSONDecodeError；現在 `_raise_for_status` 將 redirect 映射為 `SessionExpiredError`
- **下載 302 靜默損壞**：`stream_download` 不跟隨 redirect，會把空 redirect body 寫入檔案還回報成功；現在 per-request `follow_redirects=True`
- **Cookie 洩漏**：cookie 原以 dict 傳入（domain-less，會送往任何 host 含外部 CDN）；現在綁定 base_url host
- **stream 錯誤訊息**：stream response 在 4xx/5xx 時先 `aread()`，否則 `.json()/.text` 拋 `ResponseNotRead`
- **mypy**：`run_async_command` 參數型別 `Awaitable` → `Coroutine`（`asyncio.run` 要求）
- **文件錯誤**：CLAUDE.md 的 cookie 優先順序與程式碼相反，已修正為 keyring 優先
- 移除 `session_probe.py` 無效的 try/except（純 re-raise）

### 測試

- 新增 `tests/unit/test_client_factory.py`（cookie 回存 3 例）
- `tests/unit/test_http.py` 追加 rotation / 302 / 下載 redirect + cookie 不洩漏 CDN 共 3 例

## 真實環境驗證結果（2026-07-17）

- Session 過期時伺服器回 **401**（實測，非 302；302 映射為額外防護）
- Session 效期為 **24 小時滑動**（cookie 第三段為到期 ms timestamp）；rotation 回存後每次使用自動延長 24h
- Rotation 回存已實測：存入 keyring 的 cookie 跑過 `whoami`/`courses list` 後自動更新為伺服器 rotate 的新值
- session cookie **非 HttpOnly**，可從瀏覽器 `document.cookie` 直接取得（過期時可用 Chrome 自動化抓新值存 keyring，免手動貼）
- `.env` 的 `TRONCLASS_SESSION_COOKIE` 已註解（靜態值不會 rotate，正是過期問題來源；現以 keyring 為主）

## 已知限制 / 未做的事

- Cookie rotation 只能「滑動延長」；session 若閒置到絕對過期仍需重新登入（`fjumcp login` 或 `--playwright` 半自動）
- 未做背景 keep-alive（YAGNI：MCP server 每次 tool call 都會用到 session，正常使用即可維持）
- `stream_download` 不追蹤 cookie rotation（下載走 CDN，不會 rotate session）

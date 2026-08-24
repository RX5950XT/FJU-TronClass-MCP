# Tasks

## 2026-08-24 WSL + keepalive

- [x] cookie_store：keyring 失敗改走 `~/.config/fju-tronclass/session`
- [x] whoami / fju_check_auth 回存 rotate 後的 cookie
- [x] `fjumcp keepalive` + `scripts/keepalive.sh`
- [x] `fjumcp login --cookie` / stdin
- [x] probe_session 改讀 API `total`
- [x] 測試 132 passed / ruff + mypy 全過

## 2026-07-17 bug 修復 + cookie 過期

- [x] 跑測試 / lint / mypy 找出現有問題
- [x] 修 mypy：`run_async_command` 型別 `Awaitable` → `Coroutine`
- [x] 修 ruff：SIM117 巢狀 with、import 排序
- [x] Cookie 過期根因：persist rotated session cookie（http 層 + 兩個 factory）
- [x] 302 導向登入頁 → `SessionExpiredError`
- [x] `stream_download` 跟隨 redirect + 錯誤時先 `aread()`
- [x] Cookie 綁定 domain，不洩漏到外部 CDN
- [x] 補測試、更新 CLAUDE.md / CONTEXT.md

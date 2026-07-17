# Tasks

## 2026-07-17 bug 修復 + cookie 過期

- [x] 跑測試 / lint / mypy 找出現有問題
- [x] 修 mypy：`run_async_command` 型別 `Awaitable` → `Coroutine`
- [x] 修 ruff：SIM117 巢狀 with、import 排序
- [x] Cookie 過期根因：persist rotated session cookie（http 層 + 兩個 factory）
- [x] 302 導向登入頁 → `SessionExpiredError`
- [x] `stream_download` 跟隨 redirect + 錯誤時先 `aread()`
- [x] Cookie 綁定 domain，不洩漏到外部 CDN
- [x] 補測試（+6 例）、更新 CLAUDE.md / CONTEXT.md

### Review

126 passed / 覆蓋率 93.77% / ruff + mypy 全過。
Cookie 過期的根因是 rotated cookie 從未存回 keyring；修在共用層（http client + factory），
CLI 與 MCP 兩條路徑都受惠。詳見 `CONTEXT.md`。

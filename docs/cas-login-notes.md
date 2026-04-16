# 如何從瀏覽器取得 TronClass Session Cookie

本文說明如何手動取得輔大 TronClass 的 `session` cookie，供 `fjumcp login --cookie` 或 `.env` 使用。

---

## 前置條件

- 已在瀏覽器登入 `https://elearn2.fju.edu.tw/`
- 使用 Chrome / Edge / Firefox（均有 DevTools）

---

## Chrome / Edge 操作步驟

1. **開啟 DevTools**：按 `F12` 或 `Ctrl+Shift+I`

2. **切換到 Application 分頁**

3. **展開 Storage → Cookies**，點選 `https://elearn2.fju.edu.tw`

4. 在右側清單找到 **Name** 欄位值為 `session` 的那一行

5. 點選該行，複製 **Value** 欄位的完整內容（格式為 `V2-xxxxxxxxxxxxxxxx...`）

   > **注意**：Value 是一串很長的 Base64 字串，完整複製，不要截斷。

---

## Firefox 操作步驟

1. 按 `F12` 開啟 DevTools

2. 切換到 **Storage 分頁**

3. 展開 **Cookies → https://elearn2.fju.edu.tw**

4. 找到 `session` 並複製 Value

---

## 貼入 fjumcp

```powershell
# 互動式：fjumcp 會提示你貼上 cookie
fjumcp login --cookie

# 或直接寫進 .env（不建議提交到版本控制）
TRONCLASS_SESSION_COOKIE=V2-xxxxxxxxxxxxxxxx...
```

---

## Cookie 有效期

TronClass session cookie 通常在以下情況失效：
- **瀏覽器登出**（點擊「登出」按鈕）
- **閒置超時**（根據學校設定，通常 2–8 小時）
- **同時登入其他裝置**（部分 LMS 只允許單一 session）

失效後執行任何 `fjumcp` 指令會看到：

```
SessionExpiredError: Session 已過期，請重新執行 fjumcp login
```

重新用瀏覽器登入並取新 cookie 即可。

---

## 安全注意事項

- **不要**將 `session` cookie 分享給他人或貼到公開場合
- **不要**將 cookie 提交到 git repository（`.env` 已在 `.gitignore` 中）
- cookie 儲存於 Windows Credential Manager（keyring），不落地明文檔案

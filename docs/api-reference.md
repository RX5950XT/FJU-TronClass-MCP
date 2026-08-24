# TronClass API 參考文件

> 本文整理已逆向驗證的輔大 TronClass API endpoints。
> Base URL：`https://elearn2.fju.edu.tw`
> 認證方式：Cookie `session=V2-...`（帶在請求 header）

---

## 認證相關

### GET /login
- 無需認證
- 會 302 重導向至 `/cas/login?service=...`（CAS SSO 流程）
- CAPTCHA 來自 `GET /cas/captcha.jpg`

### GET /api/my-courses
用途：取得目前使用者的課程清單，也作為 session probe 使用。

| 參數 | 類型 | 說明 |
|------|------|------|
| `page` | int（可選） | 分頁，預設 1 |
| `page_size` | int（可選） | 每頁筆數，預設 20 |

回應範例：
```json
{
  "list": [
    {
      "id": 12345,
      "name": "資料結構",
      "code": "CS-301",
      "semester": "113-2",
      "teacher_name": "王教授",
      "status": "active"
    }
  ]
}
```

---

## 待辦事項

### GET /api/todos
取得使用者的作業、測驗等待辦事項。

回應欄位：`id`、`title`、`course_id`、`due_date`、`is_done`、`type`

---

## 公告

### GET /api/course-bulletins
取得課程公告。

| 參數 | 類型 | 說明 |
|------|------|------|
| `course_id` | int（必填） | 課程 ID |

回應欄位：`id`、`title`、`content`、`course_id`、`created_at`

---

## 教材下載

### GET /api/uploads/{upload_id}
取得上傳檔案的 metadata。

回應欄位：`id`、`name`（原始檔名）、`size`（bytes）、`allow_download`

> 即使 `allow_download: false`，仍可取得下載 URL（見下方）。

### GET /api/uploads/{upload_id}/url
取得含 token 的暫時下載 URL。

回應範例：
```json
{
  "url": "https://media.elearn2.fju.edu.tw/file/abc123?token=xyz&expires=..."
}
```

> **注意**：URL 含有暫時 token，有效期有限（通常數分鐘至數小時）。若下載中途遇到 403，需重新呼叫此 endpoint 取得新 URL。

---

## 學習活動（影片）

### GET /api/course/{course_id}/learning-activity/{activity_id}
取得學習活動詳情。

回應欄位：`id`、`title`、`type`、`duration`（影片總時長，秒）、`completeness`（0–100）

### POST /api/course/activities-read/{activity_id}
上報影片觀看進度。

Request body：
```json
{
  "start": 0,
  "end": 90,
  "duration": 300
}
```

| 欄位 | 說明 |
|------|------|
| `start` | 本段開始秒數 |
| `end` | 本段結束秒數 |
| `duration` | 影片總時長 |
| **限制** | `end - start` **硬上限 125 秒**；建議使用 90 秒分段 |

回應欄位：`completeness`（更新後的完成度）

---

## 其他已驗證（2026-08-24）

| 功能 | 端點 |
|------|------|
| 個人檔案 | `GET /api/profile` |
| 課程詳情 | `GET /api/courses/{id}` |
| 課程大綱 | `GET /api/courses/{id}/outline` |
| 課程模組 | `GET /api/courses/{id}/modules` |
| 修課名單 | `GET /api/course/{id}/students` |
| 選課（含教師） | `GET /api/course/{id}/enrollments` |
| 分組集合 | `GET /api/courses/{id}/group-sets` |
| 作業列表 | `GET /api/courses/{id}/homework-activities` |
| 作業詳情 | `GET /api/homework-activities/{id}` |
| 活動詳情 | `GET /api/activities/{id}` |
| 討論主題 | `GET /api/activities/{id}/topics` |
| 主題詳情 | `GET /api/topics/{id}` |
| 成績組成 | `GET /api/courses/{id}/score-items` |
| 總分（常未公布） | `GET /api/course/{id}/score` |
| 考試 | `GET /api/courses/{id}/exams` |
| 課堂互動作 | `GET /api/courses/{id}/interactions` |

活動 `type`：`material` / `online_video` / `homework` / `forum` / `web_link` / `page`

**沒有、或學生權限拿不到：** inbox、calendar、notifications、逐項已公布成績、點名明細、代繳作業、掃其他組 submission。

---

## HTTP 狀態碼對應

| 狀態碼 | 意義 | SDK 行為 |
|--------|------|---------|
| 200 | 成功 | 正常回傳 pydantic 模型 |
| 401 | Session 失效 | 拋出 `SessionExpiredError` |
| 4xx | 用戶端錯誤 | 拋出 `ClientError(status_code)` |
| 5xx | 伺服器錯誤 | tenacity 重試 3 次（1s/2s/4s），之後拋出 `ServerError` |
| 網路錯誤 | — | 同上，`status_code=0` |

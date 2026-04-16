"""自訂例外：統一錯誤分類，便於 CLI / MCP 層做一致的使用者提示。"""

from __future__ import annotations


class FjuTronclassError(Exception):
    """所有自訂例外的基底類別。"""


class AuthError(FjuTronclassError):
    """認證相關錯誤（缺少 cookie、無效憑證等）。"""


class SessionExpiredError(AuthError):
    """Session 已過期，需要重新登入。"""

    def __init__(self) -> None:
        super().__init__("Session 已過期，請執行 `fjumcp login` 重新設定 cookie。")


class ClientError(FjuTronclassError):
    """4xx HTTP 錯誤（請求參數有誤、資源不存在等）。"""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"HTTP {status_code}: {message}")


class ServerError(FjuTronclassError):
    """5xx HTTP 錯誤（伺服器端問題），重試後仍失敗時拋出。"""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"伺服器錯誤 HTTP {status_code}: {message}")


class SchemaError(FjuTronclassError):
    """API 回應格式與預期 pydantic model 不符，可能是 TronClass 版本更新所致。"""

    def __init__(self, model_name: str, raw_json: object) -> None:
        self.raw_json = raw_json
        super().__init__(
            f"API 回應格式已變更，無法解析為 {model_name}。"
            " 請回報 issue 並附上 --raw 輸出。"
        )


class DownloadError(FjuTronclassError):
    """檔案下載失敗（URL 過期、磁碟空間不足等）。"""

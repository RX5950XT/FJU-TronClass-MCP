"""CLI 輸出輔助：表格或 JSON。"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console

console = Console()


def emit_json(data: Any) -> None:
    console.print(json.dumps(data, ensure_ascii=False, indent=2, default=str))

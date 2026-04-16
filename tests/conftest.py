"""pytest 全域 fixtures。"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:  # type: ignore[type-arg]
    """讀取 tests/fixtures/{name} 並回傳 dict。"""
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))  # type: ignore[return-value]


@pytest.fixture
def fake_cookie() -> str:
    return "V2-test-fake-session-cookie"


@pytest.fixture
def base_url() -> str:
    return "https://elearn2.fju.edu.tw"

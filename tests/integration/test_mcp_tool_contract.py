"""整合測試：MCP tool 合約驗證（tool 存在、schema 欄位正確）。"""

from __future__ import annotations

import pytest

from fju_tronclass.mcp_server.server import mcp


def _get_tool(name: str) -> object:
    """從 FastMCP 實例取得指定 tool 的 Tool 物件。"""
    tools = {t.name: t for t in mcp._tool_manager.list_tools()}
    assert name in tools, f"Tool '{name}' 未在 MCP server 中註冊"
    return tools[name]


class TestToolRegistration:
    """驗證所有預期的 tool 都已正確註冊。"""

    EXPECTED_TOOLS = [
        "fju_check_auth",
        "fju_list_courses",
        "fju_get_activity",
        "fju_list_todos",
        "fju_list_course_bulletins",
        "fju_get_upload_info",
        "fju_download_upload",
        "fju_mark_video_complete",
    ]

    def test_all_expected_tools_registered(self) -> None:
        registered = {t.name for t in mcp._tool_manager.list_tools()}
        for tool_name in self.EXPECTED_TOOLS:
            assert tool_name in registered, f"缺少 tool: {tool_name}"

    def test_tool_count(self) -> None:
        tools = mcp._tool_manager.list_tools()
        assert len(tools) >= len(self.EXPECTED_TOOLS)


class TestToolSchemas:
    """驗證各 tool 的 input schema 欄位正確。"""

    def _get_input_schema(self, tool_name: str) -> dict:  # type: ignore[type-arg]
        tool = _get_tool(tool_name)
        schema: dict = tool.parameters  # type: ignore[union-attr]
        return schema

    def test_fju_check_auth_has_no_required_params(self) -> None:
        schema = self._get_input_schema("fju_check_auth")
        # 無必填參數
        required = schema.get("required", [])
        assert len(required) == 0

    def test_fju_list_courses_has_optional_semester(self) -> None:
        schema = self._get_input_schema("fju_list_courses")
        props = schema.get("properties", {})
        assert "semester" in props

    def test_fju_list_todos_has_include_done_param(self) -> None:
        schema = self._get_input_schema("fju_list_todos")
        props = schema.get("properties", {})
        assert "include_done" in props

    def test_fju_list_course_bulletins_requires_course_id(self) -> None:
        schema = self._get_input_schema("fju_list_course_bulletins")
        required = schema.get("required", [])
        assert "course_id" in required

    def test_fju_list_course_bulletins_has_limit_param(self) -> None:
        schema = self._get_input_schema("fju_list_course_bulletins")
        props = schema.get("properties", {})
        assert "limit" in props

    def test_fju_get_upload_info_requires_upload_id(self) -> None:
        schema = self._get_input_schema("fju_get_upload_info")
        required = schema.get("required", [])
        assert "upload_id" in required

    def test_fju_download_upload_requires_upload_id(self) -> None:
        schema = self._get_input_schema("fju_download_upload")
        required = schema.get("required", [])
        assert "upload_id" in required

    def test_fju_download_upload_has_optional_dest_dir(self) -> None:
        schema = self._get_input_schema("fju_download_upload")
        props = schema.get("properties", {})
        assert "dest_dir" in props

    def test_fju_mark_video_complete_requires_activity_id_and_duration(self) -> None:
        schema = self._get_input_schema("fju_mark_video_complete")
        required = schema.get("required", [])
        assert "activity_id" in required
        assert "duration_seconds" in required

    def test_fju_get_activity_requires_course_id_and_activity_id(self) -> None:
        schema = self._get_input_schema("fju_get_activity")
        required = schema.get("required", [])
        assert "course_id" in required
        assert "activity_id" in required


class TestToolDescriptions:
    """驗證 tool 有適當的說明文字（docstring 會成為 tool description）。"""

    def test_all_tools_have_descriptions(self) -> None:
        for tool in mcp._tool_manager.list_tools():
            desc = tool.description or ""
            assert len(desc) > 10, f"Tool '{tool.name}' 的 description 太短或為空"

    def test_mark_video_complete_description_mentions_ethics(self) -> None:
        tool = _get_tool("fju_mark_video_complete")
        desc = (tool.description or "").lower()  # type: ignore[union-attr]
        # description 應提到學業誠信或使用者自負
        keywords = ["誠信", "風險", "使用者", "bypass", "責任"]
        assert any(kw in desc for kw in keywords), (
            f"fju_mark_video_complete 的 description 應提及學業誠信風險，實際：{tool.description}"  # type: ignore[union-attr]
        )

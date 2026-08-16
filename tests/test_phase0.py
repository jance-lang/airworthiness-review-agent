"""第 0 阶段单元测试：只测纯逻辑，不发起任何网络请求。

重点覆盖 bare_call.parse_sse_line——SSE 解析是流式调用的心脏，
各种边界（空行/坏行/思维链/usage chunk）都必须稳。
"""

from __future__ import annotations

import json

import pytest

from src.phase0.bare_call import parse_sse_line
from src.phase0.chat_cli import SYSTEM_PROMPT, new_messages
from src.phase0.config import ConfigError, Settings, load_settings, validate_key


# ---------------------------------------------------------------------------
# SSE 行解析
# ---------------------------------------------------------------------------
def sse(payload: dict | str) -> str:
    """构造一行 SSE 数据：正常 chunk 传 dict，特殊行传字符串。"""
    if isinstance(payload, str):
        return f"data: {payload}"
    return f"data: {json.dumps(payload, ensure_ascii=False)}"


class TestParseSseLine:
    def test_content_delta(self):
        chunk = {"choices": [{"delta": {"content": "适航"}}]}
        assert parse_sse_line(sse(chunk)) == ("content", "适航")

    def test_reasoning_delta(self):
        """思考模式的思维链片段要能识别（--think 演示与 CLI /think 依赖它）。"""
        chunk = {"choices": [{"delta": {"reasoning_content": "先分析问题"}}]}
        assert parse_sse_line(sse(chunk)) == ("reasoning", "先分析问题")

    def test_done_sentinel(self):
        assert parse_sse_line("data: [DONE]") == ("done", None)

    def test_blank_line(self):
        """事件之间的空行：跳过。"""
        assert parse_sse_line("") == (None, None)
        assert parse_sse_line("   ") == (None, None)

    def test_non_data_line(self):
        """注释行（SSE 规范以冒号开头）与其他杂行：跳过。"""
        assert parse_sse_line(": keep-alive") == (None, None)
        assert parse_sse_line("event: ping") == (None, None)

    def test_malformed_json_tolerated(self):
        """坏行（如网络分包导致的半截 JSON）不能让整个对话崩溃。"""
        assert parse_sse_line("data: {broken") == (None, None)

    def test_role_only_first_chunk(self):
        """流的首个 chunk 通常只带 role 无内容：跳过。"""
        chunk = {"choices": [{"delta": {"role": "assistant"}}]}
        assert parse_sse_line(sse(chunk)) == (None, None)

    def test_usage_chunk(self):
        """stream_options.include_usage 开启后，末尾 chunk 带 usage。"""
        chunk = {"choices": [],
                 "usage": {"prompt_tokens": 5, "completion_tokens": 9,
                           "total_tokens": 14}}
        kind, text = parse_sse_line(sse(chunk))
        assert kind == "usage"
        assert "5" in text and "14" in text


# ---------------------------------------------------------------------------
# 配置加载与 Key 校验
# ---------------------------------------------------------------------------
class TestValidateKey:
    def test_missing_key_raises_with_guidance(self):
        with pytest.raises(ConfigError, match="\\.env"):
            validate_key(None)

    def test_placeholder_key_raises(self):
        with pytest.raises(ConfigError, match="占位符"):
            validate_key("sk-xxxxxxxxxxxxxxxx")

    def test_valid_key_passes_through(self):
        assert validate_key("sk-abc123") == "sk-abc123"


class TestLoadSettings:
    def test_load_from_explicit_file(self, tmp_path, monkeypatch):
        for k in ("LLM_API_KEY", "LLM_BASE_URL", "MODEL_FAST", "MODEL_SMART"):
            monkeypatch.delenv(k, raising=False)
        env_file = tmp_path / ".env"
        env_file.write_text(
            "LLM_API_KEY=sk-real-key-for-test\n"
            "MODEL_FAST=deepseek-v4-flash\n",
            encoding="utf-8",
        )
        s = load_settings(env_file)
        assert s.api_key == "sk-real-key-for-test"
        assert s.model_fast == "deepseek-v4-flash"
        # 未配置项走默认值
        assert s.base_url == "https://api.deepseek.com"
        assert s.default_model == s.model_fast

    def test_settings_is_frozen_dataclass(self):
        """配置对象应当不可变，防止运行中被意外篡改。"""
        s = Settings(api_key="sk-x", base_url="https://api.deepseek.com",
                     model_fast="f", model_smart="p", default_model="f")
        with pytest.raises(AttributeError):
            s.api_key = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# CLI 机器人：messages 结构
# ---------------------------------------------------------------------------
class TestMessages:
    def test_new_messages_has_system_prompt(self):
        messages = new_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT

    def test_system_prompt_sets_role_and_norms(self):
        """角色设定必须包含：身份、条款引用要求、免责声明三要素。"""
        assert "适航工程顾问" in SYSTEM_PROMPT
        assert "CCAR-25" in SYSTEM_PROMPT          # 条款引用格式示例
        assert "不构成适航审定结论" in SYSTEM_PROMPT  # human-in-the-loop 立场

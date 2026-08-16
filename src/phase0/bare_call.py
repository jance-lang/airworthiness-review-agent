"""手写裸调用：不用任何 SDK，httpx 直接 POST DeepSeek 接口（面试素材）。

目的：彻底理解「OpenAI 兼容协议」本质上就是一个 HTTP + JSON 约定——
  请求：POST {base_url}/chat/completions，头里带 Bearer Token，体里是 JSON
  响应：非流式一次性返回 JSON；流式按 SSE（Server-Sent Events）逐行推送

运行（在项目根目录）：
    python -m src.phase0.bare_call           # 默认关闭思考模式，输出干净
    python -m src.phase0.bare_call --think   # 开启思考模式，观察思维链流式输出

阅读顺序：Part 1 非流式 → Part 2 流式（SSE 解析是核心）。
"""

from __future__ import annotations

import argparse
import json
import sys

import httpx

try:
    from .config import ConfigError, get_settings
except ImportError:  # 脚本方式直跑（python src/phase0/bare_call.py）
    from config import ConfigError, get_settings

# 适航领域的示例问题，让输出内容本身也和项目主题相关
QUESTION = "用两三句话说明：民用飞机适航审定主要在解决什么问题？"


# ---------------------------------------------------------------------------
# Part 1 非流式调用：一发一收，响应是一个完整 JSON
# ---------------------------------------------------------------------------
def chat_non_stream(think: bool = False) -> None:
    settings = get_settings()

    # —— 请求体：亲手拼 JSON。每个字段都是协议的一部分 ——
    body = {
        # 模型名决定用哪个"大脑"：flash 便宜快，pro 贵而强
        "model": settings.default_model,
        # messages 是对话的完整上下文（本轮记忆全靠它）：
        #   role=system 设定角色，user 是用户话，assistant 是模型历史回答
        "messages": [
            {"role": "system", "content": "你是一位严谨的适航工程顾问。"},
            {"role": "user", "content": QUESTION},
        ],
        # temperature 控制随机性：0 近乎确定性，2 天马行空（思考模式下不生效）
        "temperature": 0.3,
        # 思考模式 DeepSeek 默认开启；关掉更快更省，教学演示先关
        "thinking": {"type": "enabled" if think else "disabled"},
        # 非流式：等全部生成完一次性返回
        "stream": False,
    }

    print("=" * 60)
    print("【Part 1 非流式】POST /chat/completions（stream=false）")
    print("=" * 60)
    print(f"请求体（截取）：model={body['model']}, stream={body['stream']}, "
          f"thinking={'开' if think else '关'}\n")

    # —— 请求头：认证就是最普通的 HTTP Bearer Token，没有任何魔法 ——
    headers = {
        "Authorization": f"Bearer {settings.api_key}",
        "Content-Type": "application/json",
    }

    resp = httpx.post(
        f"{settings.base_url}/chat/completions",
        headers=headers,
        json=body,
        timeout=httpx.Timeout(60.0),
    )

    if resp.status_code == 401:
        raise ConfigError("HTTP 401：API Key 无效或已过期，请检查 .env 中的 LLM_API_KEY")
    resp.raise_for_status()

    # —— 响应体：一个 JSON，五个层级各司其职 ——
    data = resp.json()
    message = data["choices"][0]["message"]

    print(f"id            : {data['id']}")            # 本次请求的唯一标识
    print(f"model         : {data['model']}")         # 实际服务的模型版本
    print(f"finish_reason : {data['choices'][0]['finish_reason']}")
    #   stop=正常结束 / length=被 max_tokens 截断 / content_filter=被安全策略拦截
    if message.get("reasoning_content"):              # 思考模式才有：思维链
        print(f"reasoning     : {message['reasoning_content'][:120]}...")
    print("-" * 60)
    print("content       :")
    print(message["content"])
    print("-" * 60)
    u = data["usage"]
    print(f"usage         : 输入 {u['prompt_tokens']} tokens + "
          f"输出 {u['completion_tokens']} tokens = {u['total_tokens']} tokens")
    print("（计费按 token；flash 约 1 元/百万输入 token 量级，此对话不到 1 分钱）\n")


# ---------------------------------------------------------------------------
# SSE 解析：流式调用的核心。抽成纯函数，不碰网络，方便单元测试
# ---------------------------------------------------------------------------
def parse_sse_line(line: str) -> tuple[str | None, str | None]:
    """解析 SSE 流中的一行，返回 (事件类型, 内容)。

    SSE 协议要点：服务端把每条 JSON 消息包进 "data: ..." 行推送，
    事件之间用空行分隔，最后以 "data: [DONE]" 哨兵行收尾。

    返回值：
        ("content",   文本)  正式回答的一个片段（增量，需自行拼接）
        ("reasoning", 文本)  思考模式的思维链片段（在正式回答之前推送）
        ("usage",     文本)  最后一个 chunk 里的 token 统计（需开启开关）
        ("done",      None)  流结束
        (None,        None)  空行/注释行/无有效载荷的行，直接跳过
    """
    line = line.strip()
    if not line:
        return None, None                      # 事件分隔空行
    if not line.startswith("data:"):
        return None, None                      # 注释行（": keep-alive"）等
    payload = line[len("data:"):].strip()
    if payload == "[DONE]":
        return "done", None                    # 流结束哨兵
    try:
        chunk = json.loads(payload)
    except json.JSONDecodeError:
        return None, None                      # 半截 JSON 等坏行，容错跳过
    choices = chunk.get("choices") or [{}]     # usage chunk 的 choices 为空
    delta = choices[0].get("delta", {})
    if delta.get("reasoning_content"):
        return "reasoning", delta["reasoning_content"]
    if delta.get("content"):
        return "content", delta["content"]
    if chunk.get("usage"):
        u = chunk["usage"]
        return "usage", f"输入 {u['prompt_tokens']} + 输出 {u['completion_tokens']} = {u['total_tokens']} tokens"
    return None, None                          # 首 chunk 只带 role，无内容


# ---------------------------------------------------------------------------
# Part 2 流式调用：逐行读 SSE，边生成边打印
# ---------------------------------------------------------------------------
def chat_stream(think: bool = False) -> None:
    settings = get_settings()

    body = {
        "model": settings.default_model,
        "messages": [{"role": "user", "content": QUESTION + "（这次用流式输出）"}],
        "thinking": {"type": "enabled" if think else "disabled"},
        "stream": True,
        # 协议细节：默认流式响应不带 usage 统计，开这个开关最后一个 chunk 才会带
        "stream_options": {"include_usage": True},
    }

    print("=" * 60)
    print("【Part 2 流式】POST /chat/completions（stream=true, SSE）")
    print("=" * 60)
    if think:
        print("（思考模式已开：先流出灰色思维链，再流出正式回答）")

    full_content = []      # 增量片段要自己拼接成完整回答——SDK 帮你省掉的就是这类活
    with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
        # stream=True 后 httpx 不一次性读 body，改为按块拉取网络数据
        with client.stream(
            "POST",
            f"{settings.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.api_key}"},
            json=body,
        ) as resp:
            resp.raise_for_status()
            # iter_lines() 按行切字节流（SSE 是文本行协议），
            # 每来一个 chunk 就能处理，这就是"打字机效果"的来源
            for line in resp.iter_lines():
                kind, text = parse_sse_line(line)
                if kind == "content":
                    print(text, end="", flush=True)   # flush 让终端实时上屏
                    full_content.append(text)
                elif kind == "reasoning":
                    print(f"\033[2m{text}\033[0m", end="", flush=True)  # 暗色=思维链
                elif kind == "usage":
                    print(f"\n\nusage: {text}")
                elif kind == "done":
                    break                             # 服务端说完了，主动收工

    print(f"\n（客户端拼接了 {len(full_content)} 个增量片段，"
          f"共 {sum(len(s) for s in full_content)} 字符）\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="手写裸调用 DeepSeek 接口")
    parser.add_argument("--think", action="store_true",
                        help="开启思考模式，观察 reasoning_content 流式输出")
    args = parser.parse_args()

    try:
        chat_non_stream(think=args.think)
        chat_stream(think=args.think)
    except ConfigError as e:
        print(f"\n[配置错误] {e}", file=sys.stderr)
        sys.exit(1)
    except httpx.ConnectError:
        print("\n[网络错误] 连不上 API。若本机有代理干扰，"
              "在 .env 加一行：NO_PROXY=api.deepseek.com", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

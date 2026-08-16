"""SDK 重写：用 openai SDK 完成与 bare_call.py 完全相同的两次调用。

核心认知：openai SDK 只是「OpenAI 兼容协议」的 HTTP 客户端（一根数据线）。
base_url 指向 api.deepseek.com 后，它和 OpenAI 公司零关系——
DeepSeek/GLM/Kimi 官方均推荐用这套 SDK 接入。

对比裸调用，SDK 帮你省掉的活：
  1. 手拼请求 JSON、手写 Authorization 头
  2. 手动解析 SSE 行（chunk 对象直接给你 delta.content 属性）
  3. 自动重试、连接池管理、类型提示（IDE 能补全字段）

运行（在项目根目录）：
    python -m src.phase0.sdk_call
    python -m src.phase0.sdk_call --think
"""

from __future__ import annotations

import argparse
import sys

from openai import APIConnectionError, OpenAI

try:
    from .config import ConfigError, get_settings
except ImportError:  # 脚本方式直跑
    from config import ConfigError, get_settings

QUESTION = "用两三句话说明：民用飞机适航审定主要在解决什么问题？"


def make_client() -> OpenAI:
    """SDK 客户端：api_key + base_url 两个字段完成全部接入配置。"""
    s = get_settings()
    return OpenAI(api_key=s.api_key, base_url=s.base_url)


def chat_non_stream(client: OpenAI, think: bool = False) -> None:
    print("=" * 60)
    print("【Part 1 非流式】client.chat.completions.create(stream=False)")
    print("=" * 60)

    resp = client.chat.completions.create(
        model=get_settings().default_model,
        messages=[
            {"role": "system", "content": "你是一位严谨的适航工程顾问。"},
            {"role": "user", "content": QUESTION},
        ],
        temperature=0.3,
        stream=False,
        # thinking 是 DeepSeek 私有参数，不在 OpenAI 标准签名里，
        # SDK 约定用 extra_body 透传——这是兼容协议的通用逃生门
        extra_body={"thinking": {"type": "enabled" if think else "disabled"}},
    )

    # 属性访问替代字典取值：SDK 把 JSON 反序列化成了对象
    print(f"model         : {resp.model}")
    print(f"finish_reason : {resp.choices[0].finish_reason}")
    if getattr(resp.choices[0].message, "reasoning_content", None):
        print(f"reasoning     : {resp.choices[0].message.reasoning_content[:120]}...")
    print("-" * 60)
    print("content       :")
    print(resp.choices[0].message.content)
    print("-" * 60)
    print(f"usage         : 输入 {resp.usage.prompt_tokens} tokens + "
          f"输出 {resp.usage.completion_tokens} tokens\n")


def chat_stream(client: OpenAI, think: bool = False) -> None:
    print("=" * 60)
    print("【Part 2 流式】client.chat.completions.create(stream=True)")
    print("=" * 60)

    stream = client.chat.completions.create(
        model=get_settings().default_model,
        messages=[{"role": "user", "content": QUESTION + "（这次用流式输出）"}],
        stream=True,
        extra_body={"thinking": {"type": "enabled" if think else "disabled"}},
    )

    n_chunks = 0
    # SDK 返回的是迭代器，SSE 解析已在底层完成：
    # 裸调用里的 parse_sse_line / [DONE] 判断 / data: 前缀，这里统统不存在
    for chunk in stream:
        if not chunk.choices:          # 最后的 usage chunk
            continue
        delta = chunk.choices[0].delta
        if getattr(delta, "reasoning_content", None):
            print(f"\033[2m{delta.reasoning_content}\033[0m", end="", flush=True)
        if delta.content:
            print(delta.content, end="", flush=True)
            n_chunks += 1
    print(f"\n（收到 {n_chunks} 个内容增量片段；SSE 协议细节全部被 SDK 屏蔽）\n")


def print_comparison() -> None:
    print("=" * 60)
    print("【总结】裸调用 vs SDK")
    print("=" * 60)
    print("""
  裸调用(bare_call.py)            SDK(sdk_call.py)
  ----------------------------    ----------------------------
  手拼 body JSON / 手写 Bearer 头   构造参数即成
  手动 iter_lines + 解析 SSE        for chunk in stream 直接拿对象
  字典取值 data['choices'][0]      属性访问 resp.choices[0]
  手动处理重试/超时                 内建重试与连接池
  看得见协议每一个字节              协议被封装（所以先学裸调用再看 SDK）

  结论：SDK = 协议客户端，与 OpenAI 公司无关；理解协议后，SDK 只是省力工具。
  后续项目代码统一用 SDK；裸调用的经验用于排查协议层问题（面试加分项）。
""")


def main() -> None:
    parser = argparse.ArgumentParser(description="openai SDK 调用 DeepSeek")
    parser.add_argument("--think", action="store_true", help="开启思考模式")
    args = parser.parse_args()

    try:
        client = make_client()
        chat_non_stream(client, think=args.think)
        chat_stream(client, think=args.think)
        print_comparison()
    except ConfigError as e:
        print(f"\n[配置错误] {e}", file=sys.stderr)
        sys.exit(1)
    except APIConnectionError:
        print("\n[网络错误] 连不上 API。若本机有代理干扰，"
              "在 .env 加一行：NO_PROXY=api.deepseek.com", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

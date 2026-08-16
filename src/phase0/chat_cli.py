"""命令行问答机器人：多轮对话 + 「适航工程顾问」角色（Week 2 核心交付）。

多轮对话的原理（本项目第 0 阶段最重要的概念）：
  API 本身无状态——模型不记得上一轮说过什么。
  "记忆"完全是客户端实现的：把历史一问一答不断追加进 messages 列表，
  每次请求都把完整历史发过去。/history 命令可以随时查看这个列表。

命令：
    /help      帮助          /new      重开对话（清空历史）
    /temp 0.7  调温度        /think    切换思考模式（默认关）
    /history   查看 messages 结构（教学用）
    /exit      退出（Ctrl+C/Ctrl+D 同效）

运行（在项目根目录）：
    python -m src.phase0.chat_cli
"""

from __future__ import annotations

import sys

from openai import APIConnectionError, APITimeoutError, AuthenticationError, OpenAI

try:
    from .config import ConfigError, get_settings
except ImportError:  # 脚本方式直跑
    from config import ConfigError, get_settings

# 角色设定：system 消息是给模型的"岗位说明书"，贯穿整个对话
SYSTEM_PROMPT = """\
你是一位资深的适航工程顾问，长期从事运输类与正常类飞机的型号审定工作。

回答规范：
1. 术语使用行业标准表述（如型号合格审定 TC、符合性验证方法 MC0-MC9）；
2. 涉及规章要求时，尽量标注条款出处，格式如 CCAR-25.813(b) 或 FAR 25.981；
3. 不确定的内容如实说明，不要编造条款号；
4. 回答简洁、结构清晰，先结论后展开。

注意：你的回答是工程参考信息，不构成适航审定结论。\
"""

HELP_TEXT = """\
命令列表：
  /help        显示本帮助
  /new         重开对话（清空历史，system 角色保留）
  /temp <0-2>  设置温度（0 确定性 ←→ 2 发散；思考模式下不生效）
  /think       切换思考模式（开：先输出灰色思维链，更慢更贵但更强）
  /history     查看当前 messages 列表——多轮对话的"记忆"本体
  /exit        退出"""


def new_messages() -> list[dict]:
    """新对话的 messages：只有一条 system 设定。"""
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def print_history(messages: list[dict]) -> None:
    """打印 messages 结构。教学用：看清"多轮记忆"就是这串列表本身。"""
    print(f"\nmessages（{len(messages)} 条）——每次请求都会完整发送这个列表：")
    for i, m in enumerate(messages):
        content = m["content"]
        preview = content if len(content) <= 72 else content[:69] + "..."
        print(f"  [{i}] {m['role']:<9} | {preview}")
    print()


def stream_reply(client: OpenAI, model: str, messages: list[dict],
                 temperature: float, think: bool) -> str:
    """发起一次流式请求，终端实时打印，返回完整回答文本。

    追加 assistant 消息的活由调用方做——本函数只负责"问一次"。
    """
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
        extra_body={"thinking": {"type": "enabled" if think else "disabled"}},
    )
    pieces: list[str] = []
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if getattr(delta, "reasoning_content", None):   # 思考模式的思维链
            print(f"\033[2m{delta.reasoning_content}\033[0m", end="", flush=True)
        if delta.content:
            print(delta.content, end="", flush=True)
            pieces.append(delta.content)
    print()  # 回答结束换行
    return "".join(pieces)


def main() -> None:
    try:  # Windows 部分终端默认 GBK，强制 UTF-8 防止中文/emoji 乱码
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    try:
        settings = get_settings()
    except ConfigError as e:
        print(f"[配置错误] {e}", file=sys.stderr)
        sys.exit(1)
    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)

    messages = new_messages()
    temperature = 0.3
    think = False

    print("=" * 60)
    print("适航工程顾问 · 命令行机器人（输入 /help 查看命令）")
    print(f"模型 {settings.default_model} | 温度 {temperature} | 思考模式 关")
    print("回答仅供工程参考，不构成适航审定结论。")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n你 > ").strip()
        except (EOFError, KeyboardInterrupt):  # Ctrl+D / Ctrl+C：退出
            print("\n再见！")
            break

        if not user_input:
            continue

        # —— 命令分发 ——
        if user_input == "/exit":
            print("再见！")
            break
        if user_input == "/help":
            print(HELP_TEXT)
            continue
        if user_input == "/new":
            messages = new_messages()
            print("（已重开对话，历史清空）")
            continue
        if user_input == "/history":
            print_history(messages)
            continue
        if user_input == "/think":
            think = not think
            note = "（注意：思考模式下温度设置不生效）" if think else ""
            print(f"（思考模式已{'开' if think else '关'}）{note}")
            continue
        if user_input.startswith("/temp"):
            parts = user_input.split()
            if len(parts) == 2:
                try:
                    t = float(parts[1])
                    if 0.0 <= t <= 2.0:
                        temperature = t
                        print(f"（温度已设为 {t}）")
                    else:
                        print("（温度范围 0 ~ 2）")
                except ValueError:
                    print("（用法：/temp 0.7）")
            else:
                print("（用法：/temp 0.7）")
            continue
        if user_input.startswith("/"):
            print(f"（未知命令 {user_input}，/help 查看命令列表）")
            continue

        # —— 正常对话：先记录用户消息，再流式生成，最后把回答也记进历史 ——
        messages.append({"role": "user", "content": user_input})
        print("\n顾问 > ", end="", flush=True)
        try:
            reply = stream_reply(client, settings.default_model,
                                 messages, temperature, think)
        except AuthenticationError:
            print("\n[错误] HTTP 401：API Key 无效，请检查 .env 中的 LLM_API_KEY",
                  file=sys.stderr)
            messages.pop()  # 本轮失败，把刚追加的 user 消息回滚，保持历史干净
            continue
        except APITimeoutError:
            print("\n[错误] 请求超时，请稍后重试", file=sys.stderr)
            messages.pop()
            continue
        except APIConnectionError:
            print("\n[网络错误] 连不上 API。若本机有代理干扰，"
                  "在 .env 加一行：NO_PROXY=api.deepseek.com", file=sys.stderr)
            messages.pop()
            continue
        except KeyboardInterrupt:  # 生成中 Ctrl+C：放弃本轮，不退出程序
            print("\n（已打断本轮回答，历史保持到上一轮完整状态）")
            messages.pop()
            continue

        if reply:
            # 多轮对话的关键一步：把模型回答追加进 messages，
            # 下一轮请求它作为上下文发回去——这就是"模型记得你"的全部秘密
            messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()

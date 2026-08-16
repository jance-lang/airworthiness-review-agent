"""Prompt 实验：同一个适航问题 × 三种问法，对比回答差异（Week 2 任务）。

实验设计（固定变量，只改问法）：
  同一模型、同一温度(0.7，让随机性可见)、思考模式关闭、无 system 设定。
  A 直白问法     —— 最常见的偷懒问法
  B 角色+背景    —— 给模型"你是谁、我在什么处境"的上下文
  C 结构化指令   —— 明确输出结构（分几步、每步要什么）

运行（在项目根目录）：
    python -m src.phase0.prompt_lab            # 每种问法各跑 1 次
    python -m src.phase0.prompt_lab --repeat 2 # 各跑 2 次，观察温度带来的随机性

结果自动存到 notebooks/results/，观察结论请手工补进
notebooks/prompt_experiment.md（模板已备好）。
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from openai import OpenAI

try:
    from .config import ConfigError, get_settings
except ImportError:  # 脚本方式直跑
    from config import ConfigError, get_settings

QUESTION_VARIANTS: list[dict[str, str]] = [
    {
        "key": "A",
        "title": "直白问法",
        "prompt": "什么是 MC0-MC9？",
    },
    {
        "key": "B",
        "title": "角色 + 背景",
        "prompt": (
            "我是刚加入运输类飞机型号审定团队的助理工程师，"
            "下周要向主任工程师汇报符合性验证方法的选择思路。"
            "请为我讲解 MC0-MC9 符合性验证方法。"
        ),
    },
    {
        "key": "C",
        "title": "结构化指令",
        "prompt": (
            "请分三步介绍 MC0-MC9 符合性验证方法：\n"
            "1) 用一句话概括它们是什么；\n"
            "2) 按「描述类 / 分析计算类 / 试验类 / 检查类」分组列出全部方法；\n"
            "3) 举例说明运输类飞机审定中最常用的三种，并说明选择理由。"
        ),
    },
]


def ask_once(client: OpenAI, model: str, prompt: str, temperature: float) -> str:
    """非流式问一次，返回完整回答。思考模式关闭，保证 temperature 真正生效。"""
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        stream=False,
        extra_body={"thinking": {"type": "disabled"}},
    )
    return resp.choices[0].message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt 三种问法对比实验")
    parser.add_argument("--repeat", type=int, default=1,
                        help="每种问法重复次数（默认 1；2 可观察随机性）")
    parser.add_argument("--temp", type=float, default=0.7,
                        help="温度（默认 0.7）")
    args = parser.parse_args()

    try:
        settings = get_settings()
    except ConfigError as e:
        print(f"[配置错误] {e}")
        raise SystemExit(1)
    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)

    results_dir = Path(__file__).resolve().parents[2] / "notebooks" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / f"prompt_lab_{datetime.now():%Y%m%d_%H%M}.md"

    lines = [
        "# Prompt 实验记录（自动生成）",
        "",
        f"- 时间：{datetime.now():%Y-%m-%d %H:%M}",
        f"- 模型：{settings.default_model} | 温度：{args.temp} | 思考模式：关",
        f"- 每种问法重复 {args.repeat} 次",
        "",
        "> 观察对比三种回答的：准确性、结构、深度、可用性；",
        "> 结论补写在 notebooks/prompt_experiment.md。",
        "",
    ]

    for variant in QUESTION_VARIANTS:
        header = f"## {variant['key']}. {variant['title']}"
        print(f"\n{'=' * 60}\n{header}\n{'=' * 60}")
        print(f"问法：{variant['prompt'][:60]}...")
        lines += [header, "", f"**问法**：{variant['prompt']}", ""]

        for i in range(1, args.repeat + 1):
            answer = ask_once(client, settings.default_model,
                              variant["prompt"], args.temp)
            label = f"### 第 {i} 次回答" if args.repeat > 1 else "### 回答"
            print(f"\n--- {label}（前 200 字）---")
            print(answer[:200] + ("..." if len(answer) > 200 else ""))
            lines += [label, "", answer, ""]

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n{'=' * 60}")
    print(f"完整结果已保存：{out_path}")
    print("下一步：打开对比三个回答，把观察结论写进 notebooks/prompt_experiment.md")


if __name__ == "__main__":
    main()

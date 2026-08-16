"""统一配置入口：从项目根目录的 .env 读取密钥与模型配置。

为什么需要它：
- 密钥绝不硬编码在代码里（会随 git 泄漏），统一放 .env（已被 .gitignore 排除）
- 所有脚本共用一份配置，换模型/换 Key 只改 .env，代码零改动

用法（两种运行方式都支持）：
    python -m src.phase0.chat_cli     # 包方式运行（推荐，在项目根目录执行）
    python src/phase0/chat_cli.py     # 脚本方式直跑
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# 项目根目录 = 本文件向上两级（src/phase0/config.py → 项目根）
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigError(RuntimeError):
    """配置缺失或格式错误，携带给用户看的修复指引。"""


@dataclass(frozen=True)
class Settings:
    """全局配置。后续阶段加配置项时在此扩展。"""

    api_key: str
    base_url: str
    model_fast: str    # 轻任务：便宜、快
    model_smart: str   # 重推理：贵、聪明
    default_model: str # 第 0 阶段默认用 flash


def validate_key(key: str | None) -> str:
    """校验 API Key，不合法时抛 ConfigError（带修复指引）。

    抽成纯函数是为了能脱离环境变量做单元测试。
    """
    if not key:
        raise ConfigError(
            "未找到 LLM_API_KEY。请先复制配置模板并填入真实 Key：\n"
            "    cp .env.example .env   然后编辑 .env 中的 LLM_API_KEY=sk-...\n"
            "（DeepSeek Key 在 https://platform.deepseek.com 创建）"
        )
    if key.startswith("sk-xxx"):
        raise ConfigError(
            "LLM_API_KEY 还是占位符 sk-xxx，请编辑 .env 填入真实 Key。"
        )
    return key


def load_settings(env_file: str | Path | None = None) -> Settings:
    """加载 .env 并返回 Settings。

    显式指定 .env 路径（而不是依赖当前工作目录），保证从任何位置
    运行脚本都能找到配置——这是 dotenv 新手最常见的坑。
    """
    load_dotenv(env_file if env_file is not None else PROJECT_ROOT / ".env")
    return Settings(
        api_key=validate_key(os.environ.get("LLM_API_KEY")),
        base_url=os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/"),
        model_fast=os.environ.get("MODEL_FAST", "deepseek-v4-flash"),
        model_smart=os.environ.get("MODEL_SMART", "deepseek-v4-pro"),
        default_model=os.environ.get("MODEL_FAST", "deepseek-v4-flash"),
    )


@lru_cache(maxsize=1)  # 进程内只加载一次
def get_settings() -> Settings:
    return load_settings()

"""第 0 阶段：LLM API 入门（ROADMAP Week 1-2）

模块导航（建议按此顺序阅读）：
- config.py     统一配置入口：.env 加载、密钥校验
- bare_call.py  手写裸调用：httpx 直接 POST，自己拼 JSON、解析 SSE 流式响应
- sdk_call.py   用 openai SDK 重写同一对调用，对照体会「SDK 只是协议客户端」
- chat_cli.py   命令行多轮问答机器人（适航工程顾问）
- prompt_lab.py Prompt 实验：同一问题 3 种问法对比
"""

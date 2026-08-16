# Airworthiness Review Agent — 适航审查智能体

> 面向适航审定与符合性审查工作的多用户 LLM Agent 系统。
> 多规章智能问答 · 中美欧条款对比 · 符合性矩阵（MC0–MC9）辅助生成。

## 这是什么

**一句话作用**：把适航工程师从翻规章、对规章、编矩阵的重复文档劳动中解放出来的 AI 助手。

审定工作的日常是：翻几百万字规章、逐条判断适用性、为每条选择符合性验证方法（MC0–MC9）、编制符合性矩阵——**文档密集、规则驱动、依赖人工经验**，正是 Agent 技术的最佳落地场景。本项目回答一个核心问题：**AI 如何辅助（而不是替代）适航工程师的符合性审查工作？**

**它替工程师干三件事：**

| # | 功能 | 替代的重复劳动 |
|---|------|--------------|
| 1 | **查规章**：自然语言问答，返回带条款号的回答，可点开条款原文核对 | 人肉在几百页 PDF 里翻条款 |
| 2 | **对规章**：一句指令完成 CCAR / FAR / CS 同条号三方对比 | 三份文档开着来回人工比对 |
| 3 | **编矩阵**：输入航空器产品描述，自动初筛适用条款 + 逐条建议验证方法，工程师确认后一键导出符合性矩阵（Excel/Markdown） | 以周计的符合性矩阵手工编制 |

## 系统架构

```
[Vue 3 SPA] ──HTTP/SSE──→ [FastAPI] ──→ [awra 引擎包] ──→ SQLite(FTS5 + sqlite-vec)
 Element Plus                REST+SSE      │                      ──→ DeepSeek API(v4-flash/v4-pro)
 ECharts                                   │                      ──→ bge-m3 / bge-reranker
                                           │
[MCP Server] ←──── 第二个壳 ──────────────┘
```

**Vue（给人用）、FastAPI（给系统用）、MCP Server（给任意 AI 客户端用）三个壳共用一个 `awra` 引擎包**——所有 AI 逻辑与界面无关。

### 引擎四层

```
┌───────────────────────────────────────────────────────────┐
│ L3 Agent 分析引擎（LangGraph）                               │
│ 模型路由 · 意图识别四路路由 · 计划生成 · Text-to-SQL          │
│ SQL安全校验 · 失败自纠错重试 · 结果压缩 · 数据解读            │
│ 推荐追问 · 会话归档 · 步骤追踪 · Markdown报告                │
│ ┗ 符合性矩阵工作流：适用性初筛 → MOC建议 → 人工确认 → 导出    │
├───────────────────────────────────────────────────────────┤
│ L2 适航知识工具（Function Calling + MCP）                    │
│ reg_lookup 精确取条款 · reg_search 语义检索                  │
│ reg_diff 中美欧对比 · moc_suggest MC0–MC9建议               │
├───────────────────────────────────────────────────────────┤
│ L1.5 知识库管理（上传→解析→切分→向量化→SQL入库，增量/删除）    │
├───────────────────────────────────────────────────────────┤
│ L1 多规章 RAG（CCAR/FAR/CS）                                │
│ 条款级切分 · BM25+向量混合检索 · RRF融合 · 重排 · 引用溯源    │
└───────────────────────────────────────────────────────────┘
```

## 核心创新点

1. **流程创新**：将「适用性筛选 → MOC 建议 → 工程师确认 → 矩阵生成」全流程建模为 LangGraph 多 Agent 工作流，MOC 建议锚定 AP-21 审定程序知识库而非 LLM 自由发挥——领域方法论 × Agent 编排，国内无公开实现
2. **数据创新**：利用 CCAR-25 与 FAR Part 25 条号天然对齐特性，构建条号对齐的多语种规章知识库，实现同条号中美欧三方对比（reg_diff）
3. **架构创新**：确定性工具（reg_lookup 零幻觉取原文）与生成式回答分离 + 条款号级引用溯源 + 检索不到即拒答，human-in-the-loop 为设计立场（与 EASA AI Roadmap 可审计方向一致）
4. **评测创新**：自建 40-50 条中英混合、带条款号标准答案的适航 RAG 评测集，可发布为社区 mini-benchmark

## 技术栈（选型理由见 docs/DESIGN.md，随第 3 阶段补充）

- **后端**：Python · FastAPI · LangGraph · SQLite(FTS5 + sqlite-vec) · sqlglot · pydantic
- **LLM**：DeepSeek（轻任务 `deepseek-v4-flash` / 重推理 `deepseek-v4-pro`，OpenAI 兼容协议接入）；Embedding 用 bge-m3（本地）+ bge-reranker-v2-m3
- **前端**：Vue 3（Composition API）· Vite · Element Plus · ECharts · Pinia · Axios/fetch 流式（SSE）
- **多用户**：JWT 鉴权 + RBAC（admin 管理全局知识库与用户 / user 使用与产出），数据按 user_id 隔离（多租户 RAG）

## 快速开始

```bash
# 1. 创建虚拟环境（Windows Git Bash）
python -m venv .venv
source .venv/Scripts/activate

# 2. 安装当前阶段依赖
pip install -r requirements.txt

# 3. 配置密钥
cp .env.example .env   # 编辑 .env，填入你的 DeepSeek API Key
```

代码随开发阶段逐步落地，当前进度与下一步见 [ROADMAP.md](./ROADMAP.md)。

## 项目结构（目录已建，代码按阶段填充）

```
├── data/
│   ├── raw/         # 原始规章文档（gitignore，不上传）
│   ├── processed/   # 条款级切分结果（劳动成果，可上传）
│   └── eval/        # 评测问题集
├── scripts/         # 规章下载、条款切分（第1阶段）
├── src/
│   ├── phase0/      # 第0阶段：LLM API 入门
│   ├── rag/         # 第1阶段：多规章 RAG + 知识库管理
│   ├── tools/       # 第2阶段：适航知识工具 + MCP Server
│   └── agents/      # 第3阶段：Agent 引擎（LangGraph）
├── backend/         # 第3阶段：FastAPI 服务层
├── frontend/        # 第3阶段：Vue 3 前端
├── tests/           # 单元测试
├── notebooks/       # 实验记录（也是博客素材）
├── ROADMAP.md       # 14 周开发路线图
├── RESOURCES.md     # 学习资源 + 适航领域资料
└── data/README.md   # 数据源清单与获取方式
```

## 声明

本项目仅用于学习与求职作品展示。**所有输出均为辅助建议，不构成适航审定结论**；符合性矩阵的最终确认始终由持证工程师完成（human-in-the-loop 是本项目的设计立场）。语料仅使用官方公开规章与程序文件（CCAR / FAR / CS / AP / AC），不含受版权保护的书籍内容。

# 学习资源清单

> 原则：每个阶段只看该阶段列出的内容，看不完收藏即可。标注 🆓 为免费资源。

## 第 0 阶段：Python / Git / LLM API

- 🆓 [Datawhale hello-agents《从零开始构建智能体》](https://github.com/datawhalechina/hello-agents) — 中文系统教程，贯穿全程的主教材
- 🆓 [DeepSeek API 文档（中文）](https://api-docs.deepseek.com/zh-cn/) — 第 0 阶段唯一必读；[模型与定价](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)（现役：deepseek-v4-flash / v4 / v4-pro）
- 🆓 [httpx 文档](https://www.python-httpx.org/) — 手写裸调用用
- 🆓 [Git 猴子都能懂的教程（中文）](https://backlog.com/git-tutorial/cn/) — 交互式，学到「分支」即可
- 🆓 [Python3 菜鸟教程](https://www.runoob.com/python3/python3-tutorial.html) — 当字典查，别通读

## 第 1 阶段：RAG / 检索 / SQLite

- 🆓 [bge-m3 模型页](https://huggingface.co/BAAI/bge-m3) — 多语言 Embedding，中文问题可查英文条款；[bge-reranker-v2-m3](https://huggingface.co/BAAI/bge-reranker-v2-m3)
- 🆓 [sqlite-vec 官方仓库](https://github.com/asg017/sqlite-vec) — SQLite 向量扩展；[FTS5 全文检索文档](https://www.sqlite.org/fts5.html)（内置 BM25）
- 🆓 [jieba 中文分词](https://github.com/fxsjy/jieba)
- 🆓 [BM25 算法讲解（Elastic 博客）](https://www.elastic.co/cn/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)
- 🆓 [RRF 融合算法（论文，2 页）](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- 🆓 [RAGAS 评估框架](https://docs.ragas.io/) — 参考指标定义，评测脚本建议手写（面试讲得清）
- 进阶视野：[Advanced RAG 技术综述](https://pub.towardsai.net/advanced-rag-techniques-an-overview-a4b4b0e8ac9a)

## 第 2 阶段：Tool Calling / MCP

- 🆓 [Function Calling 指南（OpenAI 兼容协议）](https://platform.openai.com/docs/guides/function-calling) — DeepSeek/GLM 均兼容此协议
- 🆓 [MCP 官方文档](https://modelcontextprotocol.io/) + [官方 Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- 🆓 [sqlglot](https://github.com/tobymao/sqlglot) — SQL 语法树解析（第 11 周安全校验用，提前了解）

## 第 3 阶段：LangGraph / FastAPI / Vue

- 🆓 [LangGraph 官方教程](https://langchain-ai.github.io/langgraph/tutorials/introduction/) — 重点：StateGraph、条件边、human-in-the-loop（interrupt）、checkpointer
- 🆓 [FastAPI 中文文档](https://fastapi.tiangolo.com/zh/) — 重点：路由、依赖注入、SSE 流式响应
- 🆓 [Vue 3 官方中文文档](https://cn.vuejs.org/) — 质量第一梯队，主教材；配套 [Vite](https://cn.vitejs.dev/)
- 🆓 [Element Plus 组件文档](https://element-plus.org/zh-CN/) — 表格/上传/表单三大组件重点看
- 🆓 [ECharts 官方](https://echarts.apache.org/zh/) + [Pinia](https://pinia.vuejs.org/zh/) + [Vue Router](https://router.vuejs.org/zh/)
- 🆓 [passlib（密码加密）](https://passlib.readthedocs.io/) — 第 13 周多用户用
- JS 速成（wk8 前 2-3 天）：现代 JavaScript 教程（javascript.info 有中文版），重点变量/函数/数组对象/async-await 与 Python 概念对照

## 适航领域资料（面试谈资 + 语料依据）

**规章与程序文件（数据源，详见 data/README.md）**

- 🆓 [CCAR-25-R4《运输类飞机适航标准》](https://xxgk.mot.gov.cn/gz/202112/t20211227_3633506.html) — 交通运输部，**有 Word 版直链**（解析质量最好）
- 🆓 [CCAR-23-R4《正常类飞机适航规定》(2022)](https://www.caac.gov.cn/XXGK/XXGK/MHGZ/202205/t20220531_213498.html) — 新性能基标准：4 审定等级 × 2 性能等级
- 🆓 [CCAR-21-R4《民用航空产品和零部件合格审定规定》](https://xxgk.mot.gov.cn/gz/202403/t20240312_4053238.html) — 审定程序母法（站点有反爬，浏览器访问）
- 🆓 [CCAR-92《民用无人驾驶航空器运行安全管理规则》(2024)](https://www.caac.gov.cn/PHONE/XXGK_17/XXGK/MHGZ/202401/t20240103_222566.html) — 无人机/低空经济热点
- 🆓 [eCFR 官网与 API](https://www.ecfr.gov/developers/documentation/api/v1) — FAR Part 23/25 程序化下载
- 🆓 [EASA CS-25 文档库](https://www.easa.europa.eu/en/document-library/certification-specifications/group/cs-25-large-aeroplanes) / [Easy Access Rules（含 XML 版）](https://www.easa.europa.eu/en/document-library/easy-access-rules/easy-access-rules-large-aeroplanes-cs-25)

**MC0–MC9 与审定流程（项目核心领域知识）**

- 🆓 [民机适航符合性方法研究](http://myfjcs.cnjournals.com/myfjsjyyj/article/html/20240201?st=search) — MC0–MC9 十种方法系统阐述
- AP-21-AA-2011-03《航空器型号合格审定程序》— MC 方法定义的官方出处，民航局官网「规范性文件」栏目手动下载
- FAA AC 21-10 — MC 体系的历史源头（CAAC 采纳自此）

**行业动态与学术（面试谈资）**

- EASA AI Roadmap 2.0 — 欧局对 AI 在设计/审定中应用的路线图，「可审计 AI」立场的行业背书
- ACM: Civil Aviation Legal Retrieval and Analysis Based on RAG — 与本项目最接近的学术工作（民航法律方向，非适航技术规章）
- AIAA 2025: RAG and In-Context Prompted LLMs in Aerospace（Southampton 预印本）
- 民航局适航审定中心（上海/西安/沈阳/广州）官网动态 — 了解业务与岗位

## 关键概念备忘（面试口径）

1. **对话模型 vs Embedding 模型**：前者文本进文本出（动脑），后者文本进向量出（编目）。RAG 两者缺一不可：Embedding 负责「找」（检索），对话模型负责「答」（生成）。DeepSeek 只提供对话模型，无 Embedding API——向量化用 bge-m3（本地免费），这是业界标准分工，不影响「全量对接 DeepSeek 对话模型」。
2. **openai SDK 的本质**：只是 OpenAI 兼容协议的 HTTP 客户端（一根数据线），base_url 指向 api.deepseek.com 后与 OpenAI 公司零关系；DeepSeek/GLM/Kimi 官方均推荐此协议接入。
3. **SSE vs WebSocket**：单向推送（LLM 流式输出、Agent 步骤推送）用 SSE——DeepSeek 官方流式返回本身就是 SSE 格式；双向实时（协同编辑、聊天室）才用 WebSocket。前端实现：EventSource 仅支持 GET，聊天为 POST，故用 fetch + ReadableStream 解析。
4. **RAG 与幻觉**：RAG 大幅降低但不能消灭幻觉，本项目叠加三层保险——强制条款引用（可回溯核对）、检索不到即拒答、reg_lookup 确定性工具（零幻觉路径）。

## 学不动时的调节

- B 站搜「LangGraph 实战」「RAG 从零实现」跟一两个视频实操换脑子
- 每读完一份资料，在 notebooks/ 写 5 行总结——三个月后就是博客素材

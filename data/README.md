# 数据目录说明

## 目录结构

```
data/
├── raw/         # 原始下载的规章文档（已被 .gitignore 排除，不上传 GitHub）
├── processed/   # 条款级切分结果 JSONL（劳动成果，可上传）
└── eval/        # 评测问题集（问题 + 标准条款号）
```

## 数据源核实结果（2026-08-16 逐一实测）

| 语料 | 版本/状态 | 获取方式 | 获取难度 |
|------|----------|---------|---------|
| **CCAR-25-R4**《运输类飞机适航标准》 | 现行有效（交通运输部令2016年第19号） | [交通运输部公开页](https://xxgk.mot.gov.cn/gz/202112/t20211227_3633506.html)，**Word + PDF 直链可下载**（优先用 Word，解析质量最好） | ⭐ 简单 |
| **CCAR-23-R4**《正常类飞机适航规定》 | 2022 发布，现行；新性能基分级（4 审定等级 × 2 性能等级） | [民航局官网全文页](https://www.caac.gov.cn/XXGK/XXGK/MHGZ/202205/t20220531_213498.html) | ⭐ 简单 |
| **CCAR-21-R4**《民用航空产品和零部件合格审定规定》 | 现行 | [交通运输部公开页](https://xxgk.mot.gov.cn/gz/202403/t20240312_4053238.html)；**站点有反爬验证码，用浏览器手动下载** | ⭐⭐ 手动 |
| **CCAR-92**《民用无人驾驶航空器运行安全管理规则》 | 2024-01-01 施行（注意：运行规章，非适航标准；无人机适航另有《限用类无人驾驶航空器系统适航标准》） | [民航局官网全文页](https://www.caac.gov.cn/PHONE/XXGK_17/XXGK/MHGZ/202401/t20240103_222566.html)，亦见[交通运输部](https://xxgk.mot.gov.cn/jigou/fgs/202401/t20240103_3980642.html) | ⭐ 简单 |
| **FAR Part 23/25**（14 CFR） | 持续更新（实测 Title 14 最新版 2026-08-05） | [eCFR 官方 API](https://www.ecfr.gov/developers/documentation/api/v1) **纯脚本自动下载，结构化 XML，最好处理** | ⭐ 自动 |
| **EASA CS-25** 大型飞机审定标准 | [EASA 文档库](https://www.easa.europa.eu/en/document-library/certification-specifications/group/cs-25-large-aeroplanes) | [Easy Access Rules 版](https://www.easa.europa.eu/en/document-library/easy-access-rules/easy-access-rules-large-aeroplanes-cs-25) **提供 XML 格式，比 PDF 好解析** | ⭐ 自动 |
| **AP-21-AA-2011-03**《航空器型号合格审定程序》 | MC0–MC9 方法定义出处 | 民航局官网「规范性文件」栏目，浏览器手动下载（同系列其他 AP 文件有 PDF 直链，脚本抓取会被验证码挡） | ⭐⭐ 手动 |
| FAA AC 咨询通告 | 公开 | rgl.faa.gov / faa.gov 官网 | 选做扩充 |

## 下载策略

- **英文自动**：FAR（eCFR API）+ EASA CS-25（XML）→ 后续由 `scripts/download_regs.py` 全自动拉取
- **中文手动**：CCAR 系列 → 脚本打印指引链接，浏览器下载后放入 `data/raw/`（总量 6-8 个文件，一次性工作）
- 中文政府站点普遍有反爬验证码，**这是正常现象不是被封**，手动下载即可

## 两个影响设计的发现（面试谈资）

1. **CCAR-23-R4 是 2022 年新性能基标准**：不再按正常/实用/特技/通勤分类，改为「4 个审定等级 × 2 个性能等级」——适用性规则表必须用新分级，说明你读的是现行规章而非旧版
2. **CCAR-25 与 FAR Part 25 条号天然对齐**（CCAR 参照 FAR 制定）：这是实现 `reg_diff` 中美欧同条号对比的结构基础

## 合规注意

- 只使用官方公开的规章与程序文件；**不要**把《飞机设计手册》、Raymer《Aircraft Design》等受版权保护的书籍内容放入语料并公开分发
- 所有语料标注来源与版本号（documents 表），保证可追溯
- CCAR-25 优先使用 Word 版而非扫描 PDF：解析质量好且无需 OCR

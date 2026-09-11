# Price Gap Map

[![Project Status](https://img.shields.io/badge/status-prototype-F59E0B?style=flat-square)](./DISCLAIMER.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](./modules/llm-price-live/sync.py)
[![License](https://img.shields.io/badge/license-MIT-111827?style=flat-square)](./LICENSE)
[![Focus](https://img.shields.io/badge/focus-evidence--based%20procurement-0F766E?style=flat-square)](./ROADMAP.md)
[![Language](https://img.shields.io/badge/docs-中文%20%2F%20English-7C3AED?style=flat-square)](./README-EN.md)

一个面向真实采购决策的价差解释型原型项目。它不试图直接回答“哪里最便宜”，而是把价格、限制条件、证据质量和风险拆开，帮助用户理解**为什么便宜、便宜了什么、还能不能买**。

当前版本适合作为 GitHub 上的公开实验项目，不应被视为已经完成的全网实时比价产品。

- 中文说明：`README.md`
- English documentation: [`README-EN.md`](./README-EN.md)

## 现在有什么

- `examples/concept-draft/`
  早期产品概念稿，说明项目的核心判断：价差往往来自信息差、规则差和履约差。
- `examples/interactive-prd/`
  可点击的交互式 PRD 原型，展示“需求输入、渠道比较、低价原因展开、偏好切换、价格追踪”等体验。
- `modules/llm-price-live/`
  零第三方依赖的公开 LLM 价格同步器。读取 `tokencanopy/price` 的公开快照，生成标准化 JSON 与离线 HTML 页面。
- `modules/retail-apple-sample/`
  标准电商商品样本。抓取 Apple 官方公开商品页中的 AirTag 单件装与四件装价格，演示“真实页面抓取 -> 标准化 -> 对比报告”的最小闭环。
- `templates/beauty-11-report-template/`
  面向双十一化妆品场景的采购报告模板。
- `data/beauty-11-estee-lauder-case.json` + `docs/beauty-11-real-case.html`
  Offer Snapshot v2 真实案例：记录官网 720 元、京东 660 元和苏宁 641.20 元线索，分级保存 2024/2025 历史证据，并明确排除规则。
- `docs/clawhub-beauty-11-min-protocol.md`
  Offer Snapshot 最小协议：区分现金到手价与赠品净值价；赠品构成未知时净值必须为 `null`。
- `skills/beauty-offer-auditor/`
  ClawHub Skill：审计化妆品大促购买方案，处理套装、赠品、历史 offer、证据等级与失败降级。已发布为 [`@bonniegeng-max/beauty-offer-auditor`](https://clawhub.ai/bonniegeng-max/skills/beauty-offer-auditor)。

## 为什么先发 GitHub

这个仓库更像一个**方向清楚、边界明确的原型合集**，而不是“拿来就能全网比价”的成熟 Skill。

它现在已经具备：

- 产品概念和交互原型
- 两条可运行的数据样本链路
- 一个强场景的采购报告模板
- 明确的口径说明与失败边界

但它还**不具备**：

- 全网实时最低价搜索
- 登录态价格与结算价自动采集
- 跨平台稳定的同款 SKU 识别
- 自动下单或交易闭环
- 对所有品类都可靠的风险判断

## 当前边界

这个项目当前只应该用于：

- 研究“价差解释型采购助手”是否成立
- 演示 HTML 原型和报告模板
- 验证公开数据的抓取、标准化和展示方式
- 验证并迭代垂直 Skill

不应该把它用于：

- 直接承诺“全网最低价”
- 替代人工核验结算页
- 对机票、酒店、化妆品等复杂场景给出无条件购买结论
- 在没有证据回链时输出确定性判断

更完整的限制说明见 [`DISCLAIMER.md`](./DISCLAIMER.md)。

## 快速浏览

- 概念稿：[`examples/concept-draft/index.html`](./examples/concept-draft/index.html)
- 交互式 PRD：[`examples/interactive-prd/index.html`](./examples/interactive-prd/index.html)
- LLM 公价样本：[`modules/llm-price-live/index.html`](./modules/llm-price-live/index.html)
- Apple 零售样本：[`modules/retail-apple-sample/report.html`](./modules/retail-apple-sample/report.html)
- 双十一化妆品模板：[`templates/beauty-11-report-template/index.html`](./templates/beauty-11-report-template/index.html)
- 雅诗兰黛 Offer Snapshot 案例：[`docs/beauty-11-real-case.html`](./docs/beauty-11-real-case.html)
- Offer Snapshot 协议：[`docs/clawhub-beauty-11-min-protocol.md`](./docs/clawhub-beauty-11-min-protocol.md)
- Beauty Offer Auditor Skill：[`skills/beauty-offer-auditor/README.md`](./skills/beauty-offer-auditor/README.md)

## 运行方式

### 1. LLM 价格样本

```bash
cd modules/llm-price-live
python3 sync.py
python3 -m unittest discover -s tests -v
```

### 2. Apple 零售样本

```bash
cd modules/retail-apple-sample
python3 sync.py
python3 -m unittest tests.test_sync
```

### 3. 双十一化妆品 Offer Snapshot

直接打开 `docs/beauty-11-real-case.html` 查看案例。校验结构化数据、公式、证据分级与排除逻辑：

```bash
python3 -m unittest discover -s tests -v
```

模板仍位于 `templates/beauty-11-report-template/index.html`。

### 4. Beauty Offer Auditor Skill

Skill 入口为 `skills/beauty-offer-auditor/SKILL.md`，通用示例位于 `skills/beauty-offer-auditor/examples/generic-case.json`。在仓库根目录运行同一测试命令即可校验 Skill 结构、公式与降级规则。该 Skill 已发布到 ClawHub：`openclaw skills install @bonniegeng-max/beauty-offer-auditor`。

## 仓库结构

```text
price-gap-map-github/
├── data/                          # Offer Snapshot 结构化案例
├── docs/                          # 协议与可视化真实案例
├── tests/                         # 协议、Skill 结构、公式与降级逻辑测试
├── skills/
│   └── beauty-offer-auditor/      # ClawHub Skill（已发布）
├── examples/                      # 概念原型与交互式 PRD
├── modules/
│   ├── llm-price-live/           # 公开 LLM 公价样本
│   └── retail-apple-sample/      # 标准电商公开页样本
├── templates/
│   └── beauty-11-report-template/# 强场景采购模板
├── CONTRIBUTING.md
├── DISCLAIMER.md
├── README-EN.md
├── ROADMAP.md
└── README.md
```

## 参与方式

欢迎把它当成一个正在生长中的原型项目来参与，而不是已经封装完成的产品。

- 提 issue：指出口径错误、风险漏项、失败场景或更好的证据结构
- 提 PR：补真实样本、完善模板、改进 README、增加失败处理
- 做案例：把某个真实采购场景整理成可复用示例

具体约定见 [`CONTRIBUTING.md`](./CONTRIBUTING.md)。

## 下一步

优先级按“能形成真实采购价值”而不是“覆盖更多网站”来排：

1. 为 Offer Snapshot 补齐带时间戳的结算页与 A 级证据
2. 十一酒店真实采购版
3. 更多标准电商 SKU 的跨渠道样本
4. 更稳的同款识别和证据编号体系
5. 继续迭代 Beauty Offer Auditor：补齐案例覆盖、跟进 ClawHub 使用反馈

详见 [`ROADMAP.md`](./ROADMAP.md)。

## 数据来源

- `modules/llm-price-live` 使用 `tokencanopy/price` 的公开价格快照。
- `modules/retail-apple-sample` 使用 Apple 官方公开商品页中的内嵌 JSON。
- 美妆案例逐条保存原始 URL、证据等级、局限与排除原因；2024/2025 历史材料不参与当前价格排名。

这些样本仅用于验证口径与产品方向，不构成采购建议的唯一依据。

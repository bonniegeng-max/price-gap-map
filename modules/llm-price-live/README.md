# price-intelligence-live

零第三方依赖的 LLM 公价格同步器与中文离线搜索比较页。它读取 `tokencanopy/price` 的公开 `prices.csv`，将价格统一为 **USD / 1,000,000 tokens**，并把同一模型、平台、变体、区域下的输入/输出价格配成一条报价。

## 运行

需要 Python 3.10+，无需安装依赖：

```bash
python3 sync.py
open index.html
```

同步器会生成：

- `data/prices.json`：标准化数据，含 UTC 检索时间、原始 URL、SHA-256、来源标识和 CSV 行号。
- `index.html`：嵌入完整快照的自包含离线页面，可直接通过 `file://` 打开、搜索和排序。

也可从本地快照重建：

```bash
python3 sync.py --input /path/to/prices.csv
```

## 标准化口径

1. 以 `author + model_name` 做 Unicode 大小写与标点归一化，跨平台关联同名模型；名称缺失时退回 `model_key`。
2. 以“规范模型 + 平台 + variant + region”为报价键；只在这些维度一致时配对 `input` / `output`。
3. 空维度写为“未标注”，缺失价格保留 `null`；不插值、不换算套餐、不推断优惠。
4. 页面展示的价差因素仅来自 CSV 中实际不同的 `variant`、`region`、上下文长度、生效日期、来源与价格完整度。它们是伴随差异，不被表述为因果。
5. 同名规则便于检索，但不能证明不同平台端点在精度、吞吐、延迟、限流或可靠性上等价；采购前应回到平台核验。

## JSON 顶层字段

- `retrieved_at`：同步器实际检索时间（UTC）。
- `source`：上游名称、CSV URL、仓库、许可、单位与文件摘要。
- `normalization`：比较键和规则。
- `stats`：原始行、跳过行、报价、模型及平台计数。
- `offers`：标准化报价；`prices_usd_per_1m_tokens` 分列输入、输出及缓存价。
- `observed_difference_factors`：按模型记录实际观察到的结构化差异。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖跨平台模型键、输入/输出配对、维度保留、坏行处理、缺列失败和离线数据嵌入。

## 数据来源与许可

数据来自 [tokencanopy/price](https://github.com/tokencanopy/price) 的公开快照，数据许可为 CC BY 4.0。上游说明这些是自动采集的公开标价，可能有误，也不含协议折扣、免费额度等；引用或采购前请向提供商复核。

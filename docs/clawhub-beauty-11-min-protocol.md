# 双十一化妆品 ClawHub 最小协议：Offer Snapshot v2

## 1. 定位

本协议把一次比价定义为一个**有时间边界的报价快照（Offer Snapshot）**，而不是长期有效的“最低价”。每个结论必须能回到某个报价、某条证据和某个排除理由。

协议只回答：当前样本中哪些报价可比、现金口径相差多少、哪些信息仍缺失、用户下一步应核验什么。它不承诺实时、全网最低或自动下单。

## 2. 核心原则

1. 报价与商品分离：同一商品可有多个渠道、多个时间点的报价。
2. 当前与历史分离：历史活动只作背景，默认不参与当前排名。
3. 现金与净值分离：先算现金到手价，再在证据充分时计算赠品净值价。
4. 未知不是零：赠品构成未知时 `gift_net_value = null`，不得写成 `0` 后宣称已计算净值。
5. 先分级再决策：证据不足的低价可保留为线索，但必须排除出推荐。
6. 历史不完整不得补写日期、券额、赠品 SKU、库存或结算价。

## 3. 最小输入

```json
{
  "product": {
    "name": "雅诗兰黛第七代小棕瓶",
    "spec": "50ml",
    "comparison_unit": "单件 50ml 正装"
  },
  "snapshot": {
    "captured_at": null,
    "currency": "CNY",
    "region": "中国大陆"
  },
  "offers": [
    {
      "channel": "品牌官网",
      "url": "https://...",
      "display_price": 720,
      "coupon": null,
      "mandatory_cost": 0,
      "gift": null
    }
  ],
  "constraints": {
    "needs_invoice": true,
    "minimum_expiry_months": 12
  }
}
```

必填：商品名称、规格、比较单位、币种、地区以及至少两个候选报价。`captured_at` 无法确认时可以为 `null`，但必须同时写明 freshness 限制，且不能声称实时。

## 4. Offer Snapshot 数据模型

### 4.1 顶层字段

- `schema_version`：当前为 `2.0`
- `model`：固定为 `offer_snapshot`
- `case_id`：稳定案例标识
- `snapshot`：采集时间、区域、币种与新鲜度
- `normalized_product`：被比较的唯一商品口径
- `formula_policy`：公式和缺失值规则
- `evidence_grade_policy`：证据等级定义
- `offers`：当前与历史报价
- `comparison`：仅由合格报价计算的价差
- `decision`：克制的决策与下一步核验
- `evidence`：证据登记表

### 4.2 单个 offer

每个报价至少包含：

```json
{
  "offer_id": "O-CURRENT-JD",
  "period": "current",
  "channel": "京东商品页",
  "product_match": "exact",
  "display_price": 660,
  "confirmed_discount": 0,
  "mandatory_cost": 0,
  "cash_landed_price": 660,
  "gift": {
    "composition_known": false,
    "gift_net_value": null,
    "reason": "赠品构成未知"
  },
  "net_effective_cost": null,
  "evidence_refs": ["E-CURRENT-JD"],
  "evidence_grade": "B",
  "price_comparison_eligible": true,
  "purchase_recommendation_eligible": false,
  "exclusion_reasons": ["缺少结算页与批次有效期"]
}
```

`period` 只允许 `current` 或 `history`。历史报价必须带 `event_year`，并默认 `price_comparison_eligible = false`。

## 5. 公式

### 5.1 现金到手价

```text
cash_landed_price = display_price - confirmed_discount + mandatory_cost
```

只计明确可用的优惠和必要成本。会员资格、跨店凑单、支付券、运费或税费不明时，不得猜测；字段保持 `null`，报价不得进入现金价比较。

### 5.2 赠品净值价

```text
net_effective_cost = cash_landed_price - gift_net_value
```

只有赠品 SKU、数量、履约条件、参考价值与折算规则全部可核验时才计算。赠品构成未知或仅有“买一送多”等宣传时：

- `gift.composition_known = false`
- `gift.gift_net_value = null`
- `net_effective_cost = null`
- 仍可在现金口径比较，但不得输出净值排名

### 5.3 价差

```text
gap_amount = reference_cash_landed_price - candidate_cash_landed_price
gap_rate = gap_amount / reference_cash_landed_price
```

价差两端必须同币种、同地区、同规格、同版本，并达到现金比较的最低证据等级。

## 6. 证据等级

- **A**：品牌或平台一手页面；身份、规格、价格、时间及关键结算条件均可复核。可支持购买推荐。
- **B**：一手页面，但时间、主体、结算条件、批次或有效期有缺口。可支持同口径价格比较，不支持无条件推荐。
- **C**：搜索片段、聚合页或可回链二手报道。只作线索，不进入排名。
- **D**：回顾性内容、用户内容或上下文明显缺失。只作历史背景。

等级只表达证据完整度，不表达商品真假。证据降级必须保留原因。

## 7. 可比与排除逻辑

`price_comparison_eligible` 只有同时满足下列条件才可为 `true`：

- `period = current`
- 商品身份与规格为 `exact`
- 证据等级达到 B
- 展示价、确认优惠、必要成本均为数值
- 现金到手价符合公式

以下任一情况必须排除：规格/版本/套装不同；跨境与国行履约口径混用；临期未单列；只有搜索片段；销售主体不明；历史活动；结算条件缺失到无法计算现金价。

`purchase_recommendation_eligible` 还要求 A 级证据，并核清库存、销售与发货主体、发票、批次、有效期和退换规则。

## 8. 决策枚举

`decision.result` 只允许：

- `建议采购`：至少一个报价达到购买推荐条件，且用户约束全部满足
- `有条件采购`：可做现金比较，但关键结算或履约字段仍需确认
- `不建议采购`：没有可比报价，或风险/约束已明确不满足

如果最低数字来自 C/D 级证据或被排除报价，`recommended_channel` 必须为 `null`。

## 9. 历史证据处理

历史记录用于说明活动形态与风险，不用于证明当前价格。每条历史记录必须保存：年份、来源、证据等级、原始主张、已知缺口和排除原因。

禁止：把 2024/2025 活动当作当前仍可领取；把 75ml/100ml 换算后冒充 50ml 同款报价；补造券额、赠品构成或结算截图；把二手报道升级为官方证据。

## 10. 最小输出

输出至少包含：商品归一、快照新鲜度、报价表、现金价差、赠品净值可用性、证据等级、排除原因、决策、下一步核验和证据回链。

推荐措辞示例：

> 当前样本中，京东现金展示口径较官网低 60 元；由于采集时间、结算页和赠品构成不完整，本结果仅为有条件采购线索，不构成实时最低价或渠道推荐。

## 11. 失败协议

- 时间未知：保留快照，freshness 标记 `unresolved`，禁止“实时/今日最低”。
- 赠品未知：净值字段保持 `null`，禁止按宣传价折算。
- 历史不完整：保留原始主张并降至 C/D，禁止补全。
- 规格不一致：`product_match = mismatch` 并排除。
- 只有线索：允许展示，但不得参与价差和推荐。
- 无 A 级证据：不得输出无条件渠道推荐。

## 12. 参考实现

真实案例数据：[`../data/beauty-11-estee-lauder-case.json`](../data/beauty-11-estee-lauder-case.json)

可视化案例：[`beauty-11-real-case.html`](./beauty-11-real-case.html)

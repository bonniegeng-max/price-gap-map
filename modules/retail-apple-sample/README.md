# price-intelligence-retail

抓取 Apple 官方公开购买页中的 AirTag 单件装与四件装价格，输出结构化 JSON 和离线 HTML 报告。

## 功能

- 抓取中国大陆、美国、英国、日本、加拿大的 Apple 官方 AirTag 公开购买页
- 解析页面内嵌的 `productSelectionData` JSON，不依赖第三方库
- 比较每个市场内“单件价 × 4”与“四件装总价”的差额和折扣率
- 生成 `data/retail_prices.json` 与 `report.html`
- 附带标准库单元测试 `tests/test_sync.py`

## 运行要求

- Python 3.10+
- 零第三方依赖

## 使用方式

在模块目录下执行：

```bash
python3 sync.py
```

默认输出：

- `data/retail_prices.json`
- `report.html`

可选参数：

```bash
python3 sync.py --timeout 30 --output data/retail_prices.json --html report.html --template template.html
```

## 运行测试

```bash
python3 -m unittest tests.test_sync
```

## 输出结构说明

`retail_prices.json` 中每个市场包含：

- `products.1pack`：单件装价格、件数、单件均价、料号
- `products.4pack`：四件装总价、件数、均价、料号
- `comparison.single_times_4_amount`：按单件零售价买 4 件的总价
- `comparison.savings_amount`：四件装相对单买 4 件的节省金额
- `comparison.discount_rate`：`savings_amount / single_times_4_amount`

说明：不同市场之间不做汇率转换，也不推导税费、配送或活动优惠影响。

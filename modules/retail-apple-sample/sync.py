#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).resolve().parent
DEFAULT_JSON_PATH = ROOT / "data" / "retail_prices.json"
DEFAULT_HTML_PATH = ROOT / "report.html"
DEFAULT_TEMPLATE_PATH = ROOT / "template.html"
USER_AGENT = "price-intelligence-retail/1.0 (+https://www.apple.com)"
PRODUCT_SELECTION_MARKER = "productSelectionData:"

MARKETS = [
    {
        "market_code": "CN",
        "market_name": "中国大陆",
        "storefront": "Apple Online Store China",
        "url": "https://www.apple.com.cn/shop/buy-airtag/airtag",
    },
    {
        "market_code": "US",
        "market_name": "美国",
        "storefront": "Apple Online Store US",
        "url": "https://www.apple.com/shop/buy-airtag/airtag",
    },
    {
        "market_code": "UK",
        "market_name": "英国",
        "storefront": "Apple Online Store UK",
        "url": "https://www.apple.com/uk/shop/buy-airtag/airtag",
    },
    {
        "market_code": "JP",
        "market_name": "日本",
        "storefront": "Apple Online Store Japan",
        "url": "https://www.apple.com/jp/shop/buy-airtag/airtag",
    },
    {
        "market_code": "CA",
        "market_name": "加拿大",
        "storefront": "Apple Online Store Canada",
        "url": "https://www.apple.com/ca/shop/buy-airtag/airtag",
    },
]


def fetch_html(url: str, timeout: float = 30.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_json_object(text: str, marker: str = PRODUCT_SELECTION_MARKER) -> str:
    marker_index = text.find(marker)
    if marker_index < 0:
        raise ValueError(f"未找到页面内嵌 JSON 标记: {marker}")

    start_index = text.find("{", marker_index)
    if start_index < 0:
        raise ValueError("已找到标记，但未找到 JSON 起始花括号")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "\"":
                in_string = False
            continue

        if char == "\"":
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1]

    raise ValueError("页面内嵌 JSON 花括号不完整")


def extract_product_selection_data(html: str) -> dict:
    payload = extract_json_object(html, PRODUCT_SELECTION_MARKER)
    return json.loads(payload)


def strip_tags(value: Optional[str]) -> str:
    text = re.sub(r"<[^>]+>", "", value or "")
    return unescape(text).strip()


def extract_pack_count(pack_key: str, pack_label: str) -> int:
    for candidate in (pack_key, pack_label):
        match = re.search(r"(\d+)", candidate or "")
        if match:
            return int(match.group(1))
    raise ValueError(f"无法识别包装数量: {pack_key!r} / {pack_label!r}")


def parse_amount(raw_amount: Optional[str], display_amount: Optional[str]) -> float:
    for candidate in (raw_amount, strip_tags(display_amount)):
        if not candidate:
            continue
        normalized = re.sub(r"[^0-9.]", "", str(candidate))
        if normalized:
            return float(normalized)
    raise ValueError(f"无法解析价格: raw={raw_amount!r}, display={display_amount!r}")


def normalize_product(product: dict, pack_labels: dict, prices: dict) -> dict:
    pack_key = product["dimensionPackQty"]
    pack_label = pack_labels.get(pack_key, {}).get("value", pack_key)
    price_key = product.get("fullPrice") or product.get("price")
    if not price_key:
        raise ValueError("商品缺少价格键")
    price_info = prices[price_key]
    current_price = price_info.get("currentPrice", {})
    amount = parse_amount(current_price.get("raw_amount"), current_price.get("amount"))
    pack_count = extract_pack_count(pack_key, pack_label)

    return {
        "pack_key": pack_key,
        "pack_label": pack_label,
        "pack_count": pack_count,
        "part_number": product.get("partNumber"),
        "base_part_number": product.get("basePartNumber"),
        "seo_url_token": product.get("seoUrlToken"),
        "price_key": price_key,
        "currency": price_info.get("priceCurrency"),
        "display_amount": strip_tags(current_price.get("amount")),
        "amount": amount,
        "unit_price": round(amount / pack_count, 4),
    }


def build_market_snapshot(market: dict, html: str, fetched_at: str) -> dict:
    selection_data = extract_product_selection_data(html)
    prices = selection_data["displayValues"]["prices"]
    pack_labels = selection_data["displayValues"]["dimensionPackQty"]

    products = {}
    for product in selection_data["products"]:
        normalized = normalize_product(product, pack_labels, prices)
        products[normalized["pack_key"]] = normalized

    if "1pack" not in products or "4pack" not in products:
        raise ValueError("{} 页面缺少 AirTag 单件或四件装数据".format(market["market_code"]))

    single = products["1pack"]
    four_pack = products["4pack"]
    single_times_four = round(single["amount"] * 4, 4)
    savings_amount = round(single_times_four - four_pack["amount"], 4)
    discount_rate = round(savings_amount / single_times_four, 6) if single_times_four else 0.0

    return {
        "market_code": market["market_code"],
        "market_name": market["market_name"],
        "storefront": market["storefront"],
        "source_url": market["url"],
        "fetched_at": fetched_at,
        "currency": single["currency"],
        "products": {
            "1pack": single,
            "4pack": four_pack,
        },
        "comparison": {
            "single_times_4_amount": single_times_four,
            "four_pack_amount": four_pack["amount"],
            "savings_amount": savings_amount,
            "discount_rate": discount_rate,
            "four_pack_cheaper": four_pack["amount"] < single_times_four,
            "no_fx_conversion": True,
        },
    }


def build_dataset(markets: list[dict], fetched_at: str) -> dict:
    currencies = sorted({item["currency"] for item in markets})
    best_discount_market = max(markets, key=lambda item: item["comparison"]["discount_rate"])
    return {
        "schema_version": "1.0",
        "generated_at": fetched_at,
        "product": "Apple AirTag",
        "source_type": "Apple public product buy pages with embedded productSelectionData JSON",
        "comparison_rule": "仅比较同一市场同一币种下的单件价 × 4 与四件装总价，不做跨币种换汇。",
        "markets": markets,
        "summary": {
            "market_count": len(markets),
            "currencies": currencies,
            "best_discount_market": {
                "market_code": best_discount_market["market_code"],
                "market_name": best_discount_market["market_name"],
                "currency": best_discount_market["currency"],
                "discount_rate": best_discount_market["comparison"]["discount_rate"],
                "savings_amount": best_discount_market["comparison"]["savings_amount"],
            },
        },
    }


def render_report(data: dict, template_path: Path, output_path: Path) -> None:
    template = template_path.read_text(encoding="utf-8")
    marker = "/*__RETAIL_DATA__*/null"
    if template.count(marker) != 1:
        raise ValueError("模板中的数据标记数量必须为 1")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    output_path.write_text(template.replace(marker, payload), encoding="utf-8")


def write_json(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_retail_prices(timeout: float = 30.0) -> dict:
    fetched_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    snapshots = []
    for market in MARKETS:
        html = fetch_html(market["url"], timeout=timeout)
        snapshots.append(build_market_snapshot(market, html, fetched_at))
    return build_dataset(snapshots, fetched_at)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抓取 Apple AirTag 各市场零售价格并生成离线报告")
    parser.add_argument("--output", type=Path, default=DEFAULT_JSON_PATH, help="JSON 输出路径")
    parser.add_argument("--html", type=Path, default=DEFAULT_HTML_PATH, help="HTML 报告输出路径")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE_PATH, help="HTML 模板路径")
    parser.add_argument("--timeout", type=float, default=30.0, help="单页抓取超时秒数")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    data = sync_retail_prices(timeout=args.timeout)
    write_json(data, args.output)
    render_report(data, args.template, args.html)

    summary = data["summary"]["best_discount_market"]
    print(
        "已抓取 {market_count} 个市场；四件装折扣最高市场为 {market_name}（{market_code}），节省 {savings:.2f} {currency}，折扣率 {discount:.2%}。".format(
            market_count=data["summary"]["market_count"],
            market_name=summary["market_name"],
            market_code=summary["market_code"],
            savings=summary["savings_amount"],
            currency=summary["currency"],
            discount=summary["discount_rate"],
        )
    )
    print(f"JSON: {args.output}")
    print(f"HTML: {args.html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

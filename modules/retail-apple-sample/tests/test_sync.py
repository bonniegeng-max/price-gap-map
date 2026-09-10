import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sync


SAMPLE_SELECTION_DATA = {
    "sections": [{"formFieldName": "dimensionPackQty"}],
    "displayValues": {
        "dimensionPackQty": {
            "1pack": {"value": "1 件装"},
            "4pack": {"value": "4 件装"},
        },
        "prices": {
            "249_00": {
                "priceCurrency": "CNY",
                "currentPrice": {"amount": "RMB 249", "raw_amount": "249.00"},
            },
            "849_00": {
                "priceCurrency": "CNY",
                "currentPrice": {"amount": "<span>RMB 849</span>", "raw_amount": "849.00"},
            },
        },
    },
    "products": [
        {
            "dimensionPackQty": "1pack",
            "partNumber": "MFE94CH/A",
            "basePartNumber": "MFE94",
            "seoUrlToken": "1-pack",
            "fullPrice": "249_00",
        },
        {
            "dimensionPackQty": "4pack",
            "partNumber": "MFEA4CH/A",
            "basePartNumber": "MFEA4",
            "seoUrlToken": "4-pack",
            "fullPrice": "849_00",
        },
    ],
}

SAMPLE_HTML = f"<html><head></head><body><script>productSelectionData: {json.dumps(SAMPLE_SELECTION_DATA, ensure_ascii=False)};</script></body></html>"
SAMPLE_MARKET = {
    "market_code": "CN",
    "market_name": "中国大陆",
    "storefront": "Apple Online Store China",
    "url": "https://www.apple.com.cn/shop/buy-airtag/airtag",
}


class SyncTests(unittest.TestCase):
    def test_extract_product_selection_data(self):
        data = sync.extract_product_selection_data(SAMPLE_HTML)
        self.assertEqual(data["products"][0]["dimensionPackQty"], "1pack")
        self.assertEqual(data["displayValues"]["prices"]["849_00"]["priceCurrency"], "CNY")

    def test_build_market_snapshot_computes_discount(self):
        snapshot = sync.build_market_snapshot(SAMPLE_MARKET, SAMPLE_HTML, "2026-09-07T00:00:00Z")
        self.assertEqual(snapshot["products"]["1pack"]["amount"], 249.0)
        self.assertEqual(snapshot["products"]["4pack"]["amount"], 849.0)
        self.assertEqual(snapshot["comparison"]["single_times_4_amount"], 996.0)
        self.assertEqual(snapshot["comparison"]["savings_amount"], 147.0)
        self.assertAlmostEqual(snapshot["comparison"]["discount_rate"], 147 / 996, places=6)

    def test_parse_amount_handles_html_wrapped_currency(self):
        self.assertEqual(sync.parse_amount(None, "<span>18,400円</span>"), 18400.0)
        self.assertEqual(sync.extract_pack_count("4pack", "4 个装"), 4)

    def test_render_report_embeds_json_payload(self):
        dataset = sync.build_dataset([
            sync.build_market_snapshot(SAMPLE_MARKET, SAMPLE_HTML, "2026-09-07T00:00:00Z")
        ], "2026-09-07T00:00:00Z")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            template = temp / "template.html"
            output = temp / "report.html"
            template.write_text("<script>const DATA=/*__RETAIL_DATA__*/null;</script>", encoding="utf-8")
            sync.render_report(dataset, template, output)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("中国大陆", rendered)
            self.assertNotIn("/*__RETAIL_DATA__*/null", rendered)


if __name__ == "__main__":
    unittest.main()

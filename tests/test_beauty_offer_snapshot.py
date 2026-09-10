import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "beauty-11-estee-lauder-case.json"
HTML_PATH = ROOT / "docs" / "beauty-11-real-case.html"
GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1}


class OfferSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.offers = {item["offer_id"]: item for item in cls.data["offers"]}
        cls.evidence = {item["evidence_id"]: item for item in cls.data["evidence"]}

    def test_schema_and_snapshot_are_explicit(self):
        self.assertEqual(self.data["schema_version"], "2.0")
        self.assertEqual(self.data["model"], "offer_snapshot")
        self.assertEqual(self.data["snapshot"]["freshness"], "unresolved")
        self.assertIsNone(self.data["snapshot"]["captured_at"])
        self.assertTrue(self.data["snapshot"]["freshness_note"])

    def test_cash_landed_formula_for_eligible_offers(self):
        for offer in self.data["offers"]:
            if not offer["price_comparison_eligible"]:
                continue
            expected = (
                offer["display_price"]
                - offer["confirmed_discount"]
                + offer["mandatory_cost"]
            )
            self.assertAlmostEqual(offer["cash_landed_price"], expected)

    def test_current_gap_formula(self):
        comparison = self.data["comparison"]
        reference = self.offers[comparison["reference_offer_id"]]["cash_landed_price"]
        candidate = self.offers[comparison["candidate_offer_id"]]["cash_landed_price"]
        gap = reference - candidate
        self.assertEqual(gap, 60.0)
        self.assertEqual(comparison["gap_amount"], gap)
        self.assertAlmostEqual(comparison["gap_rate"], gap / reference, places=6)

    def test_unknown_gifts_never_produce_net_value(self):
        for offer in self.data["offers"]:
            if not offer["gift"]["composition_known"]:
                self.assertIsNone(offer["gift"]["gift_net_value"])
                self.assertIsNone(offer["net_effective_cost"])
        self.assertFalse(self.data["comparison"]["net_value_comparison_available"])

    def test_every_offer_has_valid_evidence_reference(self):
        for offer in self.data["offers"]:
            self.assertTrue(offer["evidence_refs"])
            for evidence_id in offer["evidence_refs"]:
                self.assertIn(evidence_id, self.evidence)
                self.assertEqual(
                    offer["evidence_grade"], self.evidence[evidence_id]["grade"]
                )

    def test_evidence_grade_controls_comparison(self):
        minimum = self.data["evidence_grade_policy"]["minimum_grade_for_price_comparison"]
        for offer in self.data["offers"]:
            if offer["price_comparison_eligible"]:
                self.assertEqual(offer["period"], "current")
                self.assertEqual(offer["product_match"], "exact")
                self.assertGreaterEqual(
                    GRADE_RANK[offer["evidence_grade"]], GRADE_RANK[minimum]
                )

    def test_historical_and_suning_clues_are_excluded_with_reasons(self):
        excluded = [
            self.offers["O-CURRENT-SUNING-CLUE"],
            self.offers["O-HISTORY-2024"],
            self.offers["O-HISTORY-2025"],
        ]
        for offer in excluded:
            self.assertFalse(offer["price_comparison_eligible"])
            self.assertFalse(offer["purchase_recommendation_eligible"])
            self.assertTrue(offer["exclusion_reasons"])
        self.assertEqual(self.offers["O-HISTORY-2024"]["product_match"], "mismatch")
        self.assertEqual(self.offers["O-HISTORY-2025"]["product_match"], "mismatch")

    def test_no_channel_is_recommended_without_grade_a(self):
        eligible = [o for o in self.data["offers"] if o["purchase_recommendation_eligible"]]
        self.assertEqual(eligible, [])
        self.assertIsNone(self.data["decision"]["recommended_channel"])
        self.assertEqual(self.data["decision"]["result"], "有条件采购")

    def test_html_exposes_core_facts_and_exclusions(self):
        html = HTML_PATH.read_text(encoding="utf-8")
        for text in ["Offer Snapshot", "¥720", "¥660", "¥641.20", "2024", "2025", "不计算赠品净值", "排除"]:
            self.assertIn(text, html)


if __name__ == "__main__":
    unittest.main()

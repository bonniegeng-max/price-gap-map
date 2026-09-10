import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "beauty-offer-auditor"
SKILL_PATH = SKILL_DIR / "SKILL.md"
EXAMPLE_PATH = SKILL_DIR / "examples" / "generic-case.json"
REQUIRED_FILES = [
    SKILL_PATH,
    SKILL_DIR / "README.md",
    SKILL_DIR / "references" / "offer-snapshot-v2.md",
    SKILL_DIR / "references" / "output-template.md",
    EXAMPLE_PATH,
]
GRADE_RANK = {"A": 4, "B": 3, "C": 2, "D": 1}


class BeautyOfferAuditorSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_text = SKILL_PATH.read_text(encoding="utf-8")
        cls.data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        cls.offers = {item["offer_id"]: item for item in cls.data["offers"]}
        cls.evidence = {item["evidence_id"]: item for item in cls.data["evidence"]}

    def test_required_skill_structure(self):
        for path in REQUIRED_FILES:
            self.assertTrue(path.is_file(), path)

    def test_frontmatter_is_standard_and_english(self):
        parts = self.skill_text.split("---", 2)
        self.assertEqual(parts[0], "")
        self.assertEqual(len(parts), 3)
        frontmatter = parts[1]
        self.assertIn('name: "beauty-offer-auditor"', frontmatter)
        description_line = next(line for line in frontmatter.splitlines() if line.startswith("description:"))
        description = description_line.split(chr(34), 2)[1]
        self.assertLessEqual(len(description), 200)
        self.assertTrue(description.isascii())
        self.assertTrue(any("一" <= char <= "鿿" for char in parts[2]))

    def test_documented_boundaries_and_degradation(self):
        for phrase in ["不宣称", "不自动", "私人数据", "一次查询结果", "失败降级", "历史 offer", "赠品", "套装"]:
            self.assertIn(phrase, self.skill_text)

    def test_example_schema_and_no_personal_fields(self):
        self.assertEqual(self.data["schema_version"], "2.0")
        self.assertEqual(self.data["model"], "offer_snapshot")
        self.assertTrue(self.data["example_only"])
        for key in ["snapshot", "normalized_product", "offers", "comparison", "decision", "evidence"]:
            self.assertIn(key, self.data)
        serialized = json.dumps(self.data, ensure_ascii=False).lower()
        for forbidden in ["phone", "mobile", "address", "order_id", "account_id", "payment_token"]:
            self.assertNotIn(forbidden, serialized)

    def test_cash_landed_formula(self):
        for offer in self.data["offers"]:
            values = [offer["display_price"], offer["confirmed_discount"], offer["mandatory_cost"]]
            if None in values:
                self.assertIsNone(offer["cash_landed_price"])
                self.assertFalse(offer["price_comparison_eligible"])
                continue
            expected = values[0] - values[1] + values[2]
            self.assertAlmostEqual(offer["cash_landed_price"], expected)

    def test_bundle_allocation_formula(self):
        offer = self.offers["O-CURRENT-BUNDLE"]
        bundle = offer["bundle"]
        total = sum(item["reference_value"] * item["quantity"] for item in bundle["components"])
        required = sum(item["reference_value"] * item["quantity"] for item in bundle["components"] if item["required"])
        self.assertAlmostEqual(bundle["bundle_reference_value_total"], total)
        self.assertAlmostEqual(bundle["required_item_reference_value"], required)
        self.assertAlmostEqual(bundle["required_item_allocated_cost"], offer["cash_landed_price"] * required / total)

    def test_gift_and_net_effective_cost_formulas(self):
        for offer in self.data["offers"]:
            gift = offer["gift"]
            if not gift["composition_known"]:
                self.assertIsNone(gift["gift_net_value"])
                self.assertIsNone(offer["net_effective_cost"])
                continue
            expected_gift = sum(item["reference_value"] * item["quantity"] * item["realization_rate"] for item in gift["items"])
            self.assertAlmostEqual(gift["gift_net_value"], expected_gift)
            self.assertAlmostEqual(offer["net_effective_cost"], offer["cash_landed_price"] - expected_gift)

    def test_gap_formula(self):
        comparison = self.data["comparison"]
        reference = self.offers[comparison["reference_offer_id"]]["cash_landed_price"]
        candidate = self.offers[comparison["candidate_offer_id"]]["cash_landed_price"]
        gap = reference - candidate
        self.assertAlmostEqual(comparison["gap_amount"], gap)
        self.assertAlmostEqual(comparison["gap_rate"], gap / reference, places=6)

    def test_evidence_and_eligibility_rules(self):
        minimum = self.data["evidence_grade_policy"]["minimum_grade_for_price_comparison"]
        for offer in self.data["offers"]:
            self.assertTrue(offer["evidence_refs"])
            for evidence_id in offer["evidence_refs"]:
                self.assertIn(evidence_id, self.evidence)
                self.assertEqual(offer["evidence_grade"], self.evidence[evidence_id]["grade"])
            if offer["price_comparison_eligible"]:
                self.assertEqual(offer["period"], "current")
                self.assertEqual(offer["product_match"], "exact")
                self.assertGreaterEqual(GRADE_RANK[offer["evidence_grade"]], GRADE_RANK[minimum])
            if offer["purchase_recommendation_eligible"]:
                self.assertEqual(offer["evidence_grade"], "A")

    def test_history_and_clues_are_excluded(self):
        for offer in self.data["offers"]:
            if offer["period"] == "history":
                self.assertIsInstance(offer["event_year"], int)
                self.assertFalse(offer["price_comparison_eligible"])
                self.assertFalse(offer["purchase_recommendation_eligible"])
            if offer["evidence_grade"] in {"C", "D"}:
                self.assertFalse(offer["price_comparison_eligible"])

    def test_recommendation_points_only_to_grade_a_offer(self):
        recommended = self.data["decision"]["recommended_offer_id"]
        self.assertIsNotNone(recommended)
        offer = self.offers[recommended]
        self.assertEqual(offer["evidence_grade"], "A")
        self.assertTrue(offer["purchase_recommendation_eligible"])


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path

import sync

HEADER="source,platform,model_key,model_name,author,open_weight,variant,region,metric,usd_per_1m,context_length,effective_date"
SAMPLE="\n".join([HEADER,"openrouter,平台甲,org/model-x,Model X,Acme,true,fp8,global,input,0.2,128000,2026-01-01","openrouter,平台甲,org/model-x,Model X,Acme,true,fp8,global,output,0.8,128000,2026-01-01","aws,平台乙,bedrock:model x,Model-X,Acme,true,standard,us-east-1,input,0.4,128000,2026-02-01","aws,平台乙,bedrock:model x,Model-X,Acme,true,standard,us-east-1,output,1.2,128000,2026-02-01","bad,坏行,x,Bad,A,,standard,,input,not-a-price,,"])

class SyncTests(unittest.TestCase):
    def test_canonical_model_id_ignores_punctuation_and_case(self):
        self.assertEqual(sync.canonical_model_id("Acme","Model X","a"),sync.canonical_model_id("acme","Model-X","b"))
    def test_parse_pairs_metrics_and_preserves_dimensions(self):
        data=sync.enrich(sync.parse_csv(SAMPLE,"2026-01-01T00:00:00Z","fixture://prices.csv"))
        self.assertEqual(data["stats"]["source_rows"],5)
        self.assertEqual(data["stats"]["invalid_or_skipped_rows"],1)
        self.assertEqual(data["stats"]["offers"],2)
        self.assertEqual(data["stats"]["cross_platform_models"],1)
        first=data["offers"][0]["prices_usd_per_1m_tokens"]
        self.assertEqual((first["input"],first["output"]),(0.2,0.8))
        factors=data["observed_difference_factors"]["acme-model-x"]
        self.assertIn("区域",{x["label"] for x in factors})
        self.assertIn("计费变体/精度",{x["label"] for x in factors})
    def test_missing_column_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"缺少字段"):
            sync.parse_csv("source,platform\na,b\n","2026-01-01T00:00:00Z")
    def test_render_embeds_data_for_file_protocol(self):
        data=sync.enrich(sync.parse_csv(SAMPLE,"2026-01-01T00:00:00Z")); data["source"]["sha256"]="abc"
        with tempfile.TemporaryDirectory() as d:
            d=Path(d); t=d/"t.html"; out=d/"index.html"
            t.write_text("<script>const D=/*__PRICE_DATA__*/null;</script>",encoding="utf-8")
            sync.render(data,t,out)
            text=out.read_text(encoding="utf-8")
            self.assertIn("acme-model-x",text)
            self.assertNotIn("/*__PRICE_DATA__*/null",text)

if __name__=="__main__": unittest.main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,sys,urllib.request
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

URL="https://raw.githubusercontent.com/tokencanopy/price/main/data/current/prices.csv"
REPO="https://github.com/tokencanopy/price"
ROOT=Path(__file__).resolve().parent
REQUIRED={"source","platform","model_key","model_name","author","variant","region","metric","usd_per_1m"}
METRICS={"input","output","cache_read","cache_write"}

def clean(v): return str(v or "").strip()
def canonical_model_id(author,name,key):
    value=" ".join(x for x in (clean(author),clean(name)) if x) or clean(key).split(":",1)[-1]
    return re.sub(r"[\W_]+","-",value.casefold(),flags=re.UNICODE).strip("-") or "unknown"
def as_int(v):
    try: return int(float(clean(v))) if clean(v) else None
    except ValueError: return None

def parse_csv(text,retrieved_at,source_url=URL):
    reader=csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    missing=REQUIRED-set(reader.fieldnames or [])
    if missing: raise ValueError("prices.csv 缺少字段: "+", ".join(sorted(missing)))
    groups={}; raw_rows=bad=0
    for line,row in enumerate(reader,start=2):
        raw_rows+=1; metric=clean(row.get("metric")).lower(); raw_price=clean(row.get("usd_per_1m"))
        try:
            price=float(raw_price)
            if metric not in METRICS or price<0: raise ValueError
        except ValueError:
            bad+=1; continue
        author,name,key=clean(row.get("author")),clean(row.get("model_name")),clean(row.get("model_key"))
        cid=canonical_model_id(author,name,key); platform=clean(row.get("platform")) or clean(row.get("source")) or "未知平台"
        variant=clean(row.get("variant")) or "未标注"; region=clean(row.get("region")) or "未标注"
        gkey=(cid,platform,variant,region)
        if gkey not in groups:
            groups[gkey]={"id":"|".join(gkey),"canonical_model_id":cid,"model_name":name or key or "未知模型","author":author or "未知","platform":platform,"variant":variant,"region":region,"prices_usd_per_1m_tokens":{m:None for m in sorted(METRICS)},"context_length":as_int(row.get("context_length")),"effective_date":clean(row.get("effective_date")) or None,"source_ids":set(),"source_model_keys":set(),"source_rows":[]}
        offer=groups[gkey]; offer["prices_usd_per_1m_tokens"][metric]=price
        offer["source_ids"].add(clean(row.get("source")) or "未知"); offer["source_rows"].append(line)
        if key: offer["source_model_keys"].add(key)
        if offer["context_length"] is None: offer["context_length"]=as_int(row.get("context_length"))
    offers=[]
    for o in groups.values():
        o["source_ids"]=sorted(o["source_ids"]); o["source_model_keys"]=sorted(o["source_model_keys"]); o["source_rows"]=sorted(set(o["source_rows"])); offers.append(o)
    offers.sort(key=lambda o:(o["author"].casefold(),o["model_name"].casefold(),o["platform"].casefold(),o["variant"],o["region"]))
    mp=defaultdict(set)
    for o in offers: mp[o["canonical_model_id"]].add(o["platform"])
    return {"schema_version":"1.0","retrieved_at":retrieved_at,"source":{"name":"tokencanopy/price","url":source_url,"repository":REPO,"license":"CC BY 4.0","price_unit":"USD / 1,000,000 tokens"},"normalization":{"comparison_key":["canonical_model_id","platform","variant","region"],"canonical_model_rule":"author + model_name 经 Unicode casefold 与标点归一化","missing_dimension":"未标注","note":"输入/输出价格仅在模型、平台、变体和区域完全相同时配对；未补齐缺失价格。"},"stats":{"source_rows":raw_rows,"invalid_or_skipped_rows":bad,"offers":len(offers),"models":len(mp),"cross_platform_models":sum(len(v)>1 for v in mp.values()),"platforms":len({o["platform"] for o in offers})},"offers":offers}

def observed_factors(items):
    result=[]
    for field,label in [("variant","计费变体/精度"),("region","区域"),("context_length","上下文长度"),("effective_date","生效日期"),("source_ids","采集来源")]:
        vals={json.dumps(x.get(field),ensure_ascii=False,sort_keys=True) for x in items if x.get(field) not in (None,"","未标注",[])}
        if len(vals)>1: result.append({"field":field,"label":label,"observed_values":len(vals)})
    mi=sum(x["prices_usd_per_1m_tokens"]["input"] is None for x in items); mo=sum(x["prices_usd_per_1m_tokens"]["output"] is None for x in items)
    if mi or mo: result.append({"field":"metric_completeness","label":"输入/输出价格完整度","observed_values":2,"missing_input":mi,"missing_output":mo})
    return result

def enrich(data):
    by=defaultdict(list)
    for o in data["offers"]: by[o["canonical_model_id"]].append(o)
    data["observed_difference_factors"]={k:observed_factors(v) for k,v in by.items() if len({o["platform"] for o in v})>1}; return data

def download(url,timeout):
    req=urllib.request.Request(url,headers={"User-Agent":"price-intelligence-live/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()
def render(data,template,out):
    text=template.read_text(encoding="utf-8"); marker="/*__PRICE_DATA__*/null"
    if text.count(marker)!=1: raise ValueError("模板数据标记数量不是 1")
    payload=json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("</","<\\/")
    out.write_text(text.replace(marker,payload),encoding="utf-8")
def main(argv=None):
    ap=argparse.ArgumentParser(description="同步公开 LLM 价格并生成离线比较页")
    ap.add_argument("--url",default=URL); ap.add_argument("--input",type=Path); ap.add_argument("--output",type=Path,default=ROOT/"data/prices.json"); ap.add_argument("--html",type=Path,default=ROOT/"index.html"); ap.add_argument("--template",type=Path,default=ROOT/"template.html"); ap.add_argument("--timeout",type=float,default=30)
    a=ap.parse_args(argv); stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")
    raw=a.input.read_bytes() if a.input else download(a.url,a.timeout); data=enrich(parse_csv(raw.decode("utf-8-sig"),stamp,a.url)); data["source"]["sha256"]=hashlib.sha256(raw).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); render(data,a.template,a.html)
    s=data["stats"]; print(f"已同步 {s['source_rows']} 行，标准化为 {s['offers']} 个报价；{s['cross_platform_models']} 个模型可跨平台比较。")
    return 0
if __name__=="__main__": sys.exit(main())

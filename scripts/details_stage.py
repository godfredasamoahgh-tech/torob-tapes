#!/usr/bin/env python3
"""Details stage: fetch full specs, sellers & in-store info for Torob products."""
import argparse
import json
import os
import random
import sys
import time
import urllib.parse
from curl_cffi import requests as cr

ap = argparse.ArgumentParser()
ap.add_argument("--shard", default="0/1")
ap.add_argument("--budget", type=int, default=55)
ap.add_argument("--out", default="details.jsonl")
ap.add_argument("--list", dest="lst", default="list.json")
a = ap.parse_args()

si, sn = (int(x) for x in a.shard.split("/"))

items_dict = json.load(open(a.lst, encoding="utf-8"))
prs = sorted(items_dict.keys())
mine = [p for i, p in enumerate(prs) if i % sn == si]

done = set()
if os.path.exists(a.out):
    for line in open(a.out, encoding="utf-8"):
        try:
            done.add(json.loads(line).get("prk"))
        except Exception:
            pass

todo = [p for p in mine if p not in done]
print(f"Shard {a.shard}: {len(mine)} assigned, {len(done)} already done, {len(todo)} to fetch (budget: {a.budget})", flush=True)

s = cr.Session(impersonate="chrome131")
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Referer": "https://torob.com/",
    "Accept": "application/json"
}

ok_count = 0
wall_count = 0
t0 = time.time()

with open(a.out, "a", encoding="utf-8") as f_out:
    for prk in todo[: a.budget]:
        meta = items_dict.get(prk, {})
        u = f"https://api.torob.com/v4/base-product/details/?prk={prk}"
        
        success = False
        for attempt in range(2):
            try:
                r = s.get(u, headers=H, timeout=25)
                if r.status_code == 200 and r.text.strip() and "آیا شما یک ربات" not in r.text:
                    d = r.json()
                    record = {
                        "prk": prk,
                        "name": d.get("name1") or meta.get("title") or "",
                        "name_en": d.get("name2") or meta.get("title_en") or "",
                        "price": d.get("price") or meta.get("price"),
                        "price_text": d.get("price_text") or meta.get("price_text"),
                        "web_client_absolute_url": d.get("web_client_absolute_url") or meta.get("url") or f"https://torob.com/p/{prk}/",
                        "category": d.get("category_name") or "جارو برقی",
                        "shop_count": d.get("shop_count") or 0,
                        "struct_specs": d.get("structural_specs"),
                        "sellers": d.get("products_info", []),
                        "in_store": d.get("products_in_store_info", []),
                        "tag": meta.get("tag", "")
                    }
                    f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
                    f_out.flush()
                    ok_count += 1
                    success = True
                    break
                else:
                    wall_count += 1
                    print(f"[{prk}] Wall / Error status {r.status_code}", flush=True)
                    time.sleep(15)
            except Exception as e:
                print(f"[{prk}] Request exception: {e}", flush=True)
                time.sleep(2)
                
        time.sleep(1.2 + random.uniform(0.1, 0.4))
        if ok_count >= a.budget:
            break

print(f"Shard {a.shard} finished: {ok_count} fetched, {wall_count} walls in {time.time()-t0:.1f}s", flush=True)

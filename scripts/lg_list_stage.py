#!/usr/bin/env python3
"""List stage for LG 2000W Vacuum Cleaner Spare Parts & Accessories on Torob."""
import json
import os
import re
import sys
import time
import urllib.parse
from curl_cffi import requests as cr

OUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "lg_list.json"

CATEGORIES = {
    "۱. قطعه اصلی (جاپاکتی و نگهدارنده پاکت ال‌جی)": [
        "جاپاکتی جاروبرقی ال جی",
        "نگهدارنده پاکت جاروبرقی ال جی",
        "جا پاکتی جاروبرقی ال جی",
        "هولدر پاکت جاروبرقی ال جی",
        "جاپاکتی جاروبرقی ال جی 2000",
        "نگهدارنده کیسه جاروبرقی ال جی"
    ],
    "۲. کیسه و پاکت جاروبرقی (یکبار مصرف نانو و دائمی زیپ‌دار ال‌جی ۲۰۰۰)": [
        "پاکت جاروبرقی ال جی 2000",
        "کیسه جاروبرقی ال جی 2000",
        "پاکت جارو برقی ال جی 2000",
        "پاکت نانو جاروبرقی ال جی 2000",
        "کیسه دائمی جاروبرقی ال جی 2000",
        "پاکت هپا جاروبرقی ال جی 2000"
    ],
    "۳. فیلتر محافظ موتور و فیلتر هپا (ال‌جی ۲۰۰۰)": [
        "فیلتر جاروبرقی ال جی 2000",
        "فیلتر محافظ موتور جاروبرقی ال جی 2000",
        "فیلتر هپا جاروبرقی ال جی 2000",
        "فیلتر ابری جاروبرقی ال جی 2000",
        "فیلتر خروجی جاروبرقی ال جی 2000"
    ],
    "۴. گلویی، زانویی و کوپلینگ خرطومی روی در (ال‌جی ۲۰۰۰)": [
        "گلویی جاروبرقی ال جی 2000",
        "زانویی جاروبرقی ال جی 2000",
        "کوپلینگ جاروبرقی ال جی 2000",
        "کوپلینگ و گلویی جاروبرقی ال جی",
        "برس و گلویی جاروبرقی ال جی"
    ]
}

# Negative filters to avoid completely unrelated items
REJECT_PATTERNS = [
    r'سامسونگ\b(?!.*ال\s*جی)',
    r'بوش\b(?!.*ال\s*جی)',
    r'پارس\s*خزر\b(?!.*ال\s*جی)',
    r'پاناسونیک\b(?!.*ال\s*جی)',
    r'فیلیپس\b(?!.*ال\s*جی)',
    r'تیوا\b|سپاهان\b|هیتاچی\b',
    r'تلویزیون\b|لباسشویی\b|یخچال\b|مایکروویو\b|کولر\b|موبایل\b'
]
re_junk = re.compile('|'.join(REJECT_PATTERNS), re.IGNORECASE)

s = cr.Session(impersonate="chrome131")
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Referer": "https://torob.com/",
    "Accept": "application/json"
}

items = {}
req_count = 0

print("=== STARTING LG 2000W VACUUM CLEANER PARTS HARVEST ===")

for cat_title, q_list in CATEGORIES.items():
    cat_new = 0
    print(f"\n--- Harvesting: {cat_title} ---")
    for q in q_list:
        q_new = 0
        for page in range(1, 4): # up to 3 pages per query
            url = f"https://api.torob.com/v4/base-product/search/?q={urllib.parse.quote(q)}&page={page}&size=24&source=next_desktop"
            try:
                r = s.get(url, headers=H, timeout=12)
                req_count += 1
                if r.status_code != 200:
                    break
                data = r.json()
            except Exception as e:
                break
                
            results = data.get("results", [])
            if not results:
                break
                
            for it in results:
                prk = it.get("random_key")
                if not prk:
                    continue
                title = (it.get("name1") or "").strip()
                if not title or re_junk.search(title):
                    continue
                if prk not in items:
                    items[prk] = {
                        "prk": prk,
                        "title": title,
                        "title_en": it.get("name2") or "",
                        "price": it.get("price"),
                        "price_text": it.get("price_text") or "",
                        "url": it.get("web_client_absolute_url") or f"https://torob.com/p/{prk}/",
                        "shop_text": it.get("shop_text") or "",
                        "stock_status": it.get("stock_status") or "",
                        "category_section": cat_title,
                        "source_query": q
                    }
                    q_new += 1
                    cat_new += 1
            time.sleep(0.3)
            if len(results) < 24:
                break
        print(f"  [{q:32}] -> +{q_new:2d} new (Total unique: {len(items):3d})")
    print(f"Section [{cat_title}] added {cat_new} items.")

print("\n" + "=" * 60)
print(f"TOTAL UNIQUE LG 2000 PARTS COLLECTED: {len(items)}")
print(f"TOTAL SEARCH REQUESTS: {req_count}")
print("=" * 60)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Saved to {OUT_FILE}")

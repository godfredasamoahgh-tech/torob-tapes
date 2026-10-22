#!/usr/bin/env python3
"""List stage for Torob vacuum cleaners (جارو برقی) with full category & brand slicing."""
import json
import os
import re
import sys
import time
import urllib.parse
from curl_cffi import requests as cr

OUT_FILE = sys.argv[1] if len(sys.argv) > 1 else "list.json"

# Strict reject patterns for junk (spare parts, bags, filters, hoses, motors)
REJECT_PATTERNS = [
    r'کیسه\b|پاکت\b',
    r'فیلتر\b|هپا\b|hepa\b',
    r'خرطومی\b|تلسکوپی\b',
    r'پارویی\b|برس\b|سری\b|نازل\b',
    r'موتور\b',
    r'سیم\s*جمع\s*کن',
    r'زانویی\b|کوپلینگ\b',
    r'برد\b|کلید\b',
    r'لوازم\s*یدکی|قطعه|قطعات',
    r'خوشبو\s*کننده',
    r'دسته\s*جارو',
    r'درب\s*جارو',
    r'چرخ\s*جارو',
    r'شیلنگ\b|شیلنگ',
    r'کاور\b|محافظ\b',
    r'تبدیل\b|رابط\b'
]
re_junk = re.compile('|'.join(REJECT_PATTERNS), re.IGNORECASE)

# Brands in Category 203
BRANDS = [
    (73, 'بوش'), (21, 'فیلیپس'), (222, 'آ ا گ'), (14294, 'پارس خزر'), (5, 'سامسونگ'),
    (20, 'پاناسونیک'), (5804, 'پاکشوما'), (1082, 'فکر'), (6, 'ال جی'), (34, 'دوو'),
    (15, 'تفال'), (102, 'شیائومی'), (247, 'هیتاچی'), (212, 'یونیک'), (13362, 'میله'),
    (2922, 'الکترولوکس'), (16071, 'بیسل'), (11916, 'روسو'), (8053, 'نانیوا'), (99, 'کرشر'),
    (17, 'تولیپس'), (401, 'کاراجا'), (35, 'اسنوا'), (2948, 'مایر'), (4615, 'ایکس ویژن'),
    (29266, 'راف'), (298, 'داتیس'), (1099, 'دلمونتی'), (2949, 'جیپاس'), (2189, 'سام'),
    (14882, 'پاکتین'), (16, 'گوسونیک'), (12035, 'لایف'), (1097, 'سنکور'), (6816, 'تیوا'),
    (2696, 'میگل'), (2952, 'سایا'), (29462, 'ساینا'), (220, 'تکنو'), (12342, 'جنرال فیت'),
    (1430, 'پلار'), (53513, 'ناسیونال'), (7711, 'سپاهان'), (10783, 'بنس'), (1767, 'اینترنشنال آنیل'),
    (13594, 'بلانتون'), (1062, 'هاردستون'), (1501, 'دسینی'), (1070, 'ویداس'), (5226, 'شروین')
]

# Form factor search queries
QUERIES = [
    "جارو برقی",
    "جاروبرقی کیسه ای",
    "جاروبرقی مخزنی",
    "جاروبرقی بدون کیسه",
    "جاروبرقی سطلی",
    "جاروبرقی عصایی",
    "جاروبرقی صنعتی",
    "جاروبرقی آب و خاک",
    "جارو برقی موشکی",
    "جاروبرقی پرتابل",
    "جارو برقی خوابیده",
    "جاروبرقی ایستاده",
    "جاروبرقی مرکزی"
]

s = cr.Session(impersonate="chrome")
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
    "Referer": "https://torob.com/",
    "Accept": "application/json"
}

items = {}
req_count = 0

def add_product(it, tag=""):
    prk = it.get("random_key")
    if not prk or prk in items:
        return False
    title = (it.get("name1") or "").strip()
    if not title:
        return False
    if re_junk.search(title):
        return False
    # Validate it is actually a vacuum cleaner
    t_lower = title.lower()
    if not any(k in t_lower for k in ["جارو", "جاروبرقی", "vacuum"]):
        return False
        
    items[prk] = {
        "prk": prk,
        "title": title,
        "title_en": it.get("name2") or "",
        "price": it.get("price"),
        "price_text": it.get("price_text") or "",
        "url": it.get("web_client_absolute_url") or f"https://torob.com/p/{prk}/",
        "shop_text": it.get("shop_text") or "",
        "stock_status": it.get("stock_status") or "",
        "tag": tag
    }
    return True

print("=== 1. HARVESTING CATEGORY 203 BY SORTS (popularity, price_asc, price_desc, newest) ===")
for sort_mode in ["popularity", "price_asc", "price_desc", "newest"]:
    sort_new = 0
    for page in range(1, 50): # up to page 49
        url = f"https://api.torob.com/v4/base-product/search/?category=203&page={page}&size=24&sort={sort_mode}&source=next_desktop"
        try:
            r = s.get(url, headers=H, timeout=12)
            req_count += 1
            if r.status_code != 200:
                print(f"  [sort={sort_mode} page={page}] HTTP {r.status_code}")
                break
            data = r.json()
        except Exception as e:
            print(f"  [sort={sort_mode} page={page}] Err: {e}")
            break
            
        results = data.get("results", [])
        if not results:
            break
            
        new_cnt = sum(1 for it in results if add_product(it, f"cat203_{sort_mode}"))
        sort_new += new_cnt
        time.sleep(0.15)
        if len(results) < 24:
            break
            
    print(f"Sort [{sort_mode:10}] -> added {sort_new:4d} new items (Total unique: {len(items):4d}) [reqs: {req_count}]")

print("\n=== 2. HARVESTING INDUSTRIAL VACUUMS (CATEGORY 1540) ===")
ind_new = 0
for page in range(1, 30):
    url = f"https://api.torob.com/v4/base-product/search/?category=1540&page={page}&size=24&sort=popularity&source=next_desktop"
    try:
        r = s.get(url, headers=H, timeout=12)
        req_count += 1
        if r.status_code != 200: break
        data = r.json()
    except Exception:
        break
    results = data.get("results", [])
    if not results: break
    new_cnt = sum(1 for it in results if add_product(it, "cat1540_industrial"))
    ind_new += new_cnt
    time.sleep(0.15)
    if len(results) < 24: break
print(f"Category 1540 (Industrial) -> added {ind_new:4d} new items (Total unique: {len(items):4d}) [reqs: {req_count}]")

print(f"\n=== 3. HARVESTING BRAND SLICES ({len(BRANDS)} BRANDS) ===")
for b_id, b_name in BRANDS:
    b_new = 0
    for page in range(1, 15):
        url = f"https://api.torob.com/v4/base-product/search/?category=203&brand={b_id}&page={page}&size=24&source=next_desktop"
        try:
            r = s.get(url, headers=H, timeout=12)
            req_count += 1
            if r.status_code != 200: break
            data = r.json()
        except Exception:
            break
        results = data.get("results", [])
        if not results: break
        new_cnt = sum(1 for it in results if add_product(it, f"brand_{b_name}"))
        b_new += new_cnt
        time.sleep(0.15)
        if len(results) < 24: break
    if b_new > 0:
        print(f"Brand [{b_name:15}] -> +{b_new:3d} new (Total unique: {len(items):4d})")

print(f"\n=== 4. HARVESTING FORM FACTOR QUERIES ({len(QUERIES)} QUERIES) ===")
for q in QUERIES:
    q_new = 0
    for page in range(1, 8):
        url = f"https://api.torob.com/v4/base-product/search/?q={urllib.parse.quote(q)}&page={page}&size=24&source=next_desktop"
        try:
            r = s.get(url, headers=H, timeout=12)
            req_count += 1
            if r.status_code != 200: break
            data = r.json()
        except Exception:
            break
        results = data.get("results", [])
        if not results: break
        new_cnt = sum(1 for it in results if add_product(it, f"query_{q}"))
        q_new += new_cnt
        time.sleep(0.15)
        if len(results) < 24: break
    if q_new > 0:
        print(f"Query [{q:20}] -> +{q_new:3d} new (Total unique: {len(items):4d})")

print("\n" + "=" * 60)
print(f"HARVEST COMPLETE: {len(items):,} UNIQUE CLEAN VACUUM CLEANERS")
print(f"TOTAL SEARCH REQUESTS: {req_count}")
print("=" * 60)

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
print(f"Saved to {OUT_FILE}")

#!/usr/bin/env python3
"""Crawl + JSON-LD check for site_before/ (port 8821) and site_after/ (port 8822)."""
import json, re, urllib.request, urllib.parse, urllib.error, urllib.robotparser
REQ = {"LocalBusiness": ["name", "address", "telephone"], "Plumber": ["name", "address", "telephone"], "FAQPage": ["mainEntity"]}
BOTS = ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended"]
def get(u):
    try:
        with urllib.request.urlopen(u, timeout=5) as r: return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e: return e.code, ""
def rp(txt):
    r = urllib.robotparser.RobotFileParser(); r.parse(txt.splitlines()); return r
def site(base):
    seen, todo, broken, canon, ok, err = set(), ["/index.html"], [], 0, 0, []
    while todo:
        p = todo.pop()
        if p in seen: continue
        seen.add(p); st, html = get(base + p)
        if st != 200: broken.append(p); continue
        if not p.endswith(".html"): continue
        canon += bool(re.search(r'rel=["\']canonical', html))
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try: data = json.loads(blk)
            except Exception: err.append(f"{p}: invalid JSON"); continue
            for it in (data if isinstance(data, list) else data.get("@graph", [data])):
                t = it.get("@type"); t = t[0] if isinstance(t, list) else t
                miss = [k for k in REQ.get(t, []) if k not in it]
                if miss: err.append(f"{p}: {t} missing {miss}")
                else: ok += 1
        for h in re.findall(r'href=["\']([^"\'#]+)', html):
            if not h.startswith(("http", "mailto", "tel")): todo.append(urllib.parse.urljoin(p, h))
    rst, robots = get(base + "/robots.txt"); sst, smap = get(base + "/sitemap.xml"); lst, llms = get(base + "/llms.txt")
    sm = {urllib.parse.urlparse(u).path for u in re.findall(r"<loc>(.*?)</loc>", smap)}
    links = re.findall(r"\]\(([^)]+)\)", llms); bad = [l for l in links if get(base + urllib.parse.urlparse(l).path)[0] != 200]
    pages = sorted(x for x in seen if x.endswith(".html") and x not in broken)
    return {"pages_found": len(pages), "broken_links": broken, "pages_with_canonical": canon, "jsonld_items_valid": ok, "jsonld_errors": err,
            "ai_crawlers_allowed": {b: rp(robots).can_fetch(b, "/") for b in BOTS} if rst == 200 else "no robots.txt",
            "sitemap_urls": len(sm) if sst == 200 else "no sitemap",
            "crawled_not_in_sitemap": [p for p in pages if sst == 200 and p not in sm and p.replace("index.html", "") not in sm],
            "llms_txt": f"present, title={llms.startswith('# ')}, links {len(links)-len(bad)}/{len(links)} resolve" if lst == 200 else "missing"}
out = {"before": site("http://localhost:8821"), "after": site("http://localhost:8822")}
json.dump(out, open(__file__.rsplit("/", 1)[0] + "/crawl-schema.json", "w"), indent=1); print(json.dumps(out, indent=1))

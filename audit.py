"""Deterministic SEO + GEO audit for a small static site (standard library only).

Usage: python samples/g1_seo_geo/audit.py <site_folder>
Prints a PASS/FAIL table and a score; writes out/report_<name>.md
(site_before -> report_before.md, site_after -> report_after.md).

Rules are fixed and checkable by code. They are good-practice checks, not a
prediction of rankings or AI citations. The NAP name/address patterns are written
for this sample business (Larkspur Lane Plumbing); change them for a real client.
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

AI_BOTS = ["Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ClaudeBot", "PerplexityBot", "Google-Extended"]
TITLE_RANGE = (30, 60)
DESC_RANGE = (70, 160)
MAX_ANSWER_WORDS = 60
MIN_FAQ = 5

PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}")
NAME_RE = re.compile(r"Larkspur\s+(?:Lane\s+)?Plumb(?:ing|ers)(?:\s+Co\.?)?")
ADDR_RE = re.compile(r"\b\d{1,4} [A-Z][a-z]+ (?:Street|St\.?|Road|Rd\.?|Avenue|Ave\.?)(?=[\s,<]|$)")

# (id, why it matters in one line, scope)
CHECKS = [
    ("title_present", "Every page has a <title>", "page"),
    ("title_length", f"Title is {TITLE_RANGE[0]}-{TITLE_RANGE[1]} characters", "page"),
    ("title_unique", "No two pages share a title", "site"),
    ("desc_present", "Every page has a meta description", "page"),
    ("desc_length", f"Description is {DESC_RANGE[0]}-{DESC_RANGE[1]} characters", "page"),
    ("desc_unique", "No two pages share a description", "site"),
    ("one_h1", "Exactly one H1 per page", "page"),
    ("img_alt", "Every image has non-empty alt text", "page"),
    ("canonical", "Absolute https canonical URL, same host everywhere", "page"),
    ("lang_viewport", "html lang attribute and mobile viewport tag", "page"),
    ("date_author", "Page shows a dated <time> and an author meta tag", "page"),
    ("jsonld_valid", "Page has JSON-LD and it parses", "page"),
    ("schema_localbusiness", "Home page has LocalBusiness schema with name, phone, address", "site"),
    ("schema_faqpage", "FAQ page has FAQPage schema matching the visible questions", "site"),
    ("nap_consistent", "One business name, one phone, one street address on all pages", "site"),
    ("faq_answer_first", f"FAQ has {MIN_FAQ}+ questions, each with an answer of {MAX_ANSWER_WORDS} words or fewer", "site"),
    ("sitemap", "sitemap.xml lists every page and robots.txt points to it", "site"),
    ("robots_ai", "robots.txt does not block search and AI crawlers", "site"),
    ("llms_txt", "llms.txt present (proposed convention, ranking effect unproven)", "site"),
]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.meta = {}
        self.canonical = None
        self.h1 = 0
        self.imgs = []
        self.ld = []
        self.times = 0
        self.lang = None
        self.viewport = False
        self.blocks = []  # (tag, text) for h1-h6 and p
        self.text = []
        self._cur = None
        self._buf = []
        self._script = None
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
            self.title = ""
        elif tag == "meta":
            n = (a.get("name") or "").lower()
            if n:
                self.meta[n] = a.get("content") or ""
            if n == "viewport":
                self.viewport = True
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href")
        elif tag == "img":
            self.imgs.append(a.get("alt"))
        elif tag == "time" and a.get("datetime"):
            self.times += 1
        elif tag == "script":
            self._script = "" if (a.get("type") or "") == "application/ld+json" else None
            self._skip = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self._cur, self._buf = tag, []
            if tag == "h1":
                self.h1 += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            if self._script is not None:
                self.ld.append(self._script)
            self._script = None
            self._skip = False
        elif tag == self._cur:
            self.blocks.append((tag, " ".join("".join(self._buf).split())))
            self._cur = None

    def handle_data(self, d):
        if self._in_title and self.title is not None:
            self.title += d
        elif self._script is not None:
            self._script += d
        elif getattr(self, "_skip", False):
            return
        else:
            self.text.append(d)
            if self._cur:
                self._buf.append(d)


def parse_ld(p):
    """Return (ok, list_of_schema_objects)."""
    objs = []
    if not p.ld:
        return False, objs
    for raw in p.ld:
        try:
            data = json.loads(raw)
        except ValueError:
            return False, objs
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        objs.extend(i for i in items if isinstance(i, dict))
    return True, objs


def types_of(o):
    t = o.get("@type", [])
    return t if isinstance(t, list) else [t]


def robots_blocked(text, bot):
    groups, agents, rules, last_rule = [], [], [], False
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if ":" not in line:
            continue
        k, v = (s.strip() for s in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if last_rule:
                groups.append((agents, rules))
                agents, rules, last_rule = [], [], False
            agents.append(v.lower())
        elif k in ("allow", "disallow"):
            rules.append((k, v))
            last_rule = True
    groups.append((agents, rules))
    pick = [g for g in groups if bot.lower() in g[0]] or [g for g in groups if "*" in g[0]]
    return any(k == "disallow" and v == "/" for g in pick for k, v in g[1])


def audit(site):
    site = Path(site)
    files = sorted(site.glob("*.html"))
    pages = {}
    for f in files:
        p = PageParser()
        p.feed(f.read_text(encoding="utf-8"))
        pages[f.name] = p
    results = {c[0]: [] for c in CHECKS}  # id -> list of (ok, where, detail)

    def add(cid, ok, where, detail=""):
        results[cid].append((ok, where, detail))

    for name, p in pages.items():
        t = (p.title or "").strip()
        add("title_present", bool(t), name, "missing" if not t else "")
        if t:
            add("title_length", TITLE_RANGE[0] <= len(t) <= TITLE_RANGE[1], name, f"{len(t)} chars")
        else:
            add("title_length", False, name, "no title")
        d = p.meta.get("description", "").strip()
        add("desc_present", bool(d), name, "missing" if not d else "")
        if d:
            add("desc_length", DESC_RANGE[0] <= len(d) <= DESC_RANGE[1], name, f"{len(d)} chars")
        else:
            add("desc_length", False, name, "no description")
        add("one_h1", p.h1 == 1, name, f"{p.h1} H1")
        bad = sum(1 for a in p.imgs if not (a or "").strip())
        add("img_alt", bad == 0, name, f"{bad} of {len(p.imgs)} images without alt" if bad else "")
        c = p.canonical or ""
        u = urlparse(c)
        add("canonical", bool(c) and u.scheme == "https" and bool(u.netloc), name, "missing or not absolute https" if not (c and u.scheme == "https") else "")
        add("lang_viewport", bool(p.lang) and p.viewport, name, "no lang" if not p.lang else ("no viewport" if not p.viewport else ""))
        add("date_author", p.times > 0 and bool(p.meta.get("author")), name, "no date" if not p.times else ("no author" if not p.meta.get("author") else ""))
        ok, _ = parse_ld(p)
        add("jsonld_valid", ok, name, "none or invalid" if not ok else "")

    hosts = {urlparse(p.canonical or "").netloc for p in pages.values() if p.canonical}
    if len(hosts) > 1:
        add("canonical", False, "site", "canonical hosts differ")

    def dup(values):
        seen, d = {}, set()
        for n, v in values:
            if v:
                if v in seen:
                    d.update((n, seen[v]))
                seen[v] = n
        return sorted(d)

    dt = dup((n, (p.title or "").strip()) for n, p in pages.items())
    add("title_unique", not dt, "site", "duplicates: " + ", ".join(dt) if dt else "")
    dd = dup((n, p.meta.get("description", "").strip()) for n, p in pages.items())
    add("desc_unique", not dd, "site", "duplicates: " + ", ".join(dd) if dd else "")

    # schema (site-level)
    home = pages.get("index.html")
    ok = False
    if home:
        for o in parse_ld(home)[1]:
            if any(t in ("LocalBusiness", "Plumber", "Store", "Bakery") or t.endswith("Business") for t in types_of(o)):
                ok = bool(o.get("name") and o.get("telephone") and o.get("address"))
    add("schema_localbusiness", ok, "index.html", "" if ok else "missing or incomplete")
    faq = pages.get("faq.html")
    ok, why = False, "no FAQPage schema"
    if faq:
        visible = {t for tag, t in faq.blocks if tag == "h3"}
        for o in parse_ld(faq)[1]:
            if "FAQPage" in types_of(o):
                qs = [q.get("name", "") for q in o.get("mainEntity", [])]
                ok = len(qs) >= MIN_FAQ and all(q in visible for q in qs)
                why = "" if ok else "schema questions do not match visible questions"
    add("schema_faqpage", ok, "faq.html", why)

    # NAP
    alltext = " ".join(" ".join(p.text) for p in pages.values())
    per = {}
    for n, p in pages.items():
        tx = " ".join(p.text)
        per[n] = (set(NAME_RE.findall(tx)), {re.sub(r"\D", "", x) for x in PHONE_RE.findall(tx)}, set(ADDR_RE.findall(tx)))
    names = set().union(*(v[0] for v in per.values())) if per else set()
    phones = set().union(*(v[1] for v in per.values())) if per else set()
    addrs = set().union(*(v[2] for v in per.values())) if per else set()
    problems = [f"{label}: {len(s)} variants" for label, s in (("name", names), ("phone", phones), ("address", addrs)) if len(s) != 1]
    add("nap_consistent", not problems, "site", "; ".join(problems))

    # FAQ answer-first
    ok, why = False, "no faq.html"
    if faq:
        qa = []
        for i, (tag, t) in enumerate(faq.blocks):
            if tag == "h3" and i + 1 < len(faq.blocks) and faq.blocks[i + 1][0] == "p":
                qa.append((t, len(faq.blocks[i + 1][1].split())))
        long_ = [q for q, n in qa if n > MAX_ANSWER_WORDS]
        ok = len(qa) >= MIN_FAQ and not long_
        why = "" if ok else f"{len(qa)} Q&A pairs; {len(long_)} answers over {MAX_ANSWER_WORDS} words"
    add("faq_answer_first", ok, "faq.html", why)

    # site files
    robots = site / "robots.txt"
    rtxt = robots.read_text(encoding="utf-8") if robots.exists() else ""
    sm = site / "sitemap.xml"
    ok, why = False, "sitemap.xml missing"
    if sm.exists():
        try:
            locs = re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8"))
            paths = {urlparse(l).path or "/" for l in locs}
            expected = {"/" if n == "index.html" else "/" + n for n in pages}
            missing = sorted(expected - paths)
            ref = re.search(r"(?im)^\s*sitemap:\s*\S+sitemap\.xml", rtxt) is not None
            ok = not missing and ref
            why = "" if ok else ("pages missing: " + ", ".join(missing) if missing else "robots.txt has no Sitemap line")
        except OSError:
            pass
    add("sitemap", ok, "sitemap.xml", why)
    if not robots.exists():
        add("robots_ai", False, "robots.txt", "robots.txt missing")
    else:
        blocked = [b for b in AI_BOTS if robots_blocked(rtxt, b)]
        add("robots_ai", not blocked, "robots.txt", "blocks: " + ", ".join(blocked) if blocked else "")
    ll = site / "llms.txt"
    ok = ll.exists() and ll.read_text(encoding="utf-8").lstrip().startswith("# ") and "](" in ll.read_text(encoding="utf-8")
    add("llms_txt", bool(ok), "llms.txt", "" if ok else "missing or malformed")
    return results


def summarize(results):
    rows = []
    for cid, desc, scope in CHECKS:
        r = results[cid]
        fails = [(w, d) for ok, w, d in r if not ok]
        rows.append((cid, desc, not fails, "; ".join(f"{w}: {d}" if d else w for w, d in fails)))
    passed = sum(1 for r in rows if r[2])
    return rows, passed, len(rows)


def render(name, rows, passed, total):
    md = [f"# SEO + GEO audit: {name}", "", f"**Score: {passed}/{total} checks passed ({round(100 * passed / total)}%)**", "",
          "| Check | Rule | Result | Where it fails |", "|---|---|---|---|"]
    for cid, desc, ok, det in rows:
        md.append(f"| {cid} | {desc} | {'PASS' if ok else 'FAIL'} | {det} |")
    md += ["", "These are good-practice checks. A high score does not guarantee rankings or AI citations."]
    return "\n".join(md) + "\n"


def run(site):
    site = Path(site)
    rows, passed, total = summarize(audit(site))
    label = site.name.replace("site_", "") or site.name
    out = Path(__file__).parent / "out"
    out.mkdir(exist_ok=True)
    (out / f"report_{label}.md").write_text(render(site.name, rows, passed, total), encoding="utf-8")
    return rows, passed, total, label


def main(argv):
    if len(argv) != 2:
        print("usage: python audit.py <site_folder>")
        return 2
    rows, passed, total, label = run(argv[1])
    w = max(len(r[0]) for r in rows)
    print(f"{'CHECK'.ljust(w)}  RESULT  DETAIL")
    for cid, _, ok, det in rows:
        print(f"{cid.ljust(w)}  {'PASS' if ok else 'FAIL'}    {det}")
    print(f"\nScore: {passed}/{total} ({round(100 * passed / total)}%)  ->  out/report_{label}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

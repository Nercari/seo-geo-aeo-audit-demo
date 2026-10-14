import csv
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import audit

BEFORE = ROOT / "demo" / "site_before"
AFTER = ROOT / "demo" / "site_after"


class AuditV2(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "a" / "b"

    def tearDown(self):
        self.tmp.cleanup()

    def test_core_score_unchanged(self):
        self.assertEqual(audit.run(BEFORE, out=self.out)[1:3], (2, 19))
        self.assertEqual(audit.run(AFTER, out=self.out)[1:3], (19, 19))

    def test_every_check_has_tier_and_fix(self):
        for cid, _, _ in audit.ALL_CHECKS:
            tier, fix = audit.TIERS[cid]
            self.assertIn(tier, audit.TIER_ORDER)
            self.assertTrue(fix and "\n" not in fix)

    def test_health_counts_errors_only(self):
        r = audit.audit(AFTER)
        self.assertEqual(audit.health(r, audit.ALL_CHECKS), 100)
        r["llms_txt"] = [(False, "llms.txt", "x")]
        self.assertEqual(audit.health(r, audit.ALL_CHECKS), 100)
        r["canonical"] = [(False, "a.html", "x")]
        self.assertLess(audit.health(r, audit.ALL_CHECKS), 100)

    def test_exports_sorted_and_stable(self):
        audit.run(BEFORE, out=self.out)
        rows = list(csv.DictReader(open(self.out / "findings_before.csv")))
        self.assertEqual(list(rows[0].keys()), ["url", "check", "tier", "issue", "fix"])
        keys = [(audit.TIER_ORDER[r["tier"]], r["check"], r["url"], r["issue"]) for r in rows]
        self.assertEqual(keys, sorted(keys))
        first = (self.out / "findings_before.json").read_text()
        audit.run(BEFORE, out=self.out)
        self.assertEqual(first, (self.out / "findings_before.json").read_text())

    def test_compare(self):
        audit.run(BEFORE, out=self.out)
        prev = json.loads((self.out / "findings_before.json").read_text())
        cur = audit.findings(audit.audit(AFTER), audit.ALL_CHECKS)
        new, fixed, same = audit.compare(prev, cur)
        self.assertEqual(len(fixed), len(prev) - len(same))
        self.assertEqual(audit.compare(prev, prev), ([], [], prev and sorted(prev, key=lambda f: (f["url"], f["check"], f["issue"]))))

    def test_bot_table_separates_kinds(self):
        t = dict(((b, k), a) for k, b, a in audit.bot_table(BEFORE))
        self.assertEqual(t[("GPTBot", "training")], "blocked")
        self.assertEqual(t[("Googlebot", "search/answer")], "allowed")
        self.assertTrue(all(a == "allowed" for _, _, a in audit.bot_table(AFTER)))

    def test_report_sections(self):
        audit.run(BEFORE, out=self.out)
        md = (self.out / "report_before.md").read_text()
        self.assertIn("## Readiness (we control)", md)
        self.assertIn("## Visibility (measured, not promised)", md)
        self.assertIn("Health:", md)


PAGE = """<html lang="en"><head><title>T</title>{meta}
<script type="application/ld+json">{ld}</script></head><body><p>{body}</p></body></html>"""


class ExtraChecks(unittest.TestCase):
    def site(self, meta="", ld='{"@type":"Plumber","name":"Acme Pipes","telephone":"+1-555-010-0142"}',
             body="Acme Pipes (555) 010-0142", robots="root"):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "index.html").write_text(PAGE.format(meta=meta, ld=ld, body=body))
        if robots == "root":
            (d / "robots.txt").write_text("User-agent: *\nAllow: /\n")
        elif robots == "nested":
            (d / "sub").mkdir()
            (d / "sub" / "robots.txt").write_text("User-agent: *\nAllow: /\n")
        return {f["check"]: f for f in audit.findings(audit.audit(d), audit.EXTRA_CHECKS)}

    def test_clean(self):
        self.assertEqual(self.site(), {})

    def test_robots_not_at_root(self):
        f = self.site(robots="nested")["robots_root"]
        self.assertEqual(f["tier"], "Warn")
        self.assertIn("sub/robots.txt", f["issue"])
        self.assertIn("robots_root", self.site(robots=None))

    def test_jsonld_value_not_visible(self):
        f = self.site(body="Acme Pipes")["jsonld_visible"]
        self.assertIn("telephone", f["issue"])
        self.assertNotIn("name=", f["issue"])

    def test_snippet_and_noindex(self):
        r = self.site(meta='<meta name="robots" content="noindex, max-snippet:0">')
        self.assertEqual(r["noindex"]["tier"], "Error")
        self.assertIn("max-snippet:0", r["snippet_controls"]["issue"])
        self.assertIn("nosnippet", self.site(meta='<meta name="googlebot" content="nosnippet">')["snippet_controls"]["issue"])

    def test_extras_not_in_core_score(self):
        self.assertEqual(len(audit.CHECKS), 19)
        self.assertEqual(len(audit.ALL_CHECKS), 23)


class NapAndSitemap(unittest.TestCase):
    PAGE = ('<html lang="en"><head><title>{t}</title><link rel="canonical" href="{c}">{h}</head>'
            '<body><h1>{t}</h1><p>{b}</p></body></html>')

    def make(self, pages, sitemap=None, home_head=""):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        for n, (canon, body) in pages.items():
            (d / n).write_text(self.PAGE.format(t=n, c=canon, h=home_head if n == "index.html" else "", b=body), encoding="utf-8")
        (d / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://x.example/sub/sitemap.xml\n", encoding="utf-8")
        if sitemap is not None:
            locs = "".join(f"<url><loc>{u}</loc></url>" for u in sitemap)
            (d / "sitemap.xml").write_text(f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{locs}</urlset>', encoding="utf-8")
        return audit.audit(d)

    NAP = "Call Bramble Bakery at 555-123-4567, 12 Oak Street, Ashby."
    LD = '<script type="application/ld+json">{"@type": "Bakery", "name": "Bramble Bakery"}</script>'

    def test_nap_uses_site_declared_name_not_hardcoded(self):
        r = self.make({"index.html": ("https://x.example/", self.NAP), "a.html": ("https://x.example/a.html", self.NAP)}, home_head=self.LD)
        self.assertTrue(r["nap_consistent"][0][0], r["nap_consistent"])
        self.assertNotIn("Larkspur", Path(audit.__file__).read_text(encoding="utf-8"))
        self.assertFalse(hasattr(audit, "NAME_RE"))

    def test_nap_declared_name_in_ordinary_text_is_not_a_variant(self):
        bodies = ["Visit Bramble Bakery.", "Bramble Bakery's bread", "<b>Bramble</b> Bakery", "Bramble\u00a0Bakery",
                  "</p><h2>Bramble Bakery Opening Hours</h2><p>"]
        for b in bodies:
            with self.subTest(b=b):
                r = self.make({"index.html": ("https://x.example/", self.NAP + " " + b)}, home_head=self.LD)
                self.assertTrue(r["nap_consistent"][0][0], r["nap_consistent"])

    def test_nap_suffix_variant_flagged(self):
        r = self.make({"index.html": ("https://x.example/", self.NAP + " Bramble Bakery Co. since 1990")}, home_head=self.LD)
        ok, _, why = r["nap_consistent"][0]
        self.assertFalse(ok)
        self.assertIn("Bramble Bakery Co.", why)

    def test_nap_prefers_localbusiness_over_organization(self):
        ld = ('<script type="application/ld+json">{"@graph": [{"@type": "Organization", "name": "Agency Ltd"},'
              ' {"@type": "Bakery", "name": "Bramble Bakery"}]}</script>')
        self.assertTrue(self.make({"index.html": ("https://x.example/", self.NAP)}, home_head=ld)["nap_consistent"][0][0])

    def test_nap_name_starting_with_the(self):
        ld = '<script type="application/ld+json">{"@type": "Bakery", "name": "The Copper Kettle"}</script>'
        body = "The Copper Kettle at 555-123-4567, 12 Oak Street, Ashby. The bread is fresh."
        self.assertTrue(self.make({"index.html": ("https://x.example/", body)}, home_head=ld)["nap_consistent"][0][0])

    def test_nap_og_site_name_and_variant_flagged(self):
        og = '<meta property="og:site_name" content="Bramble Bakery (demo)">'
        r = self.make({"index.html": ("https://x.example/", self.NAP),
                       "a.html": ("https://x.example/a.html", self.NAP.replace("Bramble Bakery", "Bramble Bakers Co."))}, home_head=og)
        ok, _, why = r["nap_consistent"][0]
        self.assertFalse(ok)
        self.assertIn("Bramble Bakers Co.", why)

    def test_nap_old_demo_name_ignored(self):
        r = self.make({"index.html": ("https://x.example/", self.NAP + " Larkspur Plumbing")}, home_head=self.LD)
        self.assertTrue(r["nap_consistent"][0][0])

    def test_sitemap_absolute_urls_in_subfolder(self):
        base = "https://x.example/sub/"
        r = self.make({"index.html": (base, self.NAP), "a.html": (base + "a.html", self.NAP), "404.html": (base + "404.html", "")},
                      sitemap=[base, base + "a.html"])
        self.assertTrue(r["sitemap"][0][0], r["sitemap"])

    def test_sitemap_subfolder_still_catches_missing_page(self):
        base = "https://x.example/sub/"
        r = self.make({"index.html": (base, self.NAP), "a.html": (base + "a.html", self.NAP)}, sitemap=[base])
        ok, _, why = r["sitemap"][0]
        self.assertFalse(ok)
        self.assertIn("/sub/a.html", why)

    def test_sitemap_no_canonical_uses_sitemap_folder_and_survives_relative_locs(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        for n in ("index.html", "a.html"):
            (d / n).write_text("<html><body><p>x</p></body></html>", encoding="utf-8")
        (d / "robots.txt").write_text("Sitemap: https://x.example/sub/sitemap.xml\n", encoding="utf-8")
        sm = d / "sitemap.xml"
        sm.write_text("<urlset><url><loc>https://x.example/sub/</loc></url><url><loc>https://x.example/sub/a.html</loc></url></urlset>", encoding="utf-8")
        self.assertTrue(audit.audit(d)["sitemap"][0][0])
        sm.write_text("<urlset><url><loc>a.html</loc></url><url><loc>https://x.example/sub/</loc></url></urlset>", encoding="utf-8")
        self.assertFalse(audit.audit(d)["sitemap"][0][0])  # fails the check, does not crash

    def test_sitemap_other_host_fails_and_whitespace_ok(self):
        base = "https://x.example/sub/"
        pages = {"index.html": (base, self.NAP), "a.html": (base + "a.html", self.NAP)}
        self.assertFalse(self.make(pages, sitemap=["https://staging.example/sub/", "https://staging.example/sub/a.html"])["sitemap"][0][0])
        self.assertTrue(self.make(pages, sitemap=["\n  " + base + "  \n", base + "a.html"])["sitemap"][0][0])

    def test_sitemap_canonical_without_trailing_slash(self):
        r = self.make({"index.html": ("https://x.example/sub", self.NAP), "a.html": ("https://x.example/sub/a.html", self.NAP)},
                      sitemap=["https://x.example/sub/", "https://x.example/sub/a.html"])
        self.assertTrue(r["sitemap"][0][0], r["sitemap"])

    def test_robots_root_warns_for_subfolder_site(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "index.html").write_text(self.PAGE.format(t="i", c="https://x.example/sub/", h="", b=""), encoding="utf-8")
        (d / "robots.txt").write_text("User-agent: *\n", encoding="utf-8")
        res = {}
        pages = {}
        for f in sorted(d.glob("*.html")):
            pp = audit.PageParser(); pp.feed(f.read_text(encoding="utf-8")); pages[f.name] = pp
        audit.extra_checks(d, pages, res)
        ok, _, why = res["robots_root"][0]
        self.assertFalse(ok)
        self.assertIn("/sub/", why)

    def test_sitemap_wrong_folder_fails(self):
        base = "https://x.example/sub/"
        r = self.make({"index.html": (base, self.NAP), "a.html": (base + "a.html", self.NAP)},
                      sitemap=["https://x.example/", "https://x.example/a.html"])
        self.assertFalse(r["sitemap"][0][0])


if __name__ == "__main__":
    unittest.main()

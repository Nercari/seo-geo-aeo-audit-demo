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
        with open(self.out / "findings_before.csv", encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
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

    def ld(self, name="Bramble Bakery", phone="555-123-4567", street="12 Oak Street", typ='"Bakery"'):
        return ('<script type="application/ld+json">{"@type": %s, "name": "%s", "telephone": "%s", '
                '"address": {"@type": "PostalAddress", "streetAddress": "%s"}}</script>' % (typ, name, phone, street))

    def nap(self, pages):
        """pages: {file: (head, body)}"""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        for n, (head, body) in pages.items():
            (d / n).write_text(self.PAGE.format(t=n, c="https://x.example/" + n, h=head, b=body), encoding="utf-8")
        return audit.audit(d)["nap_consistent"][0]

    def test_nap_uses_site_declared_name_not_hardcoded(self):
        r = self.make({"index.html": ("https://x.example/", self.NAP), "a.html": ("https://x.example/a.html", self.NAP)}, home_head=self.LD)
        self.assertTrue(r["nap_consistent"][0][0], r["nap_consistent"])
        # behaviour, not layout: other names, phones and streets written in prose never change the result
        prose = " Larkspur Plumbing, Bramble Bakers Co., call 555-999-0000, 99 Elm Street."
        ok, _, why = self.nap({"index.html": (self.ld(), self.NAP + prose), "a.html": (self.ld(), prose)})
        self.assertTrue(ok, why)

    def test_nap_body_text_never_scanned(self):
        bodies = ["Visit Bramble Bakery.", "Bramble Bakery's bread", "<b>Bramble</b> Bakery", "Bramble\u00a0Bakery",
                  "</p><h2>Bramble Bakery Opening Hours</h2><p>", "Bramble Bakery Co. since 1990", "Bramble Bakers Co.",
                  "Larkspur Plumbing, call 555-999-0000 at 99 Elm Street"]
        for b in bodies:
            with self.subTest(b=b):
                ok, _, why = self.nap({"index.html": (self.ld(), self.NAP + " " + b)})
                self.assertTrue(ok, why)

    def test_nap_rev4_blocker_names(self):
        cases = [("Bread and Butter Bakery", "Bread and Butter Bakery bakes daily. Bread is good."),
                 ("House of Bread", "House of Bread. The House is open."),
                 ("Studio 54 Salon", "Studio 54 Salon, Studio hours vary."),
                 ("Dr. Smith's Dental", "Dr. Smith's Dental. Dr. Smith is in."),
                 ("Ashby Plumbing", "Ashby Plumbing, 12 Oak Street, Ashby."),
                 ("Main Street Bakery", "Main Street Bakery at 12 Main Street."),
                 ("Quillmere Plumbing", "</p><a>Quillmere Plumbing</a><a>Services</a><h2>Company history</h2><p>")]
        for name, body in cases:
            with self.subTest(name=name):
                ok, _, why = self.nap({"index.html": (self.ld(name=name), body),
                                       "a.html": (self.ld(name=name), body)})
                self.assertTrue(ok, why)

    def test_nap_normalisation(self):
        ok, _, why = self.nap({"index.html": (self.ld(name="Dr. Smith's Dental", phone="+1 (555) 123-4567"), ""),
                               "a.html": (self.ld(name="dr smith\u2019s\u00a0 DENTAL", phone="555.123.4567", street="12 oak street."), "")})
        self.assertTrue(ok, why)

    def test_nap_declared_mismatch_flagged(self):
        for kw, label in (({"name": "Bramble Bakers Co."}, "name"), ({"phone": "555-123-9999"}, "phone"),
                          ({"street": "14 Mill Street"}, "street address")):
            with self.subTest(label=label):
                ok, _, why = self.nap({"index.html": (self.ld(), ""), "a.html": (self.ld(**kw), "")})
                self.assertFalse(ok)
                self.assertIn(label + " differs", why)
                self.assertIn("a.html", why)

    def test_nap_og_site_name_tagline_and_mismatch(self):
        og = '<meta property="og:site_name" content="%s">'
        ok, _, why = self.nap({"index.html": (self.ld() + og % "Bramble Bakery | Fresh bread daily", "")})
        self.assertTrue(ok, why)
        ok, _, why = self.nap({"index.html": (og % "Bramble Bakery (demo)", "")})
        self.assertTrue(ok, why)
        ok, _, why = self.nap({"index.html": (og % "Bramble Bakery: fresh bread", ""), "a.html": (og % "Bramble Bakers", "")})
        self.assertFalse(ok)
        self.assertIn("Bramble Bakers", why)
        # og:site_name is a fallback only: a short brand next to a declared LocalBusiness name is not a mismatch
        ok, _, why = self.nap({"index.html": (self.ld(), ""), "a.html": (og % "Bramble", "")})
        self.assertTrue(ok, why)

    def test_nap_prefers_localbusiness_over_organization(self):
        ld = ('<script type="application/ld+json">{"@graph": [{"@type": "Organization", "name": "Agency Ltd"},'
              ' {"@type": "Bakery", "name": "Bramble Bakery"}]}</script>')
        self.assertTrue(self.make({"index.html": ("https://x.example/", self.NAP)}, home_head=ld)["nap_consistent"][0][0])

    def test_nap_no_declared_name_fails(self):
        ok, _, why = self.nap({"index.html": ("", self.NAP)})
        self.assertFalse(ok)
        self.assertIn("declares no business name", why)

    def test_localbusiness_subtypes_and_null_type(self):
        for typ in ('"Dentist"', '"HairSalon"', '"LegalService"', '"RoofingContractor"', '["Thing", "Restaurant"]'):
            with self.subTest(typ=typ):
                ok, _, why = self.nap({"index.html": (self.ld(typ=typ), "")})
                self.assertTrue(ok, why)
        for typ in ("null", '[null, 3]', '{"x": 1}'):
            with self.subTest(typ=typ):
                ok, _, why = self.nap({"index.html": (self.ld(typ=typ), "")})  # must not crash
                self.assertFalse(ok)

    def test_nap_microdata_and_address_element(self):
        md = ('<div itemscope itemtype="https://schema.org/Bakery"><span itemprop="name">Bramble  Bakery</span>'
              '<div itemprop="author" itemscope itemtype="https://schema.org/Person"><span itemprop="name">Ann Lee</span></div>'
              '<div itemprop="address" itemscope itemtype="https://schema.org/PostalAddress">'
              '<span itemprop="streetAddress">12 Oak Street</span></div><span itemprop="telephone">555 123 4567</span></div>')
        ok, _, why = self.nap({"index.html": (self.ld(), md)})
        self.assertTrue(ok, why)  # the Person's name is not a business name
        ok, _, why = self.nap({"index.html": (self.ld(), md.replace("Bramble  Bakery", "Bramble Cakes"))})
        self.assertFalse(ok)
        good = "</p><address>Bramble Bakery<br>12 Oak Street, Ashby<br>(555) 123-4567</address><p>"
        ok, _, why = self.nap({"index.html": (self.ld(), good)})
        self.assertTrue(ok, why)
        ok, _, why = self.nap({"index.html": (self.ld(), good.replace("4567", "9999"))})
        self.assertFalse(ok)
        ok, _, why = self.nap({"index.html": (self.ld(), good.replace("12 Oak", "14 Mill"))})
        self.assertFalse(ok)
        self.assertIn("<address>", why)

    def test_plain_service_and_online_store_are_not_businesses(self):
        svc = ('<script type="application/ld+json">[{"@type": "Plumber", "name": "Bramble Bakery", "telephone": "555-123-4567",'
               ' "address": {"@type": "PostalAddress", "streetAddress": "12 Oak Street"}},'
               ' {"@type": "Service", "name": "Drain cleaning", "provider": {"@type": "Plumber", "name": "Bramble Bakery"}},'
               ' {"@type": "OnlineStore", "name": "Bramble Shop Online"}]</script>')
        ok, _, why = self.nap({"index.html": (svc, ""),
                               "a.html": ('<script type="application/ld+json">{"@type": "Service", "name": "Leak repair"}</script>', "")})
        self.assertTrue(ok, why)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "index.html").write_text(self.PAGE.format(t="i", c="https://x.example/", h=svc, b=""), encoding="utf-8")
        self.assertTrue(audit.audit(d)["schema_localbusiness"][0][0])  # a later Service does not override the Plumber
        for typ in ('"Service"', '"OnlineStore"', '"OnlineBusiness"'):
            self.assertFalse(audit.is_local_business({"@type": typ.strip('"')}), typ)
        for typ in ("ProfessionalService", "FinancialService", "EmergencyService", "LegalService", "ShoeStore"):
            self.assertTrue(audit.is_local_business({"@type": typ}), typ)

    def test_street_needs_whole_words(self):
        good = "</p><address>Bramble Bakery<br>12 Oak Street<br>(555) 123-4567</address><p>"
        ok, _, why = self.nap({"index.html": (self.ld(), good.replace("12 Oak", "112 Oak"))})
        self.assertFalse(ok)
        ok, _, why = self.nap({"index.html": (self.ld(), good.replace("Street", "Streets"))})
        self.assertFalse(ok)

    def test_author_byline_address_ignored(self):
        bylines = ['</p><article><address>By <a href="mailto:a@b.example">Ann Lee</a>, 1 Elm Road, 555-999-0000</address></article><p>',
                   '</p><address>Written by Ann Lee</address><p>',
                   '</p><div itemscope itemtype="https://schema.org/Person"><address>Ann Lee, 1 Elm Road, 555-999-0000</address></div><p>']
        for b in bylines:
            with self.subTest(b=b):
                ok, _, why = self.nap({"index.html": (self.ld(), b)})
                self.assertTrue(ok, why)

    def test_address_phone_split_by_inline_markup(self):
        ok, _, why = self.nap({"index.html": (self.ld(), "</p><address>12 Oak Street, (555) 123-<span>9999</span></address><p>")})
        self.assertFalse(ok)
        self.assertIn("phone differs", why)

    def test_non_string_jsonld_values_skipped(self):
        ld = ('<script type="application/ld+json">{"@type": "Bakery", "name": ["Bramble Bakery", "BB"], "telephone": 5551234567,'
              ' "address": [{"@type": "PostalAddress", "streetAddress": "12 Oak Street"}]}</script>')
        ok, _, why = self.nap({"index.html": (ld, ""), "a.html": (self.ld(), "")})
        self.assertTrue(ok, why)

    def test_employee_telephone_and_nested_itemprop(self):
        md = ('<div itemscope itemtype="https://schema.org/Bakery"><span itemprop="name"><span>Bramble</span> Bakery</span>'
              '<span itemprop="telephone">555 123 4567</span>'
              '<div itemprop="employee" itemscope itemtype="https://schema.org/Person"><span itemprop="name">Ann</span>'
              '<span itemprop="telephone">555 999 0000</span>'
              '<div itemprop="address" itemscope itemtype="https://schema.org/PostalAddress"><span itemprop="streetAddress">1 Elm Road</span></div></div>'
              '<div itemprop="address" itemscope itemtype="https://schema.org/PostalAddress"><span itemprop="streetAddress">12 Oak Street</span></div></div>')
        ok, _, why = self.nap({"index.html": (self.ld(), md)})
        self.assertTrue(ok, why)

    def test_nap_old_demo_name_ignored(self):
        r = self.make({"index.html": ("https://x.example/", self.NAP + " Larkspur Plumbing")}, home_head=self.LD)
        self.assertTrue(r["nap_consistent"][0][0])

    def test_extra_checks_survive_non_utf8_sitemap(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "index.html").write_text(self.PAGE.format(t="i", c="https://x.example/", h=self.LD, b=""), encoding="utf-8")
        (d / "sitemap.xml").write_bytes(b"<urlset><loc>https://x.example/\xff\xfe</loc></urlset>")
        r = audit.audit(d)
        self.assertFalse(r["sitemap"][0][0])
        self.assertIn("unreadable", r["sitemap"][0][2])

    def test_sitemap_skips_none_directive_and_decodes_paths(self):
        base = "https://x.example/"
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "index.html").write_text(self.PAGE.format(t="i", c=base, h="", b=""), encoding="utf-8")
        (d / "about us.html").write_text(self.PAGE.format(t="a", c=base + "about%20us.html", h="", b=""), encoding="utf-8")
        (d / "hid.html").write_text(self.PAGE.format(t="h", c=base + "hid.html", h='<meta name="robots" content="none">', b=""), encoding="utf-8")
        (d / "robots.txt").write_text("Sitemap: https://x.example/sitemap.xml\n", encoding="utf-8")
        (d / "sitemap.xml").write_text(f"<urlset><loc>{base}</loc><loc>{base}about%20us.html</loc></urlset>", encoding="utf-8")
        r = audit.audit(d)
        self.assertTrue(r["sitemap"][0][0], r["sitemap"])

    def test_sitemap_relative_canonical_does_not_flag_host(self):
        r = self.make({"index.html": ("/", self.NAP), "a.html": ("/a.html", self.NAP)},
                      sitemap=["https://x.example/", "https://x.example/a.html"])
        self.assertNotIn("canonical host", r["sitemap"][0][2])

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

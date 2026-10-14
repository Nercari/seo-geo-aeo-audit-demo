import csv
import json
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


if __name__ == "__main__":
    unittest.main()

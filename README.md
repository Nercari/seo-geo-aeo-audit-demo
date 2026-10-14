# SEO + GEO + AEO audit demo (with llms.txt) — measured, fictional demo by Nercari

[![checks](https://github.com/Nercari/seo-geo-aeo-audit-demo/actions/workflows/checks.yml/badge.svg)](https://github.com/Nercari/seo-geo-aeo-audit-demo/actions/workflows/checks.yml)
[![Live demo](https://img.shields.io/badge/live%20demo-nercari.github.io-blue)](https://nercari.github.io/seo-geo-aeo-audit-demo/)
[![llms.txt](https://img.shields.io/badge/llms.txt-ready-green)](./llms.txt)

**What a buyer gets:** an audit of technical SEO and AI-answer readiness, the fixes (written or applied), schema markup, `llms.txt`, and a re-audit showing before vs after.

> Fictional demo only. Quillmere Plumbing (Marlowe Falls, OR) is not a real business and is not client work. Numbers below come from reproducible local runs dated **2026-10-14**. No search rankings or AI citations are promised.

## What did the fixes change?

### Local audit (`python3 accept.py`)

| | site_before | site_after |
|---|---|---|
| Checks passing | **2/19** | **19/19** |

### Lighthouse 13.5 (mobile, local server, index.html)

| Category | Before | After |
|---|---|---|
| Performance | 100 | 100 |
| Accessibility | 69 | 96 |
| Best Practices | 96 | 96 |
| SEO | 92 | 100 |

### Schema.org validator (validator.schema.org, all 4 pages)

| | Before | After |
|---|---|---|
| Schema objects found | 0 | 4 |
| Errors | 0 | 0 |
| Types | none | Plumber, FAQPage, Question/Answer, PostalAddress, OpeningHoursSpecification, Organization, Person, WebPage |

### Crawl and AI-answer readiness

| | Before | After |
|---|---|---|
| Pages found / broken links | 4 / 0 | 4 / 0 |
| Pages with canonical | 0/4 | 4/4 |
| AI crawlers allowed (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended) | blocked / missing | allowed |
| `llms.txt` | missing | present |

Reproduce the local audit: `python3 accept.py` (expects `site_after/` to pass 19/19).

## Live demo

[nercari.github.io/seo-geo-aeo-audit-demo](https://nercari.github.io/seo-geo-aeo-audit-demo/) — the full Quillmere Plumbing **after** site (title, meta, schema, sitemap, robots, `llms.txt`, visible fictional-demo banner).

Once indexed, search for **"Quillmere Plumbing"** on Google and Bing; the Nercari demo should be the primary result for that unique name. Indexing usually takes a few days after Search Console / Bing Webmaster submission.

## What's in this repo?

- `site_before/` / `site_after/` — the demo site before and after the fixes
- `audit.py` / `accept.py` — the 19-check auditor used in CI
- `measurements/` — Lighthouse reports and other run artifacts
- `docs/pages/` — the GitHub Pages copy of `site_after` (with Nercari demo labelling)
- `llms.txt` — machine-readable summary for AI crawlers

## FAQ

### Will my site rank #1 for my keywords?
This demo does not claim rankings. It shows measurable on-site checks (audit, Lighthouse, schema, crawlability, `llms.txt`). Ranking depends on competition, links and many other factors outside the audit.

### Is Quillmere Plumbing a real plumber?
No. It is a fictional business in a fictional town (Marlowe Falls, OR), created so the audit and the live demo can be public.

### Can you publish the fixes on my CMS?
Yes, when you grant a CMS login for the fixes you approve. See the matching Fiverr gig FAQ.

## Order / related

**Order an audit:** [Fiverr gig](https://www.fiverr.com/nercari/PLACEHOLDER-seo-geo-aeo) · [Claude skill examples](https://github.com/Nercari/claude-skill-examples) · [Claude Code setup](https://github.com/Nercari/claude-code-setup-example) · [Nercari profile](https://github.com/Nercari/Nercari)

Delivery-only. No video calls, voice or face content.

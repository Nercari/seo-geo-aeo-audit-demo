# SEO + GEO + AEO audit demo (with llms.txt) — demo project by Nercari

**What a buyer gets:** an audit of technical SEO and AI-answer readiness, the fixes (written or applied), schema markup, llms.txt, and a re-audit showing before vs after.

## Results (real runs, 2026-10-14, fictional "Larkspur Plumbing" site)
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
| sitemap.xml | missing | 4 URLs, all crawled pages listed |
| robots.txt lets GPTBot, ClaudeBot, PerplexityBot, Google-Extended fetch `/` | 0/4 | 4/4 |
| llms.txt | missing | present, 3/3 links resolve |
| JSON-LD valid (LocalBusiness/FAQPage required fields) | 0 items | 4 items, 0 errors |

Performance was already high on this small static site, so it didn't move; we report it anyway. No ranking or AI-citation guarantee: these are measurable site checks, not search outcomes.

## Reproduce
```bash
python3 audit.py; python3 accept.py
python3 -m http.server 8821 -d site_before & python3 -m http.server 8822 -d site_after &
npx -y lighthouse http://localhost:8821/index.html --chrome-flags="--headless=new --no-sandbox" --output=json --output=html --output-path=measurements/lighthouse-before
npx -y lighthouse http://localhost:8822/index.html --chrome-flags="--headless=new --no-sandbox" --output=json --output=html --output-path=measurements/lighthouse-after
python3 measurements/crawl_schema.py
bash measurements/schema_validator.sh
```
Raw reports: `measurements/lighthouse-*.report.html|json`, `measurements/schema/`, `measurements/crawl-schema.json`.

Demo project. Larkspur Plumbing is fictional; this is not a client result.

**Order an audit:** [Fiverr gig](https://www.fiverr.com/nercari/PLACEHOLDER-seo-geo-aeo) · [Claude skill examples](https://github.com/Nercari/claude-skill-examples) · [Claude Code setup](https://github.com/Nercari/claude-code-setup-example)

# SEO + GEO audit: site_after

**Score: 19/19 checks passed (100%)**

**Health: 100%** (share of checks with no Error finding; Warn and Notice do not lower it)

## Readiness (we control)

| Check | Tier | Rule | Result | Where it fails |
|---|---|---|---|---|
| title_present | Error | Every page has a <title> | PASS |  |
| title_length | Warn | Title is 30-60 characters | PASS |  |
| title_unique | Warn | No two pages share a title | PASS |  |
| desc_present | Error | Every page has a meta description | PASS |  |
| desc_length | Warn | Description is 70-160 characters | PASS |  |
| desc_unique | Warn | No two pages share a description | PASS |  |
| one_h1 | Warn | Exactly one H1 per page | PASS |  |
| img_alt | Warn | Every image has non-empty alt text | PASS |  |
| canonical | Error | Absolute https canonical URL, same host everywhere | PASS |  |
| lang_viewport | Warn | html lang attribute and mobile viewport tag | PASS |  |
| date_author | Notice | Page shows a dated <time> and an author meta tag | PASS |  |
| jsonld_valid | Error | Page has JSON-LD and it parses | PASS |  |
| schema_localbusiness | Warn | Home page has LocalBusiness schema with name, phone, address | PASS |  |
| schema_faqpage | Warn | FAQ page has FAQPage schema matching the visible questions | PASS |  |
| nap_consistent | Warn | One business name, one phone, one street address on all pages | PASS |  |
| faq_answer_first | Notice | FAQ has 5+ questions, each with an answer of 60 words or fewer | PASS |  |
| sitemap | Error | sitemap.xml lists every page and robots.txt points to it | PASS |  |
| robots_ai | Error | robots.txt does not block search and AI crawlers | PASS |  |
| llms_txt | Notice | llms.txt present (proposed convention, ranking effect unproven) | PASS |  |

### AI and search bot access (robots.txt)

| Kind | Bot | Access |
|---|---|---|
| search/answer | Googlebot | allowed |
| search/answer | Bingbot | allowed |
| search/answer | OAI-SearchBot | allowed |
| search/answer | ChatGPT-User | allowed |
| search/answer | Claude-SearchBot | allowed |
| search/answer | Claude-User | allowed |
| search/answer | PerplexityBot | allowed |
| search/answer | Perplexity-User | allowed |
| training | GPTBot | allowed |
| training | ClaudeBot | allowed |
| training | Google-Extended | allowed |
| training | Applebot-Extended | allowed |
| training | CCBot | allowed |
| training | meta-externalagent | allowed |
| training | Bytespider | allowed |

## Visibility (measured, not promised)

This audit does not measure rankings, traffic or AI citations. Those come from Search Console,
Bing Webmaster Tools and a logged AI-answer check, reported separately as measured results.

These are good-practice checks. A high score does not guarantee rankings or AI citations.

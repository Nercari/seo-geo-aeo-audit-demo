# SEO + GEO audit: site_before

**Score: 2/19 checks passed (11%)**

| Check | Rule | Result | Where it fails |
|---|---|---|---|
| title_present | Every page has a <title> | PASS |  |
| title_length | Title is 30-60 characters | FAIL | about.html: 5 chars; faq.html: 96 chars; index.html: 4 chars; services.html: 4 chars |
| title_unique | No two pages share a title | FAIL | site: duplicates: index.html, services.html |
| desc_present | Every page has a meta description | PASS |  |
| desc_length | Description is 70-160 characters | FAIL | about.html: 18 chars; faq.html: 18 chars; index.html: 33 chars; services.html: 18 chars |
| desc_unique | No two pages share a description | FAIL | site: duplicates: faq.html, services.html |
| one_h1 | Exactly one H1 per page | FAIL | index.html: 0 H1; services.html: 2 H1 |
| img_alt | Every image has non-empty alt text | FAIL | about.html: 1 of 1 images without alt; index.html: 1 of 1 images without alt; services.html: 2 of 2 images without alt |
| canonical | Absolute https canonical URL, same host everywhere | FAIL | about.html: missing or not absolute https; faq.html: missing or not absolute https; index.html: missing or not absolute https; services.html: missing or not absolute https |
| lang_viewport | html lang attribute and mobile viewport tag | FAIL | index.html: no lang |
| date_author | Page shows a dated <time> and an author meta tag | FAIL | about.html: no date; faq.html: no date; index.html: no date; services.html: no date |
| jsonld_valid | Page has JSON-LD and it parses | FAIL | about.html: none or invalid; faq.html: none or invalid; index.html: none or invalid; services.html: none or invalid |
| schema_localbusiness | Home page has LocalBusiness schema with name, phone, address | FAIL | index.html: missing or incomplete |
| schema_faqpage | FAQ page has FAQPage schema matching the visible questions | FAIL | faq.html: no FAQPage schema |
| nap_consistent | One business name, one phone, one street address on all pages | FAIL | site: name: 3 variants; phone: 2 variants; address: 2 variants |
| faq_answer_first | FAQ has 5+ questions, each with an answer of 60 words or fewer | FAIL | faq.html: 3 Q&A pairs; 1 answers over 60 words |
| sitemap | sitemap.xml lists every page and robots.txt points to it | FAIL | sitemap.xml: sitemap.xml missing |
| robots_ai | robots.txt does not block search and AI crawlers | FAIL | robots.txt: blocks: GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended |
| llms_txt | llms.txt present (proposed convention, ranking effect unproven) | FAIL | llms.txt: missing or malformed |

These are good-practice checks. A high score does not guarantee rankings or AI citations.

# SEO + GEO audit: site_before

**Score: 2/19 checks passed (11%)**

**Health: 79%** (share of checks with no Error finding; Warn and Notice do not lower it)

## Readiness (we control)

| Check | Tier | Rule | Result | Where it fails |
|---|---|---|---|---|
| title_present | Error | Every page has a <title> | PASS |  |
| title_length | Warn | Title is 30-60 characters | FAIL | about.html: 5 chars; faq.html: 96 chars; index.html: 4 chars; services.html: 4 chars |
| title_unique | Warn | No two pages share a title | FAIL | site: duplicates: index.html, services.html |
| desc_present | Error | Every page has a meta description | PASS |  |
| desc_length | Warn | Description is 70-160 characters | FAIL | about.html: 18 chars; faq.html: 18 chars; index.html: 33 chars; services.html: 18 chars |
| desc_unique | Warn | No two pages share a description | FAIL | site: duplicates: faq.html, services.html |
| one_h1 | Warn | Exactly one H1 per page | FAIL | index.html: 0 H1; services.html: 2 H1 |
| img_alt | Warn | Every image has non-empty alt text | FAIL | about.html: 1 of 1 images without alt; index.html: 1 of 1 images without alt; services.html: 2 of 2 images without alt |
| canonical | Error | Absolute https canonical URL, same host everywhere | FAIL | about.html: missing or not absolute https; faq.html: missing or not absolute https; index.html: missing or not absolute https; services.html: missing or not absolute https |
| lang_viewport | Warn | html lang attribute and mobile viewport tag | FAIL | index.html: no lang |
| date_author | Notice | Page shows a dated <time> and an author meta tag | FAIL | about.html: no date; faq.html: no date; index.html: no date; services.html: no date |
| jsonld_valid | Error | Page has JSON-LD and it parses | FAIL | about.html: none or invalid; faq.html: none or invalid; index.html: none or invalid; services.html: none or invalid |
| schema_localbusiness | Warn | Home page has LocalBusiness schema with name, phone, address | FAIL | index.html: missing or incomplete |
| schema_faqpage | Warn | FAQ page has FAQPage schema matching the visible questions | FAIL | faq.html: no FAQPage schema |
| nap_consistent | Warn | One business name, one phone, one street address on all pages | FAIL | site: name: 3 variants; phone: 2 variants; address: 2 variants |
| faq_answer_first | Notice | FAQ has 5+ questions, each with an answer of 60 words or fewer | FAIL | faq.html: 3 Q&A pairs; 1 answers over 60 words |
| sitemap | Error | sitemap.xml lists every page and robots.txt points to it | FAIL | sitemap.xml: sitemap.xml missing |
| robots_ai | Error | robots.txt does not block search and AI crawlers | FAIL | robots.txt: blocks: GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended |
| llms_txt | Notice | llms.txt present (proposed convention, ranking effect unproven) | FAIL | llms.txt: missing or malformed |

### Findings and fixes

| Tier | URL | Check | Issue | Fix |
|---|---|---|---|---|
| Error | about.html | canonical | missing or not absolute https | Add an absolute https canonical link on one host. |
| Error | faq.html | canonical | missing or not absolute https | Add an absolute https canonical link on one host. |
| Error | index.html | canonical | missing or not absolute https | Add an absolute https canonical link on one host. |
| Error | services.html | canonical | missing or not absolute https | Add an absolute https canonical link on one host. |
| Error | about.html | jsonld_valid | none or invalid | Add JSON-LD that parses (check it with a JSON validator). |
| Error | faq.html | jsonld_valid | none or invalid | Add JSON-LD that parses (check it with a JSON validator). |
| Error | index.html | jsonld_valid | none or invalid | Add JSON-LD that parses (check it with a JSON validator). |
| Error | services.html | jsonld_valid | none or invalid | Add JSON-LD that parses (check it with a JSON validator). |
| Error | robots.txt | robots_ai | blocks: GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended | Remove the Disallow: / rules for the search and AI crawlers you want. |
| Error | sitemap.xml | sitemap | sitemap.xml missing | List every page in sitemap.xml and add a Sitemap line to robots.txt. |
| Warn | about.html | desc_length | 18 chars | Rewrite the description to 70-160 characters. |
| Warn | faq.html | desc_length | 18 chars | Rewrite the description to 70-160 characters. |
| Warn | index.html | desc_length | 33 chars | Rewrite the description to 70-160 characters. |
| Warn | services.html | desc_length | 18 chars | Rewrite the description to 70-160 characters. |
| Warn | site | desc_unique | duplicates: faq.html, services.html | Give each page its own description. |
| Warn | about.html | img_alt | 1 of 1 images without alt | Add short alt text that describes each image. |
| Warn | index.html | img_alt | 1 of 1 images without alt | Add short alt text that describes each image. |
| Warn | services.html | img_alt | 2 of 2 images without alt | Add short alt text that describes each image. |
| Warn | index.html | lang_viewport | no lang | Add <html lang> and a mobile viewport meta tag. |
| Warn | site | nap_consistent | name: 3 variants; phone: 2 variants; address: 2 variants | Use one business name, phone and street address on every page. |
| Warn | index.html | one_h1 | 0 H1 | Keep exactly one H1 and make the rest H2 or lower. |
| Warn | services.html | one_h1 | 2 H1 | Keep exactly one H1 and make the rest H2 or lower. |
| Warn | faq.html | schema_faqpage | no FAQPage schema | Add FAQPage schema whose questions match the visible ones. |
| Warn | index.html | schema_localbusiness | missing or incomplete | Add LocalBusiness schema with name, telephone and address to the home page. |
| Warn | about.html | title_length | 5 chars | Rewrite the title to 30-60 characters. |
| Warn | faq.html | title_length | 96 chars | Rewrite the title to 30-60 characters. |
| Warn | index.html | title_length | 4 chars | Rewrite the title to 30-60 characters. |
| Warn | services.html | title_length | 4 chars | Rewrite the title to 30-60 characters. |
| Warn | site | title_unique | duplicates: index.html, services.html | Give each page its own title. |
| Notice | about.html | date_author | no date | Show a dated <time> element and an author meta tag. |
| Notice | faq.html | date_author | no date | Show a dated <time> element and an author meta tag. |
| Notice | index.html | date_author | no date | Show a dated <time> element and an author meta tag. |
| Notice | services.html | date_author | no date | Show a dated <time> element and an author meta tag. |
| Notice | faq.html | faq_answer_first | 3 Q&A pairs; 1 answers over 60 words | Answer each question first, in 60 words or fewer. |
| Notice | llms.txt | llms_txt | missing or malformed | Add an llms.txt with a title and links (optional, effect unproven). |

### AI and search bot access (robots.txt)

| Kind | Bot | Access |
|---|---|---|
| search/answer | Googlebot | allowed |
| search/answer | Bingbot | allowed |
| search/answer | OAI-SearchBot | blocked |
| search/answer | ChatGPT-User | allowed |
| search/answer | Claude-SearchBot | allowed |
| search/answer | Claude-User | allowed |
| search/answer | PerplexityBot | blocked |
| search/answer | Perplexity-User | allowed |
| training | GPTBot | blocked |
| training | ClaudeBot | blocked |
| training | Google-Extended | blocked |
| training | Applebot-Extended | allowed |
| training | CCBot | allowed |
| training | meta-externalagent | allowed |
| training | Bytespider | allowed |

## Visibility (measured, not promised)

This audit does not measure rankings, traffic or AI citations. Those come from Search Console,
Bing Webmaster Tools and a logged AI-answer check, reported separately as measured results.

These are good-practice checks. A high score does not guarantee rankings or AI citations.

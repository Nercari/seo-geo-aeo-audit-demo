# Sample: SEO + GEO audit and fixes for a small business website

All names, domains, phone numbers and addresses here are fictional (`quillmere-plumbing.example`, 555 numbers). The business, "Quillmere Plumbing" in "Marlowe Falls", does not exist.

**SEO** = getting found on Google. **GEO** = getting found and quoted in AI answers (ChatGPT, Perplexity, Claude, Google AI features).

## What is in this folder

| Item | What it is |
|---|---|
| `demo/site_before/` | A small 4-page site with the problems I see most often |
| `demo/site_after/` | The same site after fixes |
| `audit.py` | A checker that tests 19 rules and prints PASS/FAIL per rule. Same input, same answer every time |
| `accept.py` | Runs the checker on both folders and confirms: many failures before, none after |
| `out/` | The two reports the checker writes |
| `deliverable_example.md` | What a buyer receives (Markdown; the buyer applies the files and nothing is published for them) |

Run it: `python audit.py demo/site_before` (Python 3 only, nothing to install).

## Result on this sample

| | Checks passed | Score |
|---|---|---|
| Before | 2 of 19 | 11% |
| After | 19 of 19 | 100% |

The score counts checks passed. It measures how complete the fundamentals are. It is not a ranking score.

## What is checked and why

| Check | Why it matters for Google | Why it matters for AI answers |
|---|---|---|
| Title present, 30-60 chars, unique | The title is the clickable headline in results. Too long gets cut off; duplicates make pages compete | Titles help AI tools tell your pages apart |
| Meta description present, 70-160 chars, unique | Often shown as the snippet under the title; affects whether people click | Gives a ready summary of the page |
| One H1 per page | Tells search engines what the page is about | A clear top heading makes the page easier to summarize |
| Alt text on images | Helps image search and accessibility | Text is the only part of an image most AI tools can use |
| Canonical URL | Stops duplicate-URL confusion | Same: one clear address per page |
| `lang` and mobile viewport | Mobile-friendliness is a Google requirement | Basic page hygiene |
| Date and author on pages | Shows freshness and who is responsible | AI tools prefer content with a visible, current source |
| JSON-LD structured data | Lets Google show rich results and understand the business | Machine-readable facts are easy to quote correctly |
| LocalBusiness schema | Feeds local results and maps | States name, phone, address and area in a form AI can read |
| FAQPage schema matching visible questions | Questions and answers are explicit | Mirrors how people ask AI tools |
| Same name, address, phone everywhere (NAP) | Conflicting details lower trust in local results | Conflicting facts make AI tools quote the wrong number, or skip you |
| FAQ with short answer-first replies | Matches the questions people type | A 1-2 sentence direct answer is the easiest thing to quote |
| sitemap.xml listing every page, linked from robots.txt | Helps Google find all pages | Same for other crawlers |
| robots.txt allows search and AI crawlers (Googlebot, Bingbot, GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended) | Blocking Googlebot or Bingbot removes you from results | If AI crawlers are blocked, those tools cannot read your site. Whether to allow them is your business decision; the sample allows them |
| llms.txt | None known | A plain-text summary for AI tools. This is a **proposed convention**. Its effect on rankings or AI citations is **unproven**, and no major search engine has said it uses it. It is cheap, so I include it as optional |

## Limits (please read)

- This sample shows the audit and the fixes. It does **not** prove higher rankings or more AI citations.
- Rankings and AI answers depend on many outside factors: competitors, your reviews and backlinks, your location, how long the site has existed, and changes by Google and the AI companies. Results take weeks to months, if they come at all.
- No one can honestly guarantee a position on Google or a mention in ChatGPT, and I do not.
- The checker tests technical basics and page text. It does not judge content quality, your competitors, or whether your pages answer your customers' real questions beyond the structure shown.
- Prices and facts on the sample site are invented.
- Real client work may use a CMS (WordPress, Wix, Shopify). Fixes can be delivered as files, or applied on the site when the buyer grants CMS access.

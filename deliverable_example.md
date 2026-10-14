# SEO + GEO audit for Quillmere Plumbing (sample, fictional)

Site audited: quillmere-plumbing.example, 4 pages. Result: **2 of 19 checks passed**.

Fixes are ordered by importance. "Effort" is how long the change takes me or your web person.

## Priority 1: stop losing visibility (fix first)

1. **Let search and AI crawlers read your site.** Your `robots.txt` blocks GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot and Google-Extended. AI tools cannot read pages they are blocked from. Replace it with the version in the `site_after` folder. This is your choice to make: if you do not want AI tools using your content, say so and we keep the blocks. Effort: 5 minutes.
2. **Give every page a unique title of 30-60 characters.** Today the home page and services page are both titled "Home" (4 characters), the About page has no title, and the FAQ title is 95 characters and gets cut off. Example fix for the home page: "Plumber in Marlowe Falls, OR | Quillmere Plumbing". Effort: 20 minutes.
3. **Declare your name, address and phone, and keep them the same on every page.** Your pages have no LocalBusiness schema, so the automatic check finds no declared business name and fails. The tool only compares declared values (schema, microdata, the footer address); reading your pages by hand, I also found three business names (Quillmere Plumbing, Quillmere Plumbing Co., Quillmere Lane Plumbers), two phone numbers ((555) 010-0142 and (555) 010-0124) and two street addresses (14 Mill Street and 41 Mill St.). Search and AI tools cannot tell which is true and may show a wrong number. Pick the correct set, put it in LocalBusiness schema and use it everywhere. Effort: 30 minutes, plus your confirmation of the right details.

## Priority 2: help Google understand each page

4. **Write a meta description for each page (70-160 characters).** The home and About pages have none; the Services and FAQ pages share the same 18-character text. Effort: 20 minutes.
5. **Use exactly one H1 heading per page.** The home page has none and the Services page has two. Effort: 10 minutes.
6. **Add alt text to all 4 images.** Describe what the picture shows in a short sentence. Effort: 10 minutes.
7. **Add a canonical link to each page** so each page has one official address. Effort: 10 minutes.
8. **Add `sitemap.xml` and a Sitemap line in `robots.txt`**, listing all 4 pages. Effort: 10 minutes.
9. **Add the language setting to the home page** (`lang="en"`). Effort: 1 minute.

## Priority 3: get quoted in AI answers

10. **Rewrite the FAQ as short, direct answers.** Your current answers are vague ("please reach out to our team") and one runs 70+ words. Lead with the answer in 1-2 sentences, with real numbers where you have them. The sample FAQ has 7 questions people really ask, such as "How much does a plumber cost in Marlowe Falls?". Every answer uses only a fact you confirmed, such as a price or a time. I will not invent facts for you, and an answer without a confirmed fact stays out. You approve each answer before it goes on your site. Effort: 1-2 hours, mostly your input.
11. **Add LocalBusiness structured data (JSON-LD) to the home page** with your name, phone, address, hours and service area. Effort: 15 minutes.
12. **Add FAQPage structured data to the FAQ page**, matching the visible questions exactly. Effort: 15 minutes.
13. **Add structured data to the other pages** (a simple WebPage block). Effort: 10 minutes.
14. **Show a "last reviewed" date and an author** on each page. Visible dates and a named person make content easier to trust. Effort: 10 minutes.

## Priority 4: optional extra

15. **Add an `llms.txt` file** (a plain-text summary of your site for AI tools). This is a proposed convention; there is no evidence yet that it changes rankings or AI citations. It is cheap, so you can have it or skip it.

## After the fixes

Before delivery I ran the same checker (`audit.py`) on the drafted fixes and the drafted FAQ, not only on the old site. The results are measured, and the full before and after reports are in `demo/out/`.

| | Pages checked | Checks passed | Score |
|---|---|---|---|
| Before (your current site) | 4 | 2 of 19 | 11% |
| After (the drafted fixes and FAQ) | 4 | 19 of 19 | 100% |

AI-answer citations: not measured in this sample (the business is fictional). On a real job I include them only when I can measure them, before and after, and I report what I saw. I do not promise citations.

How the files reach your site: by default you receive Markdown, HTML or a git draft and apply them yourself. If you grant CMS access, I can apply the fixes you approve on your site. Either way, you approve each fix and each FAQ answer first.

## What to expect

These fixes remove technical problems that hold a site back and make your facts clear to search engines and AI tools. They do not guarantee a higher Google position or a mention in ChatGPT or other AI answers. Those depend on competitors, reviews, links, your location and changes outside anyone's control, and usually take weeks to months to show. Check your Google Search Console in 4-8 weeks and compare.

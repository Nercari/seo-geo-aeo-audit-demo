"""Deterministic SEO + GEO audit for a small static site (standard library only).

Usage: python3 audit.py <site_folder> [--compare prev.json]
Prints a PASS/FAIL table and a score; writes demo/out/report_<name>.md plus
findings_<name>.json and findings_<name>.csv (url, check, tier, issue, fix),
sorted so they diff cleanly against an earlier run or a Screaming Frog export.
--compare prev.json lists new, fixed and unchanged findings against a past run.

The score counts the 19 core checks. Each check also has a tier (Error, Warn,
Notice); the health % counts only checks with an Error finding.

Rules are fixed and checkable by code. They are good-practice checks, not a
prediction of rankings or AI citations. The NAP check compares only declared,
structured values across pages (LocalBusiness-family JSON-LD name, telephone and
streetAddress; LocalBusiness microdata; phones and street in a business <address>
element; og:site_name only as a fallback name),
normalised for case, whitespace, NBSP and punctuation. It does not scan body text
for name variants, so a variant written only in prose is not caught.
"""
import json
import posixpath
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

AI_BOTS = ["Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ClaudeBot", "PerplexityBot", "Google-Extended"]
TITLE_RANGE = (30, 60)
DESC_RANGE = (70, 160)
MAX_ANSWER_WORDS = 60
MIN_FAQ = 5

PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]\d{4}")


# LocalBusiness and its schema.org subtypes, listed explicitly (no suffix matching: a plain "Service"
# or "OnlineStore" is not a local business).
LB_TYPES = {
    "LocalBusiness",
    "AnimalShelter", "ArchiveOrganization", "AutomotiveBusiness", "AutoBodyShop", "AutoDealer", "AutoPartsStore",
    "AutoRental", "AutoRepair", "AutoWash", "GasStation", "MotorcycleDealer", "MotorcycleRepair",
    "ChildCare", "Dentist", "DryCleaningOrLaundry",
    "EmergencyService", "FireStation", "Hospital", "PoliceStation",
    "EmploymentAgency", "EntertainmentBusiness", "AdultEntertainment", "AmusementPark", "ArtGallery", "Casino",
    "ComedyClub", "MovieTheater", "NightClub",
    "FinancialService", "AccountingService", "AutomatedTeller", "BankOrCreditUnion", "InsuranceAgency",
    "FoodEstablishment", "Bakery", "BarOrPub", "Brewery", "CafeOrCoffeeShop", "Distillery", "FastFoodRestaurant",
    "IceCreamShop", "Restaurant", "Winery",
    "GovernmentOffice", "PostOffice",
    "HealthAndBeautyBusiness", "BeautySalon", "DaySpa", "HairSalon", "HealthClub", "NailSalon", "TattooParlor",
    "HomeAndConstructionBusiness", "Electrician", "GeneralContractor", "HVACBusiness", "HousePainter", "Locksmith",
    "MovingCompany", "Plumber", "RoofingContractor",
    "InternetCafe", "LegalService", "Attorney", "Notary", "Library",
    "LodgingBusiness", "BedAndBreakfast", "Campground", "Hostel", "Hotel", "Motel", "Resort", "VacationRental",
    "MedicalBusiness", "CommunityHealth", "Dermatology", "DietNutrition", "Emergency", "Geriatric", "Gynecologic",
    "MedicalClinic", "Midwifery", "Nursing", "Obstetric", "Oncologic", "Optician", "Optometric", "Otolaryngologic",
    "Pediatric", "Pharmacy", "Physician", "Physiotherapy", "PlasticSurgery", "Podiatric", "PrimaryCare",
    "Psychiatric", "PublicHealth",
    "ProfessionalService", "RadioStation", "RealEstateAgent", "RecyclingCenter", "SelfStorage", "ShoppingCenter",
    "SportsActivityLocation", "BowlingAlley", "ExerciseGym", "GolfCourse", "PublicSwimmingPool", "SkiResort",
    "SportsClub", "StadiumOrArena", "TennisComplex",
    "Store", "BikeStore", "BookStore", "ClothingStore", "ComputerStore", "ConvenienceStore", "DepartmentStore",
    "ElectronicsStore", "Florist", "FurnitureStore", "GardenStore", "GroceryStore", "HardwareStore", "HobbyShop",
    "HomeGoodsStore", "JewelryStore", "LiquorStore", "MensClothingStore", "MobilePhoneStore", "MovieRentalStore",
    "MusicStore", "OfficeEquipmentStore", "OutletStore", "PawnShop", "PetStore", "ShoeStore", "SportingGoodsStore",
    "TireShop", "ToyStore", "WholesaleStore",
    "TelevisionStation", "TouristInformationCenter", "TravelAgency", "VeterinaryCare",
}
ADDR_SCOPES = {"PostalAddress", "ContactPoint"}


def is_local_business(o):
    return any(t in LB_TYPES for t in types_of(o))


def scope_kind(itemtype):
    t = (itemtype or "").split()[0].rstrip("/").rsplit("/", 1)[-1] if (itemtype or "").strip() else ""
    return "lb" if t in LB_TYPES else "addr" if t in ADDR_SCOPES else "other"


def nkey(t):
    """Comparison key: lower case, NBSP and runs of whitespace collapsed, punctuation dropped
    ("Acme Co." == "acme co", "+1 (555) 010-0142" phones are compared by digits instead)."""
    t = str(t).replace("\xa0", " ").lower()
    return " ".join(re.sub(r"[^\w\s]", " ", t).split())


def og_name(v):
    """og:site_name without a tagline ("Bramble Bakery | Fresh bread") or a trailing "(demo)"."""
    v = re.split(r"\s+[|\u2013\u2014]\s+|\s*:\s+|\s+-\s+", v.strip(), maxsplit=1)[0]
    return re.sub(r"\s*\(.*\)\s*$", "", v).strip()


def phone_key(v):
    d = re.sub(r"\D", "", str(v))
    return d[-10:] if len(d) >= 10 else d


def as_str(v):
    """A JSON-LD value usable as a NAP key: strings only (lists, objects, numbers, null are skipped)."""
    return v.strip() if isinstance(v, str) else ""


def street_of(addr):
    if isinstance(addr, dict):
        return as_str(addr.get("streetAddress"))
    return as_str(addr)


def has_word_seq(key, text):
    """key (an nkey) appears in text as whole words: '12 oak street' is not found in '112 oak street'."""
    return re.search(r"(?<!\w)" + re.escape(key) + r"(?!\w)", nkey(text)) is not None


def nap_sources(pages):
    """Declared NAP values only:
    - LocalBusiness-family JSON-LD: name, telephone, address.streetAddress (string values only);
    - microdata itemprop name/telephone/streetAddress belonging to a LocalBusiness itemscope (directly, or via
      its PostalAddress/ContactPoint; a nested Person's values are ignored);
    - phone numbers in a business <address> element (see PageParser.addresses);
    - og:site_name (tagline stripped), only when no LocalBusiness name is declared anywhere.
    Body text is never scanned. Returns {"name"|"phone"|"street": {key: (shown value, [pages])}}."""
    src = {"name": {}, "phone": {}, "street": {}}

    def put(kind, key, shown, page):
        if key:
            src[kind].setdefault(key, (shown, []))[1].append(page)

    for n in sorted(pages):
        p = pages[n]
        for o in parse_ld(p)[1]:
            if is_local_business(o):
                nm, tel, st = as_str(o.get("name")), as_str(o.get("telephone")), street_of(o.get("address"))
                put("name", nkey(nm), nm, n)
                put("phone", phone_key(tel), tel, n)
                put("street", nkey(st), st, n)
        for k, v in p.itemprops:
            kind = {"name": "name", "telephone": "phone", "streetAddress": "street"}[k]
            put(kind, phone_key(v) if kind == "phone" else nkey(v), " ".join(v.split()), n)
        for t in p.addresses:
            for ph in PHONE_RE.findall(t):
                put("phone", phone_key(ph), ph, n)
    if not src["name"]:
        for n in sorted(pages):
            og = og_name(pages[n].meta.get("og:site_name", ""))
            put("name", nkey(og), og, n)
    return src


# (id, why it matters in one line, scope)
CHECKS = [
    ("title_present", "Every page has a <title>", "page"),
    ("title_length", f"Title is {TITLE_RANGE[0]}-{TITLE_RANGE[1]} characters", "page"),
    ("title_unique", "No two pages share a title", "site"),
    ("desc_present", "Every page has a meta description", "page"),
    ("desc_length", f"Description is {DESC_RANGE[0]}-{DESC_RANGE[1]} characters", "page"),
    ("desc_unique", "No two pages share a description", "site"),
    ("one_h1", "Exactly one H1 per page", "page"),
    ("img_alt", "Every image has non-empty alt text", "page"),
    ("canonical", "Absolute https canonical URL, same host everywhere", "page"),
    ("lang_viewport", "html lang attribute and mobile viewport tag", "page"),
    ("date_author", "Page shows a dated <time> and an author meta tag", "page"),
    ("jsonld_valid", "Page has JSON-LD and it parses", "page"),
    ("schema_localbusiness", "Home page has LocalBusiness schema with name, phone, address", "site"),
    ("schema_faqpage", "FAQ page has FAQPage schema matching the visible questions", "site"),
    ("nap_consistent", "Declared business name, phone and street address (schema, microdata, footer <address>) match on all pages", "site"),
    ("faq_answer_first", f"FAQ has {MIN_FAQ}+ questions, each with an answer of {MAX_ANSWER_WORDS} words or fewer", "site"),
    ("sitemap", "sitemap.xml lists every page and robots.txt points to it", "site"),
    ("robots_ai", "robots.txt does not block search and AI crawlers", "site"),
    ("llms_txt", "llms.txt present (proposed convention, ranking effect unproven)", "site"),
]


# Tier and one-line fix for every check.
TIERS = {
    "title_present": ("Error", "Add a unique <title> to the page."),
    "title_length": ("Warn", f"Rewrite the title to {TITLE_RANGE[0]}-{TITLE_RANGE[1]} characters."),
    "title_unique": ("Warn", "Give each page its own title."),
    "desc_present": ("Error", "Add a meta description that sums up the page."),
    "desc_length": ("Warn", f"Rewrite the description to {DESC_RANGE[0]}-{DESC_RANGE[1]} characters."),
    "desc_unique": ("Warn", "Give each page its own description."),
    "one_h1": ("Warn", "Keep exactly one H1 and make the rest H2 or lower."),
    "img_alt": ("Warn", "Add short alt text that describes each image."),
    "canonical": ("Error", "Add an absolute https canonical link on one host."),
    "lang_viewport": ("Warn", "Add <html lang> and a mobile viewport meta tag."),
    "date_author": ("Notice", "Show a dated <time> element and an author meta tag."),
    "jsonld_valid": ("Error", "Add JSON-LD that parses (check it with a JSON validator)."),
    "schema_localbusiness": ("Warn", "Add LocalBusiness schema with name, telephone and address to the home page."),
    "schema_faqpage": ("Warn", "Add FAQPage schema whose questions match the visible ones."),
    "nap_consistent": ("Warn", "Declare the business name, phone and address in LocalBusiness schema and use the same values on every page."),
    "faq_answer_first": ("Notice", f"Answer each question first, in {MAX_ANSWER_WORDS} words or fewer."),
    "sitemap": ("Error", "List every page in sitemap.xml and add a Sitemap line to robots.txt."),
    "robots_ai": ("Error", "Remove the Disallow: / rules for the search and AI crawlers you want."),
    "llms_txt": ("Notice", "Add an llms.txt with a title and links (optional, effect unproven)."),
}
TIERS.update({
    "robots_root": ("Warn", "Move robots.txt to the site root (https://host/robots.txt)."),
    "jsonld_visible": ("Warn", "Show the same value on the page, or remove it from the JSON-LD."),
    "snippet_controls": ("Error", "Remove nosnippet / max-snippet:0 from the robots meta tag."),
    "noindex": ("Error", "Remove noindex from the robots meta tag if the page should be found."),
})
VISIBLE_KEYS = {"name", "telephone", "streetAddress", "addressLocality", "postalCode", "text"}
TIER_ORDER = {"Error": 0, "Warn": 1, "Notice": 2}

# Bots for the access table. Search/answer bots fetch pages to show or cite them;
# training bots collect data for model training. Blocking one does not block the other.
SEARCH_BOTS = ["Googlebot", "Bingbot", "OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot",
               "Claude-User", "PerplexityBot", "Perplexity-User"]
TRAINING_BOTS = ["GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot",
                 "meta-externalagent", "Bytespider"]


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.meta = {}
        self.canonical = None
        self.h1 = 0
        self.imgs = []
        self.ld = []
        self.times = 0
        self.lang = None
        self.viewport = False
        self.blocks = []  # (tag, text) for h1-h6 and p
        self.text = []
        self._cur = None
        self._buf = []
        self._script = None
        self._in_title = False
        self.itemprops = []  # (itemprop, value)
        self._scopes = []  # open elements: (tag, None | is-LocalBusiness itemscope)
        self.addresses = []
        self._ip = []  # open itemprop captures: [tag, prop, parts]
        self._addr = None
        self._addr_biz = False
        self._addr_level = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        ip = a.get("itemprop")
        sc = [k for _, k in self._scopes if k is not None]  # enclosing itemscope kinds, outermost first
        lb_own = sc[-1:] == ["lb"] or sc[-2:] == ["lb", "addr"]  # the business itself or its address/contact
        if ip in ("name", "telephone", "streetAddress") and (sc[-1:] == ["lb"] if ip == "name" else lb_own):
            if a.get("content") is not None:
                self.itemprops.append((ip, a["content"]))
            elif tag not in VOID:
                self._ip.append([len(self._scopes) + 1, ip, []])
        if tag not in VOID:
            self._scopes.append((tag, scope_kind(a.get("itemtype")) if "itemscope" in a else None))
        if self._addr is not None and tag in ("br", "p", "div", "li", "tr", "td"):
            self._addr.append(" ")
        if tag == "address" and self._addr is None:
            in_article = any(t == "article" for t, _ in self._scopes[:-1])
            # business <address>: inside the LocalBusiness scope, or outside any itemscope and any <article>
            self._addr_biz = lb_own or (not sc and not in_article)
            self._addr_level = len(self._scopes)
            self._addr = []
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "title":
            self._in_title = True
            self.title = ""
        elif tag == "meta":
            n = (a.get("name") or a.get("property") or "").lower()
            if n:
                self.meta[n] = a.get("content") or ""
            if n == "viewport":
                self.viewport = True
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href")
        elif tag == "img":
            self.imgs.append(a.get("alt"))
        elif tag == "time" and a.get("datetime"):
            self.times += 1
        elif tag == "script":
            self._script = "" if (a.get("type") or "") == "application/ld+json" else None
            self._skip = True
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p"):
            self._cur, self._buf = tag, []
            if tag == "h1":
                self.h1 += 1

    def handle_endtag(self, tag):
        for i in range(len(self._scopes) - 1, -1, -1):
            if self._scopes[i][0] == tag:
                del self._scopes[i:]
                break
        while self._ip and self._ip[-1][0] > len(self._scopes):
            _, ip, parts = self._ip.pop()
            self.itemprops.append((ip, "".join(parts)))
        if self._addr is not None and self._addr_level > len(self._scopes):
            t = " ".join("".join(self._addr).split())
            # a byline-like <address> with neither a phone nor a number (street) is not business contact data
            if self._addr_biz and (PHONE_RE.search(t) or re.search(r"\d", t)):
                self.addresses.append(t)
            self._addr = None
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            if self._script is not None:
                self.ld.append(self._script)
            self._script = None
            self._skip = False
        elif tag == self._cur:
            self.blocks.append((tag, " ".join("".join(self._buf).split())))
            self._cur = None

    def handle_data(self, d):
        if self._in_title and self.title is not None:
            self.title += d
        elif self._script is not None:
            self._script += d
        elif getattr(self, "_skip", False):
            return
        else:
            self.text.append(d)
            for c in self._ip:
                c[2].append(d)
            if self._addr is not None:
                self._addr.append(d)
            if self._cur:
                self._buf.append(d)


def parse_ld(p):
    """Return (ok, list_of_schema_objects)."""
    objs = []
    if not p.ld:
        return False, objs
    for raw in p.ld:
        try:
            data = json.loads(raw)
        except ValueError:
            return False, objs
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        objs.extend(i for i in items if isinstance(i, dict))
    return True, objs


def types_of(o):
    t = o.get("@type")
    t = t if isinstance(t, list) else [t]
    return [x for x in t if isinstance(x, str)]


def robots_blocked(text, bot):
    groups, agents, rules, last_rule = [], [], [], False
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if ":" not in line:
            continue
        k, v = (s.strip() for s in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if last_rule:
                groups.append((agents, rules))
                agents, rules, last_rule = [], [], False
            agents.append(v.lower())
        elif k in ("allow", "disallow"):
            rules.append((k, v))
            last_rule = True
    groups.append((agents, rules))
    pick = [g for g in groups if bot.lower() in g[0]] or [g for g in groups if "*" in g[0]]
    return any(k == "disallow" and v == "/" for g in pick for k, v in g[1])


def site_base(home, locs):
    """Folder the site is served from, e.g. '/' or '/seo-geo-aeo-audit-demo/' (GitHub Pages project site).
    From the home page canonical when present, else the sitemap's common folder. Returns (base, parsed home URL)."""
    hu = urlparse(home.canonical) if home is not None and home.canonical else None
    if hu is not None and hu.path:
        hp = unquote(hu.path)
        if not hp.endswith("/"):
            hp = hp.rsplit("/", 1)[0] + "/" if "." in hp.rsplit("/", 1)[1] else hp + "/"
        return hp, hu
    paths = [unquote(urlparse(l).path) for l in locs]
    paths = [q for q in paths if q.startswith("/")]
    if not paths:
        return "/", hu
    return posixpath.commonpath([q.rsplit("/", 1)[0] + "/" for q in paths]).rstrip("/") + "/", hu


def is_noindex(p):
    d = {x.strip() for k in ("robots", "googlebot", "bingbot") for x in p.meta.get(k, "").lower().split(",")}
    return "noindex" in d or "none" in d


def audit(site):
    site = Path(site)
    files = sorted(site.glob("*.html"))
    pages = {}
    for f in files:
        p = PageParser()
        p.feed(f.read_text(encoding="utf-8"))
        pages[f.name] = p
    results = {c[0]: [] for c in CHECKS}  # id -> list of (ok, where, detail)

    def add(cid, ok, where, detail=""):
        results[cid].append((ok, where, detail))

    for name, p in pages.items():
        t = (p.title or "").strip()
        add("title_present", bool(t), name, "missing" if not t else "")
        if t:
            add("title_length", TITLE_RANGE[0] <= len(t) <= TITLE_RANGE[1], name, f"{len(t)} chars")
        else:
            add("title_length", False, name, "no title")
        d = p.meta.get("description", "").strip()
        add("desc_present", bool(d), name, "missing" if not d else "")
        if d:
            add("desc_length", DESC_RANGE[0] <= len(d) <= DESC_RANGE[1], name, f"{len(d)} chars")
        else:
            add("desc_length", False, name, "no description")
        add("one_h1", p.h1 == 1, name, f"{p.h1} H1")
        bad = sum(1 for a in p.imgs if not (a or "").strip())
        add("img_alt", bad == 0, name, f"{bad} of {len(p.imgs)} images without alt" if bad else "")
        c = p.canonical or ""
        u = urlparse(c)
        add("canonical", bool(c) and u.scheme == "https" and bool(u.netloc), name, "missing or not absolute https" if not (c and u.scheme == "https") else "")
        add("lang_viewport", bool(p.lang) and p.viewport, name, "no lang" if not p.lang else ("no viewport" if not p.viewport else ""))
        add("date_author", p.times > 0 and bool(p.meta.get("author")), name, "no date" if not p.times else ("no author" if not p.meta.get("author") else ""))
        ok, _ = parse_ld(p)
        add("jsonld_valid", ok, name, "none or invalid" if not ok else "")

    hosts = {urlparse(p.canonical or "").netloc for p in pages.values() if p.canonical}
    if len(hosts) > 1:
        add("canonical", False, "site", "canonical hosts differ")

    def dup(values):
        seen, d = {}, set()
        for n, v in values:
            if v:
                if v in seen:
                    d.update((n, seen[v]))
                seen[v] = n
        return sorted(d)

    dt = dup((n, (p.title or "").strip()) for n, p in pages.items())
    add("title_unique", not dt, "site", "duplicates: " + ", ".join(dt) if dt else "")
    dd = dup((n, p.meta.get("description", "").strip()) for n, p in pages.items())
    add("desc_unique", not dd, "site", "duplicates: " + ", ".join(dd) if dd else "")

    # schema (site-level)
    home = pages.get("index.html")
    ok = bool(home) and any(is_local_business(o) and o.get("name") and o.get("telephone") and o.get("address")
                            for o in parse_ld(home)[1])
    add("schema_localbusiness", ok, "index.html", "" if ok else "missing or incomplete")
    faq = pages.get("faq.html")
    ok, why = False, "no FAQPage schema"
    if faq:
        visible = {t for tag, t in faq.blocks if tag == "h3"}
        for o in parse_ld(faq)[1]:
            if "FAQPage" in types_of(o):
                qs = [q.get("name", "") for q in o.get("mainEntity", [])]
                ok = len(qs) >= MIN_FAQ and all(q in visible for q in qs)
                why = "" if ok else "schema questions do not match visible questions"
    add("schema_faqpage", ok, "faq.html", why)

    # NAP: structured / declared sources only (see nap_sources); no free-text name scanning.
    src = nap_sources(pages)
    problems = []
    if not src["name"]:
        problems.append("site declares no business name (LocalBusiness JSON-LD, og:site_name or itemprop name)")
    for label, kind in (("name", "name"), ("phone", "phone"), ("street address", "street")):
        if len(src[kind]) > 1:
            vals = sorted(src[kind].values(), key=lambda v: (-len(v[1]), v[0]))
            problems.append(f"{label} differs across declared sources: " + "; ".join(
                f"'{shown}' ({', '.join(sorted(set(pg)))})" for shown, pg in vals))
    streets = list(src["street"])
    if len(streets) == 1:
        miss = sorted(n for n, p in pages.items() for t in p.addresses if not has_word_seq(streets[0], t))
        if miss:
            problems.append("<address> element does not show the declared street address: " + ", ".join(sorted(set(miss))))
    add("nap_consistent", not problems, "site", "; ".join(problems))

    # FAQ answer-first
    ok, why = False, "no faq.html"
    if faq:
        qa = []
        for i, (tag, t) in enumerate(faq.blocks):
            if tag == "h3" and i + 1 < len(faq.blocks) and faq.blocks[i + 1][0] == "p":
                qa.append((t, len(faq.blocks[i + 1][1].split())))
        long_ = [q for q, n in qa if n > MAX_ANSWER_WORDS]
        ok = len(qa) >= MIN_FAQ and not long_
        why = "" if ok else f"{len(qa)} Q&A pairs; {len(long_)} answers over {MAX_ANSWER_WORDS} words"
    add("faq_answer_first", ok, "faq.html", why)

    # site files
    robots = site / "robots.txt"
    rtxt = robots.read_text(encoding="utf-8") if robots.exists() else ""
    sm = site / "sitemap.xml"
    ok, why = False, "sitemap.xml missing"
    if sm.exists():
        try:
            locs = [l.strip() for l in re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8"))]
            base, home_u = site_base(home, locs)
            paths = {unquote(urlparse(l).path) or "/" for l in locs}
            paths |= {q[:-len("index.html")] for q in paths if q.endswith("/index.html")}
            listable = [n for n, p in pages.items() if n != "404.html" and not is_noindex(p)]
            expected = {base if n == "index.html" else base + n for n in listable}
            if home_u is not None and home_u.netloc:
                off = sorted(l for l in locs if (urlparse(l).scheme, urlparse(l).netloc) != (home_u.scheme, home_u.netloc))
            else:
                off = []
            missing = sorted(expected - paths)
            ref = re.search(r"(?im)^\s*sitemap:\s*\S+sitemap\.xml", rtxt) is not None
            ok = not missing and ref and not off
            why = "" if ok else ("pages missing: " + ", ".join(missing) if missing else
                                 "URLs not on the canonical host: " + ", ".join(off[:3]) if off else "robots.txt has no Sitemap line")
        except (OSError, ValueError) as e:
            why = f"sitemap.xml unreadable: {e}"
    add("sitemap", ok, "sitemap.xml", why)
    if not robots.exists():
        add("robots_ai", False, "robots.txt", "robots.txt missing")
    else:
        blocked = [b for b in AI_BOTS if robots_blocked(rtxt, b)]
        add("robots_ai", not blocked, "robots.txt", "blocks: " + ", ".join(blocked) if blocked else "")
    ll = site / "llms.txt"
    ok = ll.exists() and ll.read_text(encoding="utf-8").lstrip().startswith("# ") and "](" in ll.read_text(encoding="utf-8")
    add("llms_txt", bool(ok), "llms.txt", "" if ok else "missing or malformed")
    extra_checks(site, pages, results)
    return results


def ld_values(o, out):
    """Collect (key, string) pairs for VISIBLE_KEYS anywhere in a JSON-LD object."""
    if isinstance(o, dict):
        for k, v in o.items():
            if k in VISIBLE_KEYS and isinstance(v, str):
                out.append((k, v))
            else:
                ld_values(v, out)
    elif isinstance(o, list):
        for v in o:
            ld_values(v, out)
    return out


def norm(t):
    return " ".join(t.lower().split())


def extra_checks(site, pages, results):
    for cid, _, _ in EXTRA_CHECKS:
        results.setdefault(cid, [])
    sm = site / "sitemap.xml"
    try:
        locs = [l.strip() for l in re.findall(r"<loc>([^<]+)</loc>", sm.read_text(encoding="utf-8"))] if sm.exists() else []
    except (OSError, ValueError):  # ValueError covers UnicodeDecodeError
        locs = []
    base, _ = site_base(pages.get("index.html"), locs)
    if (site / "robots.txt").exists() and base != "/":
        results["robots_root"].append((False, "robots.txt", f"site is served from {base}; crawlers only read /robots.txt at the host root, so this file is ignored"))
    elif (site / "robots.txt").exists():
        results["robots_root"].append((True, "robots.txt", ""))
    else:
        nested = sorted(str(p.relative_to(site)) for p in site.rglob("robots.txt"))
        results["robots_root"].append((False, "robots.txt", "found only at " + ", ".join(nested) if nested else "no robots.txt at root"))
    for name, p in pages.items():
        text = norm(" ".join(p.text))
        digits = re.sub(r"\D", "", text)
        missing = []
        for k, v in ld_values(parse_ld(p)[1], []):
            if k == "telephone":
                d = re.sub(r"\D", "", v)[-10:]
                if d and d not in digits:
                    missing.append(f"{k}={v}")
            elif norm(v) not in text:
                missing.append(f"{k}={v[:40]}")
        results["jsonld_visible"].append((not missing, name, "not visible: " + "; ".join(sorted(set(missing))) if missing else ""))
        directives = {d.strip().replace(" ", "") for n in ("robots", "googlebot", "bingbot") for d in p.meta.get(n, "").lower().split(",")}
        snip = sorted(d for d in directives if d in ("nosnippet", "max-snippet:0"))
        results["snippet_controls"].append((not snip, name, ", ".join(snip)))
        results["noindex"].append(("noindex" not in directives and "none" not in directives, name, "noindex" if "noindex" in directives or "none" in directives else ""))


def summarize(results):
    rows = []
    for cid, desc, scope in CHECKS:
        r = results[cid]
        fails = [(w, d) for ok, w, d in r if not ok]
        rows.append((cid, desc, not fails, "; ".join(f"{w}: {d}" if d else w for w, d in fails)))
    passed = sum(1 for r in rows if r[2])
    return rows, passed, len(rows)


# Extra checks: tiered and exported, but not part of the 19-check score.
EXTRA_CHECKS = [
    ("robots_root", "robots.txt sits at the site root", "site"),
    ("jsonld_visible", "Key JSON-LD values (name, phone, address, FAQ text) are visible on the page", "page"),
    ("snippet_controls", "No nosnippet or max-snippet:0 that hides text from search and AI answers", "page"),
    ("noindex", "No noindex on pages meant to be found", "page"),
]
ALL_CHECKS = CHECKS + EXTRA_CHECKS


def findings(results, checks=None):
    """Failing results as sorted dicts with url, check, tier, issue, fix."""
    out = []
    for cid, _, _ in (checks or CHECKS):
        tier, fix = TIERS[cid]
        for ok, where, det in results.get(cid, []):
            if not ok:
                out.append({"url": where, "check": cid, "tier": tier, "issue": det or "fails", "fix": fix})
    out.sort(key=lambda f: (TIER_ORDER[f["tier"]], f["check"], f["url"], f["issue"]))
    return out


def health(results, checks=None):
    """Percent of checks with no Error-tier finding (Warn and Notice do not count)."""
    checks = checks or CHECKS
    bad = sum(1 for cid, _, _ in checks if TIERS[cid][0] == "Error" and any(not r[0] for r in results.get(cid, [])))
    return round(100 * (len(checks) - bad) / len(checks))


def bot_table(site):
    robots = Path(site) / "robots.txt"
    if not robots.exists():
        return [(kind, b, "allowed (no robots.txt)") for kind, bots in (("search/answer", SEARCH_BOTS), ("training", TRAINING_BOTS)) for b in bots]
    txt = robots.read_text(encoding="utf-8")
    return [(kind, b, "blocked" if robots_blocked(txt, b) else "allowed")
            for kind, bots in (("search/answer", SEARCH_BOTS), ("training", TRAINING_BOTS)) for b in bots]


def compare(prev, cur):
    """Return (new, fixed, unchanged) keyed on url + check + issue."""
    key = lambda f: (f["url"], f["check"], f["issue"])
    pk, ck = {key(f): f for f in prev}, {key(f): f for f in cur}
    srt = lambda d, ks: [d[k] for k in sorted(ks)]
    return srt(ck, ck.keys() - pk.keys()), srt(pk, pk.keys() - ck.keys()), srt(ck, ck.keys() & pk.keys())


def render(name, rows, passed, total, found=None, hp=None, bots=None, diff=None):
    md = [f"# SEO + GEO audit: {name}", "", f"**Score: {passed}/{total} checks passed ({round(100 * passed / total)}%)**", ""]
    if hp is not None:
        md += [f"**Health: {hp}%** (share of checks with no Error finding; Warn and Notice do not lower it)", ""]
    md += ["## Readiness (we control)", "", "| Check | Tier | Rule | Result | Where it fails |", "|---|---|---|---|---|"]
    for cid, desc, ok, det in rows:
        md.append(f"| {cid} | {TIERS[cid][0]} | {desc} | {'PASS' if ok else 'FAIL'} | {det} |")
    if found:
        md += ["", "### Findings and fixes", "", "| Tier | URL | Check | Issue | Fix |", "|---|---|---|---|---|"]
        md += [f"| {f['tier']} | {f['url']} | {f['check']} | {f['issue']} | {f['fix']} |" for f in found]
    if bots:
        md += ["", "### AI and search bot access (robots.txt)", "", "| Kind | Bot | Access |", "|---|---|---|"]
        md += [f"| {k} | {b} | {a} |" for k, b, a in bots]
    if diff:
        new, fixed, same = diff
        md += ["", "### Compared with the previous run", "", f"New: {len(new)}, fixed: {len(fixed)}, unchanged: {len(same)}", ""]
        md += [f"- NEW {f['tier']} {f['url']} {f['check']}: {f['issue']}" for f in new]
        md += [f"- FIXED {f['tier']} {f['url']} {f['check']}: {f['issue']}" for f in fixed]
    md += ["", "## Visibility (measured, not promised)", "",
           "This audit does not measure rankings, traffic or AI citations. Those come from Search Console,",
           "Bing Webmaster Tools and a logged AI-answer check, reported separately as measured results.",
           "", "These are good-practice checks. A high score does not guarantee rankings or AI citations."]
    return "\n".join(md) + "\n"


def write_exports(out, label, found):
    import csv
    (out / f"findings_{label}.json").write_text(json.dumps(found, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    with open(out / f"findings_{label}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["url", "check", "tier", "issue", "fix"], lineterminator="\n")
        w.writeheader()
        w.writerows(found)


def run(site, prev=None, out=None):
    site = Path(site)
    results = audit(site)
    rows, passed, total = summarize(results)
    found = findings(results, ALL_CHECKS)
    hp = health(results, ALL_CHECKS)
    diff = compare(prev, found) if prev is not None else None
    label = site.name.replace("site_", "") or site.name
    out = Path(out) if out else Path(__file__).parent / "demo" / "out"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"report_{label}.md").write_text(render(site.name, rows, passed, total, found, hp, bot_table(site), diff), encoding="utf-8")
    write_exports(out, label, found)
    return rows, passed, total, label


def main(argv):
    args = argv[1:]
    prev = None
    if "--compare" in args:
        i = args.index("--compare")
        if i + 1 >= len(args):
            print("usage: python3 audit.py <site_folder> [--compare prev.json]")
            return 2
        prev = json.loads(Path(args[i + 1]).read_text(encoding="utf-8"))
        del args[i:i + 2]
    if len(args) != 1:
        print("usage: python3 audit.py <site_folder> [--compare prev.json]")
        return 2
    rows, passed, total, label = run(args[0], prev)
    w = max(len(r[0]) for r in rows)
    print(f"{'CHECK'.ljust(w)}  TIER    RESULT  DETAIL")
    for cid, _, ok, det in rows:
        print(f"{cid.ljust(w)}  {TIERS[cid][0].ljust(6)}  {'PASS' if ok else 'FAIL'}    {det}")
    print(f"\nScore: {passed}/{total} ({round(100 * passed / total)}%)  ->  demo/out/report_{label}.md")
    if prev is not None:
        new, fixed, same = compare(prev, json.loads((Path(__file__).parent / "demo" / "out" / f"findings_{label}.json").read_text()))
        print(f"Compare: {len(new)} new, {len(fixed)} fixed, {len(same)} unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

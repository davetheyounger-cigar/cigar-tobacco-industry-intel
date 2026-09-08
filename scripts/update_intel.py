#!/usr/bin/env python3

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "intel.json"

# ------------------------------------------------------------
# CORE SEED INTELLIGENCE
# These are retained even if an automated source is unavailable.
# ------------------------------------------------------------

SEED = [
    {
        "id": "seed-cuba-paradox",
        "priority": "critical",
        "country": "Cuba",
        "stage": "Supply",
        "source": "Cigar Journal",
        "title": "Cuba's Cigar Paradox",
        "description": "Record Habanos revenue is occurring alongside shrinking physical supply and continuing production/infrastructure constraints.",
        "url": "https://www.cigarjournal.com/cubas-cigar-paradox/",
        "date": "2026-09-08",
        "automatic": False
    },
    {
        "id": "seed-pinar-del-rio",
        "priority": "critical",
        "country": "Cuba",
        "stage": "Field / crop",
        "source": "Granma",
        "title": "Pinar del Río campaign closes with 11,400+ hectares",
        "description": "The 2025–26 campaign finished below the original plan after rain, energy and drought problems.",
        "url": "https://www.granma.cu/cuba/2026-03-16/con-mas-de-11-400-hectareas-cierran-siembras-de-campana-tabacalera-en-pinar-del-rio-15-03-2026-16-03-51",
        "date": "2026-03-16",
        "automatic": False
    },
    {
        "id": "seed-dr-drew",
        "priority": "high",
        "country": "Dominican Republic",
        "stage": "Factory",
        "source": "Drew Estate",
        "title": "Drew Estate announces Drew Dominicana",
        "description": "A planned 73,000 sq. ft. compound and exclusive farm in Villa González would be Drew Estate's first production outside Nicaragua.",
        "url": "https://drewestate.com/411-news/announcing-drew-dominicana-new-drew-estate-farm-and-factory/",
        "date": "2026-04-17",
        "automatic": False
    },
    {
        "id": "seed-dr-irrigation",
        "priority": "high",
        "country": "Dominican Republic",
        "stage": "Field / crop",
        "source": "Dominican Presidency",
        "title": "Tobacco irrigation modernization",
        "description": "Irrigation technology, training and technical support are being strengthened for tobacco growers.",
        "url": "https://presidencia.gob.do/noticias/tnr-e-intabaco-firman-acuerdo-para-promover-tecnificacion-del-riego-y-fortalecer",
        "date": "2026-07-08",
        "automatic": False
    },
    {
        "id": "seed-dr-acreage",
        "priority": "high",
        "country": "Dominican Republic",
        "stage": "Field / crop",
        "source": "INTABACO",
        "title": "2025–26 harvest: 160,000+ tareas planted",
        "description": "INTABACO reported more than 160,000 tareas planted across 29 tobacco zones and 15 provinces.",
        "url": "https://intabaco.gob.do/noticias/intabaco-inicia-cosecha-tabacalera-2025-2026-con-siembra-de-mas-de-160-mil-tareas/",
        "date": "2026",
        "automatic": False
    },
    {
        "id": "seed-ni-plasencia",
        "priority": "high",
        "country": "Nicaragua",
        "stage": "Blending / release",
        "source": "Cigar Journal",
        "title": "Plasencia — Born of This Land",
        "description": "A major brand-evolution announcement. Watch for subsequent blend, tobacco, production and distribution implications.",
        "url": "https://www.cigarjournal.com/plasencia-cigars-unveils-the-next-chapter-of-its-brand-evolution/",
        "date": "2026-09-07",
        "automatic": False
    },
    {
        "id": "seed-climate",
        "priority": "medium",
        "country": "Global",
        "stage": "Weather",
        "source": "Reuters",
        "title": "Strong El Niño developing for 2026–27",
        "description": "A strong El Niño could alter rainfall and temperature patterns across tropical agricultural regions. Climate watch only; not proof of tobacco damage.",
        "url": "https://www.reuters.com/business/environment/strong-el-nino-developing-weather-agencies-say-2026-08-18/",
        "date": "2026-08-18",
        "automatic": False
    },
    {
        "id": "seed-san-juan",
        "priority": "medium",
        "country": "Dominican Republic",
        "stage": "Field / crop",
        "source": "INTABACO",
        "title": "San Juan Valley 2026–27 crop planning",
        "description": "Planning includes financing, technical assistance, commercialization and producer training.",
        "url": "https://intabaco.gob.do/noticias/fortalecen-acciones-para-el-cultivo-de-tabaco-en-el-valle-de-san-juan/",
        "date": "2026",
        "automatic": False
    },
    {
        "id": "seed-pest",
        "priority": "medium",
        "country": "Dominican Republic",
        "stage": "Field / crop",
        "source": "INTABACO",
        "title": "Integrated pest-management operations",
        "description": "Agricultural-veda operations in Montecristi are part of the crop-protection picture.",
        "url": "https://intabaco.gob.do/noticias/intabaco-participa-en-operativos-de-veda-agricola-2026/",
        "date": "2026",
        "automatic": False
    },
    {
        "id": "seed-mildew",
        "priority": "medium",
        "country": "Global",
        "stage": "Curing / fermentation",
        "source": "Industrial Crops and Products",
        "title": "Post-harvest mildew risk research",
        "description": "Research proposes a Mold Risk Index for post-harvest cigar-tobacco conditions, reinforcing the importance of humidity and storage controls.",
        "url": "https://www.sciencedirect.com/science/article/pii/S0926669026012604",
        "date": "2026-08",
        "automatic": False
    }
]

# ------------------------------------------------------------
# SOURCES
# ------------------------------------------------------------

RSS_FEEDS = [
    ("Cigar Snob", "https://www.cigarsnobmag.com/feed/"),
    ("Developing Palates", "https://developingpalates.com/feed/")
]

COUNTRY_TERMS = {
    "Nicaragua": [
        "nicaragua", "esteli", "estelí", "jalapa", "condega",
        "con dega", "ometepe", "jalapa valley", "estelí valley"
    ],
    "Honduras": [
        "honduras", "danli", "danlí", "jamastran", "jamastrán",
        "talanga", "copan", "copán"
    ],
    "Dominican Republic": [
        "dominican republic", "dominican tobacco", "villa gonzalez",
        "villa gonzález", "santiago", "mao", "san juan"
    ],
    "Ecuador": [
        "ecuador", "los rios", "los ríos", "quevedo",
        "ecuadorian habano", "ecuadorian sumatra"
    ],
    "Mexico": [
        "mexico", "méxico", "san andres tuxtla",
        "san andrés tuxtla", "nayarit", "san andres", "san andrés"
    ],
    "Brazil": [
        "brazil", "bahia", "bahía", "brazilian mata fina"
    ],
    "Cuba": [
        "cuba", "pinar del rio", "pinar del río", "vuelta abajo",
        "san luis", "san juan y martinez", "san juan y martínez",
        "habanos"
    ],
    "United States": [
        "connecticut", "pennsylvania", "kentucky", "tennessee",
        "connecticut broadleaf", "connecticut shade"
    ]
}

# Terms that establish that an article is relevant to the premium-cigar
# supply chain rather than generic tobacco/smoking news.
CIGAR_RELEVANCE = [
    "premium cigar", "premium cigars", "handmade cigar", "handmade cigars",
    "cigar tobacco", "cigar leaf", "cigar wrapper", "cigar binder",
    "cigar filler", "wrapper leaf", "binder leaf", "filler leaf",
    "cigar factory", "cigar manufacturer", "cigar production",
    "cigar blend", "cigar release", "cigar line", "cigar brand",
    "cigar company", "cigar industry", "tobacco farm", "tobacco field",
    "tobacco harvest", "tobacco crop", "tobacco curing",
    "tobacco fermentation", "tobacco aging", "tobacco shortage",
    "tobacco supply", "tobacco acreage", "tobacco disease",
    "tobacco pest", "tobacco mildew", "tobacco mold",
    "tobacco variety", "tobacco seed", "leaf tobacco"
]

# Generic tobacco/cigarette/public-health terms. These are excluded unless
# the same story also contains strong premium-cigar relevance.
EXCLUDE_GENERIC = [
    "cigarette consumption", "cigarette sales", "cigarette smoking",
    "smoking prevalence", "smoking cessation", "smoking rates",
    "e-cigarette", "e-cigarettes", "electronic cigarette", "vaping",
    "vape", "nicotine pouch", "nicotine pouches", "smokeless tobacco",
    "cigarette tax", "cigarette taxes", "cigarette ban",
    "smoking ban", "public health", "lung cancer", "cdc",
    "heart disease", "tobacco control", "youth tobacco",
    "youth smoking", "teen smoking", "cigarette excise"
]

STAGE_TERMS = {
    "Field / crop": [
        "crop", "harvest", "tobacco leaf", "leaf", "farm", "farmer",
        "planting", "acre", "acreage", "drought", "rainfall", "rain",
        "flood", "hurricane", "storm", "disease", "pest", "blue mold",
        "mildew", "virus", "nematode", "irrigation", "soil", "seed"
    ],
    "Curing / fermentation": [
        "curing", "curing barn", "fermentation", "ferment",
        "barn", "humidity", "mold", "mildew", "post-harvest",
        "aging tobacco", "storage"
    ],
    "Supply": [
        "shortage", "supply", "inventory", "availability", "allocation",
        "leaf supply", "exports", "export", "shipping", "tariff",
        "price increase", "cost", "raw material"
    ],
    "Factory": [
        "factory", "manufacturing", "production facility",
        "plant", "capacity", "facility", "labor", "workforce",
        "expansion", "closure", "shutdown"
    ],
    "Blending / release": [
        "release", "ships", "ship", "launch", "blend", "vitola",
        "limited edition", "new cigar", "new line", "sampler",
        "production cigar"
    ],
    "Ownership / strategy": [
        "acquire", "acquisition", "merger", "partnership",
        "ownership", "investment", "expansion", "strategy",
        "appoints", "ceo", "joint venture"
    ]
}

CRITICAL_TERMS = [
    "crop failure", "major crop loss", "factory fire", "factory closure",
    "factory shutdown", "hurricane", "major hurricane", "drought emergency",
    "major flood", "blue mold outbreak", "major disease outbreak",
    "major pest outbreak", "leaf shortage", "tobacco shortage",
    "supply disruption", "production halted", "production suspended",
    "acquisition", "merger", "ownership change"
]

HIGH_TERMS = [
    "significant crop loss", "crop damage", "harvest damage",
    "hurricane", "drought", "flood", "disease outbreak",
    "pest outbreak", "mildew outbreak", "new factory",
    "factory expansion", "production expansion", "production reduction",
    "capacity expansion", "tobacco shortage", "supply disruption",
    "leaf shortage", "new farm", "exclusive farm",
    "acquisition", "ownership", "major partnership"
]

MEDIUM_TERMS = [
    "harvest", "crop", "farm", "factory", "production",
    "irrigation", "curing", "fermentation", "mold", "mildew",
    "new tobacco", "tobacco variety", "new cigar", "new blend",
    "limited edition", "launch", "ships", "partnership",
    "export", "inventory", "research"
]


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Cigar-Tobacco-Industry-Intel/15.1"
        }
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def clean(text):
    return re.sub(
        r"\s+",
        " ",
        re.sub(r"<[^>]+>", " ", text or "")
    ).strip()


def parse_feed(source, url):
    results = []

    try:
        root = ET.fromstring(fetch(url))

        for item in root.findall(".//item")[:50]:
            title = clean(item.findtext("title"))
            link = clean(item.findtext("link"))
            description = clean(item.findtext("description"))
            pub_date = clean(item.findtext("pubDate"))

            if title and link:
                results.append({
                    "source": source,
                    "title": title,
                    "description": description[:1000],
                    "url": link,
                    "date": pub_date
                })

    except Exception as error:
        print(f"RSS failed for {source}: {error}")

    return results


def parse_google_news(query):
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    return parse_feed("Google News Discovery", url)


def contains_any(text, terms):
    return any(term in text for term in terms)


def classify(title, description, source=""):
    text = (title + " " + description).lower()

    # Country
    country = "Global"
    for name, terms in COUNTRY_TERMS.items():
        if contains_any(text, terms):
            country = name
            break

    # Stage
    stage = "Industry"
    stage_hits = []

    for name, terms in STAGE_TERMS.items():
        hits = [term for term in terms if term in text]
        if hits:
            stage_hits.append((len(hits), name))

    if stage_hits:
        stage = sorted(stage_hits, reverse=True)[0][1]

    # Priority
    if contains_any(text, CRITICAL_TERMS):
        priority = "critical"
    elif contains_any(text, HIGH_TERMS):
        priority = "high"
    elif contains_any(text, MEDIUM_TERMS):
        priority = "medium"
    else:
        priority = "low"

    # Stronger primary-source bias.
    source_lower = source.lower()
    if any(x in source_lower for x in [
        "drew estate", "plasencia", "intabaco", "presidencia",
        "premium cigar association", "jre tobacco", "my father",
        "aganorsa", "a.j. fernandez", "oliva", "arturo fuente",
        "la flor dominicana", "habanos"
    ]):
        if priority == "low":
            priority = "medium"

    return country, stage, priority


def is_relevant(title, description):
    text = (title + " " + description).lower()

    cigar_hits = sum(term in text for term in CIGAR_RELEVANCE)
    generic_hits = sum(term in text for term in EXCLUDE_GENERIC)

    # Hard exclusion for generic cigarette/public-health stories unless
    # they contain multiple strong cigar-industry signals.
    if generic_hits >= 1 and cigar_hits < 2:
        return False

    # Require at least one meaningful premium-cigar/upstream signal.
    if cigar_hits == 0:
        return False

    return True


def normalize_date(value):
    if not value:
        return ""

    # Keep the original value if parsing is unnecessary; dashboard can display it.
    return value[:80]


def make_id(title, url):
    basis = (title + "|" + url).lower()
    return "auto-" + re.sub(r"[^a-z0-9]+", "-", basis).strip("-")[:110]


def make_item(article):
    title = article["title"]
    description = article["description"]
    source = article["source"]
    url = article["url"]

    country, stage, priority = classify(
        title,
        description,
        source
    )

    return {
        "id": make_id(title, url),
        "priority": priority,
        "country": country,
        "stage": stage,
        "source": source,
        "title": title,
        "description": description[:600],
        "url": url,
        "date": normalize_date(article.get("date", "")),
        "automatic": True,
        "verification": "DISCOVERY — verify important signals against a primary source."
    }


def main():
    print("Starting V15.1 premium-cigar intelligence update...")

    # Load existing database so the system does not lose useful historical items.
    existing = []
    if OUT.exists():
        try:
            payload = json.loads(
                OUT.read_text(encoding="utf-8")
            )
            existing = payload.get("items", [])
        except Exception as error:
            print("Existing database could not be read:", error)

    # Keep seeds exactly as defined above.
    final = {item["id"]: item for item in SEED}

    # Preserve only relevant existing automatic items.
    for item in existing:
        if not item.get("automatic"):
            final[item.get("id")] = item
            continue

        title = item.get("title", "")
        description = item.get("description", "")

        if is_relevant(title, description):
            final[item.get("id") or make_id(title, item.get("url", ""))] = item

    discovered = []

    # Direct industry feeds.
    for source, feed_url in RSS_FEEDS:
        print("Checking:", source)
        discovered.extend(parse_feed(source, feed_url))

    # Targeted upstream and production discovery.
    queries = [
        '"Nicaragua" tobacco cigar farm harvest disease factory',
        '"Honduras" tobacco cigar farm harvest disease factory',
        '"Dominican Republic" tobacco cigar farm harvest irrigation factory',
        '"Ecuador" tobacco wrapper cigar farm harvest',
        '"Mexico" tobacco cigar farm harvest San Andres',
        '"Brazil" tobacco cigar leaf Bahia',
        '"Cuba" Pinar del Rio tobacco harvest cigar supply factory',
        '"Connecticut" Broadleaf Shade tobacco cigar crop',
        '"premium cigar" tobacco leaf shortage supply',
        '"premium cigar" factory expansion production',
        '"cigar tobacco" disease pest crop',
        '"cigar tobacco" hurricane drought flood',
        '"cigar factory" acquisition partnership expansion',
        '"cigar release" new blend production'
    ]

    for query in queries:
        print("Checking:", query)
        discovered.extend(parse_google_news(query))

    accepted = 0
    rejected = 0

    for article in discovered:
        if not is_relevant(
            article["title"],
            article["description"]
        ):
            rejected += 1
            continue

        item = make_item(article)
        final[item["id"]] = item
        accepted += 1

    # Convert to list and remove duplicates by URL.
    by_url = {}
    for item in final.values():
        url = item.get("url", "")
        if url:
            by_url[url] = item

    items = list(by_url.values())

    # Priority and recency sorting.
    priority_rank = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3
    }

    items.sort(
        key=lambda x: (
            priority_rank.get(x.get("priority", "low"), 9),
            str(x.get("date", ""))
        )
    )

    # Preserve all seeds, then keep the newest 300 relevant automatic items.
    seed_ids = {item["id"] for item in SEED}
    seed_items = [x for x in items if x.get("id") in seed_ids]
    automatic_items = [x for x in items if x.get("id") not in seed_ids]

    automatic_items.sort(
        key=lambda x: str(x.get("date", "")),
        reverse=True
    )

    automatic_items = automatic_items[:300]

    final_items = seed_items + automatic_items

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "github-actions-v15.1",
        "filter": {
            "focus": "premium cigar tobacco supply chain",
            "excluded": "generic cigarette, smoking-prevalence, vaping, nicotine and public-health stories unless directly tied to premium cigars",
            "verification": "Automated items are discovery leads, not confirmed intelligence."
        },
        "stats": {
            "accepted_this_run": accepted,
            "rejected_as_irrelevant": rejected,
            "total_database_items": len(final_items)
        },
        "items": final_items,
        "source_feeds": [
            {
                "name": name,
                "url": url
            }
            for name, url in RSS_FEEDS
        ]
    }

    OUT.write_text(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print(
        f"V15.1 complete: {len(final_items)} relevant items retained; "
        f"{accepted} new discovery items accepted; "
        f"{rejected} discovery items rejected."
    )


if __name__ == "__main__":
    main()

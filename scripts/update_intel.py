#!/usr/bin/env python3

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "intel.json"

# Keep the manually curated intelligence anchors.
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
        "url": "https://www.granma.cu/cuba/2026-03-16/con-mas-de-11.400-hectareas-cierran-siembras-de-campana-tabacalera-en-pinar-del-rio-15-03-2026-16-03-51",
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

RSS_FEEDS = [
    ("Cigar Snob", "https://www.cigarsnobmag.com/feed/"),
    ("Developing Palates", "https://developingpalates.com/feed/")
]

# Terms that identify actual premium-cigar/tobacco supply-chain relevance.
STRONG = [
    "premium cigar", "premium cigars", "handmade cigar", "handmade cigars",
    "cigar tobacco", "cigar leaf", "cigar wrapper", "wrapper leaf",
    "binder leaf", "filler leaf", "cigar factory", "cigar manufacturer",
    "cigar production", "cigar blend", "cigar release", "cigar line",
    "cigar brand", "cigar company", "cigar industry", "tobacco farm",
    "tobacco field", "tobacco harvest", "tobacco crop", "tobacco curing",
    "tobacco fermentation", "tobacco aging", "tobacco shortage",
    "tobacco supply", "tobacco acreage", "tobacco disease", "tobacco pest",
    "tobacco mildew", "tobacco mold", "tobacco variety", "tobacco seed",
    "leaf tobacco", "broadleaf", "connecticut shade", "corojo",
    "criollo", "havanensis", "san andrés", "san andres", "mata fina"
]

# Generic stories are excluded unless they have several strong cigar signals.
GENERIC = [
    "cigarette consumption", "cigarette sales", "cigarette smoking",
    "smoking prevalence", "smoking cessation", "smoking rates",
    "e-cigarette", "e-cigarettes", "electronic cigarette", "vaping",
    "vape", "nicotine pouch", "nicotine pouches", "smokeless tobacco",
    "cigarette tax", "cigarette taxes", "cigarette ban", "smoking ban",
    "public health", "lung cancer", "cdc", "heart disease",
    "tobacco control", "youth tobacco", "youth smoking", "teen smoking"
]

STAGE = {
    "Field / crop": [
        "crop", "harvest", "tobacco leaf", "leaf", "farm", "farmer",
        "planting", "acre", "acreage", "drought", "rainfall", "rain",
        "flood", "hurricane", "storm", "disease", "pest", "blue mold",
        "mildew", "virus", "nematode", "irrigation", "soil", "seed"
    ],
    "Curing / fermentation": [
        "curing", "curing barn", "fermentation", "ferment", "barn",
        "humidity", "mold", "mildew", "post-harvest", "aging tobacco",
        "storage"
    ],
    "Supply": [
        "shortage", "supply", "inventory", "availability", "allocation",
        "leaf supply", "exports", "export", "shipping", "tariff",
        "price increase", "raw material"
    ],
    "Factory": [
        "factory", "manufacturing", "production facility", "plant",
        "capacity", "facility", "labor", "workforce", "expansion",
        "closure", "shutdown"
    ],
    "Blending / release": [
        "release", "ships", "ship", "blend", "vitola", "limited edition",
        "new cigar", "new line", "production cigar"
    ],
    "Ownership / strategy": [
        "acquire", "acquisition", "merger", "partnership", "ownership",
        "investment", "expansion", "joint venture"
    ]
}

CRITICAL = [
    "crop failure", "major crop loss", "factory fire", "factory closure",
    "factory shutdown", "production halted", "production suspended",
    "leaf shortage", "tobacco shortage", "supply disruption",
    "major disease outbreak", "major pest outbreak", "blue mold outbreak",
    "major hurricane", "drought emergency", "major flood", "acquisition",
    "merger", "ownership change"
]

HIGH = [
    "significant crop loss", "crop damage", "harvest damage",
    "hurricane", "drought", "flood", "disease outbreak", "pest outbreak",
    "mildew outbreak", "new factory", "factory expansion",
    "production expansion", "production reduction", "capacity expansion",
    "tobacco shortage", "supply disruption", "leaf shortage", "new farm",
    "exclusive farm", "acquisition", "ownership", "major partnership"
]

MEDIUM = [
    "harvest", "crop", "farm", "factory", "production", "irrigation",
    "curing", "fermentation", "mold", "mildew", "tobacco variety",
    "new cigar", "new blend", "limited edition", "launch", "ships",
    "partnership", "export", "inventory", "research"
]


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Cigar-Tobacco-Industry-Intel/15.2"}
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()


def clean(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip()


def parse_date(value):
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def parse_feed(source, url):
    out = []
    try:
        root = ET.fromstring(fetch(url))
        for item in root.findall(".//item")[:60]:
            title = clean(item.findtext("title"))
            link = clean(item.findtext("link"))
            description = clean(item.findtext("description"))
            pub = clean(item.findtext("pubDate"))
            if title and link:
                out.append({
                    "source": source,
                    "title": title,
                    "description": description[:1500],
                    "url": link,
                    "date_raw": pub,
                    "date_dt": parse_date(pub)
                })
    except Exception as error:
        print(f"RSS failed for {source}: {error}")
    return out


def google_news(query):
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    return parse_feed("Google News Discovery", url)


def count_hits(text, terms):
    return sum(1 for term in terms if term in text)


def is_relevant(title, description):
    text = (title + " " + description).lower()
    strong_hits = count_hits(text, STRONG)
    generic_hits = count_hits(text, GENERIC)

    # Hard gate: a generic cigarette/public-health story must have
    # multiple strong premium-cigar signals.
    if generic_hits and strong_hits < 3:
        return False

    # No premium-cigar/tobacco supply-chain signal = reject.
    if strong_hits < 1:
        return False

    return True


def classify(title, description, source):
    text = (title + " " + description).lower()
    stage_hits = []

    for name, terms in STAGE.items():
        hits = count_hits(text, terms)
        if hits:
            stage_hits.append((hits, name))

    stage = max(stage_hits)[1] if stage_hits else "Industry"

    critical_hits = count_hits(text, CRITICAL)
    high_hits = count_hits(text, HIGH)
    medium_hits = count_hits(text, MEDIUM)

    # Critical requires either an explicit severe event plus a strong
    # cigar/tobacco signal, or two independent severe signals.
    strong_hits = count_hits(text, STRONG)

    if critical_hits >= 2 or (critical_hits >= 1 and strong_hits >= 2):
        priority = "critical"
    elif high_hits >= 2 or (high_hits >= 1 and strong_hits >= 2):
        priority = "high"
    elif medium_hits >= 1:
        priority = "medium"
    else:
        priority = "low"

    # Automatic discovery is deliberately capped at HIGH unless a story
    # contains unmistakable multi-signal disruption language.
    if priority == "critical" and critical_hits < 2:
        priority = "high"

    # Never allow Google News discovery to make something critical from
    # a single keyword.
    if source == "Google News Discovery" and priority == "critical":
        priority = "high"

    country = "Global"
    country_terms = {
        "Nicaragua": ["nicaragua", "esteli", "estelí", "jalapa", "condega", "con dega"],
        "Honduras": ["honduras", "danli", "danlí", "jamastran", "jamastrán", "talanga"],
        "Dominican Republic": ["dominican republic", "villa gonzalez", "villa gonzález", "mao", "san juan"],
        "Ecuador": ["ecuador", "los rios", "los ríos", "quevedo"],
        "Mexico": ["mexico", "méxico", "san andres tuxtla", "san andrés tuxtla"],
        "Brazil": ["brazil", "bahia", "bahía", "mata fina"],
        "Cuba": ["cuba", "pinar del rio", "pinar del río", "vuelta abajo", "habanos"],
        "United States": ["connecticut", "pennsylvania", "kentucky", "tennessee", "connecticut broadleaf"]
    }

    for name, terms in country_terms.items():
        if any(term in text for term in terms):
            country = name
            break

    return country, stage, priority


def make_id(title, url):
    return "auto-" + re.sub(r"[^a-z0-9]+", "-", (title + "|" + url).lower()).strip("-")[:110]


def main():
    print("Starting V15.2 intelligence update...")

    existing = []
    if OUT.exists():
        try:
            existing = json.loads(
                OUT.read_text(encoding="utf-8")
            ).get("items", [])
        except Exception as error:
            print("Could not read existing database:", error)

    # Keep curated anchors and only relevant recent automatic items.
    final = {x["id"]: x for x in SEED}
    cutoff = datetime.now(timezone.utc) - timedelta(days=45)

    for item in existing:
        if not item.get("automatic"):
            final[item.get("id")] = item
            continue

        if not is_relevant(item.get("title", ""), item.get("description", "")):
            continue

        # Old automatic discovery items are removed. This prevents a 2023
        # article surfaced by Google News from becoming today's signal.
        raw = item.get("date", "")
        dt = parse_date(raw)
        if dt and dt < cutoff:
            continue

        final[item.get("id") or make_id(item.get("title", ""), item.get("url", ""))] = item

    queries = [
        '"premium cigar" tobacco farm harvest',
        '"cigar tobacco" crop disease pest',
        '"cigar tobacco" hurricane drought flood',
        '"premium cigar" tobacco shortage supply',
        '"cigar factory" production expansion',
        '"cigar factory" closure shutdown',
        '"premium cigar" acquisition partnership',
        '"premium cigar" new factory new farm',
        '"Nicaragua" cigar tobacco harvest farm',
        '"Honduras" cigar tobacco harvest farm',
        '"Dominican Republic" cigar tobacco harvest farm',
        '"Ecuador" cigar tobacco wrapper harvest',
        '"Mexico" cigar tobacco San Andres harvest',
        '"Brazil" cigar tobacco Bahia leaf',
        '"Cuba" Pinar del Rio tobacco harvest Habanos',
        '"Connecticut Broadleaf" cigar tobacco crop'
    ]

    discovered = []
    for q in queries:
        print("Checking:", q)
        discovered.extend(google_news(q))

    for source, feed_url in RSS_FEEDS:
        print("Checking:", source)
        discovered.extend(parse_feed(source, feed_url))

    accepted = 0
    rejected = 0
    stale = 0

    for article in discovered:
        title = article["title"]
        description = article["description"]

        if not is_relevant(title, description):
            rejected += 1
            continue

        # For automatic discovery, require a real recent publication date.
        dt = article.get("date_dt")
        if dt is None or dt < cutoff:
            stale += 1
            continue

        country, stage, priority = classify(
            title, description, article["source"]
        )

        item = {
            "id": make_id(title, article["url"]),
            "priority": priority,
            "country": country,
            "stage": stage,
            "source": article["source"],
            "title": title,
            "description": description[:600],
            "url": article["url"],
            "date": dt.isoformat(),
            "automatic": True,
            "verification": "DISCOVERY — verify important signals against a primary source."
        }

        final[item["id"]] = item
        accepted += 1

    # Deduplicate URLs.
    by_url = {}
    for item in final.values():
        if item.get("url"):
            by_url[item["url"]] = item

    items = list(by_url.values())

    rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    # Curated seeds remain first and can be older. Automatic discoveries are
    # recent-only and sorted newest first within priority.
    seed_ids = {x["id"] for x in SEED}
    seeds = [x for x in items if x.get("id") in seed_ids]
    autos = [x for x in items if x.get("id") not in seed_ids]

    autos.sort(
        key=lambda x: (
            rank.get(x.get("priority", "low"), 9),
            x.get("date", "")
        ),
        reverse=False
    )

    # Re-sort with priority ascending, date descending.
    autos.sort(
        key=lambda x: (
            rank.get(x.get("priority", "low"), 9),
            x.get("date", "")
        ),
        reverse=False
    )

    # For each priority, newest first.
    grouped = []
    for p in ["critical", "high", "medium", "low"]:
        group = [x for x in autos if x.get("priority") == p]
        group.sort(key=lambda x: x.get("date", ""), reverse=True)
        grouped.extend(group)

    autos = grouped[:300]

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "github-actions-v15.2",
        "filter": {
            "focus": "premium cigar tobacco supply chain",
            "automatic_window_days": 45,
            "generic_exclusions": "cigarette consumption, smoking prevalence, vaping, nicotine and public-health stories unless strongly tied to premium cigars",
            "automatic_critical_cap": "Google News discovery cannot create CRITICAL priority; critical status is reserved for curated intelligence.",
            "verification": "Automatic items are discovery leads, not confirmed intelligence."
        },
        "stats": {
            "accepted_this_run": accepted,
            "rejected_as_irrelevant": rejected,
            "rejected_as_stale": stale,
            "total_database_items": len(seeds) + len(autos)
        },
        "items": seeds + autos,
        "source_feeds": [
            {"name": name, "url": url}
            for name, url in RSS_FEEDS
        ]
    }

    OUT.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(
        f"V15.2 complete: {len(seeds) + len(autos)} items retained; "
        f"{accepted} new items accepted; "
        f"{rejected} rejected as irrelevant; "
        f"{stale} rejected as stale."
    )


if __name__ == "__main__":
    main()

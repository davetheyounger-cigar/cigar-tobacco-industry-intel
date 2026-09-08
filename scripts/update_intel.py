#!/usr/bin/env python3

import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "intel.json"


FEEDS = [
    ("Cigar Snob", "https://www.cigarsnobmag.com/feed/"),
    ("Developing Palates", "https://developingpalates.com/feed/"),
]


QUERIES = [
    ("Nicaragua", "Nicaragua tobacco cigar farm harvest disease factory"),
    ("Honduras", "Honduras tobacco cigar farm harvest disease factory"),
    ("Dominican Republic", "Dominican Republic tobacco cigar farm harvest disease factory"),
    ("Ecuador", "Ecuador tobacco cigar farm harvest disease"),
    ("Mexico", "Mexico tobacco cigar farm harvest disease factory"),
    ("Brazil", "Brazil tobacco cigar farm harvest disease"),
    ("Cuba", "Cuba tobacco harvest cigar factory supply Habanos"),
    ("United States", "United States tobacco cigar manufacturing agriculture"),
]


def fetch(url):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Cigar-Tobacco-Industry-Intel/1.0"}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def clean_text(value):
    return re.sub(r"<[^>]+>", " ", value or "").strip()


def parse_rss(xml_data):
    root = ET.fromstring(xml_data)
    results = []

    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        description = item.findtext("description") or ""
        pub_date = item.findtext("pubDate") or ""

        results.append({
            "title": title.strip(),
            "link": link.strip(),
            "description": clean_text(description),
            "pub_date": pub_date.strip()
        })

    return results


def classify(title, description):
    text = (title + " " + description).lower()

    if any(word in text for word in [
        "hurricane", "drought", "flood", "rainfall",
        "weather", "el niño", "el nino", "wind",
        "storm", "temperature"
    ]):
        stage = "WEATHER"

    elif any(word in text for word in [
        "disease", "mold", "mildew", "pest",
        "worm", "virus", "fungus", "insect"
    ]):
        stage = "DISEASE"

    elif any(word in text for word in [
        "farm", "field", "planting", "crop",
        "harvest", "leaf", "seedling", "growing"
    ]):
        stage = "FIELD"

    elif any(word in text for word in [
        "factory", "manufactur", "production",
        "facility", "plant"
    ]):
        stage = "FACTORY"

    elif any(word in text for word in [
        "shortage", "supply", "export",
        "import", "inventory", "shipping"
    ]):
        stage = "SUPPLY"

    elif any(word in text for word in [
        "release", "launch", "new cigar",
        "new line", "announces"
    ]):
        stage = "RELEASE"

    else:
        stage = "INDUSTRY"

    if any(word in text for word in [
        "shutdown", "shortage", "hurricane",
        "disease", "acquisition", "factory closure"
    ]):
        priority = "HIGH"

    elif any(word in text for word in [
        "harvest", "crop", "farm", "factory",
        "supply", "weather", "production"
    ]):
        priority = "MEDIUM"

    else:
        priority = "LOW"

    return stage, priority


def add_item(items, seen_urls, title, source, country, stage,
             priority, url, item_type, why):

    if not url or url in seen_urls:
        return

    items.append({
        "title": title,
        "source": source,
        "date": datetime.utcnow().date().isoformat(),
        "country": country,
        "stage": stage,
        "priority": priority,
        "type": item_type,
        "url": url,
        "why": why
    })

    seen_urls.add(url)


def main():

    if DATA_FILE.exists():
        try:
            database = json.loads(
                DATA_FILE.read_text(encoding="utf-8")
            )
        except Exception:
            database = {"updated": "", "items": []}
    else:
        database = {"updated": "", "items": []}

    items = database.get("items", [])

    seen_urls = {
        item.get("url")
        for item in items
        if item.get("url")
    }

    print("Starting cigar and tobacco intelligence update...")

    # ---------------------------------------------------------
    # DIRECT INDUSTRY RSS FEEDS
    # ---------------------------------------------------------

    for source, feed_url in FEEDS:

        print(f"Checking {source}...")

        try:
            rss_data = fetch(feed_url)
            feed_items = parse_rss(rss_data)

            for article in feed_items:

                stage, priority = classify(
                    article["title"],
                    article["description"]
                )

                add_item(
                    items=items,
                    seen_urls=seen_urls,
                    title=article["title"],
                    source=source,
                    country="GLOBAL",
                    stage=stage,
                    priority=priority,
                    url=article["link"],
                    item_type="Industry Discovery",
                    why=(
                        "Automatically discovered from an industry "
                        "news feed. Verify important developments "
                        "against the primary source."
                    )
                )

        except Exception as error:
            print(f"Feed error for {source}: {error}")

    # ---------------------------------------------------------
    # COUNTRY-SPECIFIC GOOGLE NEWS DISCOVERY
    # ---------------------------------------------------------

    for country, query in QUERIES:

        print(f"Checking {country}...")

        encoded_query = urllib.parse.quote(query)

        rss_url = (
            "https://news.google.com/rss/search?q="
            + encoded_query
            + "&hl=en-US&gl=US&ceid=US:en"
        )

        try:
            rss_data = fetch(rss_url)
            news_items = parse_rss(rss_data)

            for article in news_items:

                stage, priority = classify(
                    article["title"],
                    article["description"]
                )

                add_item(
                    items=items,
                    seen_urls=seen_urls,
                    title=article["title"],
                    source="Google News Discovery",
                    country=country,
                    stage=stage,
                    priority=priority,
                    url=article["link"],
                    item_type="Discovery",
                    why=(
                        "Automatically discovered intelligence lead. "
                        "Verify the underlying report and primary source "
                        "before treating it as confirmed."
                    )
                )

        except Exception as error:
            print(f"News error for {country}: {error}")

    # ---------------------------------------------------------
    # KEEP DATABASE FROM GROWING WITHOUT LIMIT
    # ---------------------------------------------------------

    items = items[-300:]

    database = {
        "updated": datetime.utcnow().isoformat() + "Z",
        "items": items
    }

    DATA_FILE.write_text(
        json.dumps(database, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Intelligence database updated: {len(items)} items")


if __name__ == "__main__":
    main()

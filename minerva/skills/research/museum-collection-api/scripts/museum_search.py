#!/usr/bin/env python3
"""
museum_search.py — Multi-source museum collection API tool for GHB research.

Source priority (all free, no API key required for basic use):
  1. Metropolitan Museum of Art (Met)
  2. Art Institute of Chicago (AIC)
  3. Rijksmuseum
  4. British Museum (may be Cloudflare-blocked; handled gracefully)
  5. Europeana (European aggregator)
  6. Archive.org (text/catalog fallback)

Usage:
  python museum_search.py --query "venus nude mythological" --period 1400-1900
  python museum_search.py --query "susannah bathing biblical" --sources met,aic
  python museum_search.py --query "bathers impressionist" --bibtex --output results.jsonl

As a library (from Hermes skill):
  exec(open('/path/to/museum_search.py').read())
  results = search_all("diana actaeon", period=(1400, 1900))
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

TODAY = date.today().isoformat()
HEADERS = {
    "User-Agent": "GHB-Research/1.0 (academic; contact: vindalf_99@me.com)",
    "Accept": "application/json",
}

# How long to wait between API calls (be polite)
RATE_LIMIT_SEC = 0.5


@dataclass
class MuseumObject:
    source: str
    object_id: str
    title: str
    artist: str
    date_display: str
    date_start: Optional[int]
    date_end: Optional[int]
    medium: str
    department: str
    object_url: str
    image_url: str
    image_available: bool
    accession_number: str
    subject_tags: list = field(default_factory=list)
    description: str = ""
    retrieved: str = TODAY

    def bibtex_key(self) -> str:
        artist_word = (self.artist.split()[-1] if self.artist else "Unknown")
        artist_word = "".join(c for c in artist_word if c.isalpha())
        year = self.date_start or "nd"
        return f"{artist_word}{year}"

    def to_bibtex(self) -> str:
        key = self.bibtex_key()
        source_label = {
            "met": "Metropolitan Museum of Art, New York",
            "aic": "Art Institute of Chicago",
            "rijks": "Rijksmuseum, Amsterdam",
            "bm": "British Museum, London",
            "europeana": "Europeana",
        }.get(self.source, self.source)
        img_note = f" Image: {self.image_url}." if self.image_url else " No image available."
        return (
            f"@misc{{{key},\n"
            f"  author       = {{{self.artist or 'Unknown'}}},\n"
            f"  title        = {{{self.title}}},\n"
            f"  year         = {{{self.date_start or self.date_display or 'n.d.'}}},\n"
            f"  howpublished = {{[{self.medium}]. {source_label}. Accession no. {self.accession_number}}},\n"
            f"  url          = {{{self.object_url}}},\n"
            f"  note         = {{GHB research.{img_note} Retrieved via museum API {self.retrieved}.}}\n"
            f"}}"
        )


def _fetch(url: str, params: dict = None) -> Optional[dict]:
    """Simple JSON fetch with graceful failure."""
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {url}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  [ERROR] {url}: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Metropolitan Museum of Art
# https://metmuseum.github.io/
# ---------------------------------------------------------------------------

def search_met(query: str, period: tuple = None, has_images: bool = True, max_results: int = 50) -> list[MuseumObject]:
    """Search the Met collection. No API key required."""
    params = {
        "q": query,
        "hasImages": str(has_images).lower(),
        "isPublicDomain": "true",
    }
    if period:
        params["dateBegin"] = period[0]
        params["dateEnd"] = period[1]

    print(f"  [Met] Searching: {query!r} {period or ''}")
    data = _fetch("https://collectionapi.metmuseum.org/public/collection/v1/search", params)
    if not data or not data.get("objectIDs"):
        print("  [Met] No results.")
        return []

    ids = data["objectIDs"][:max_results]
    print(f"  [Met] Found {data['total']} total, fetching {len(ids)} records...")
    results = []
    for oid in ids:
        time.sleep(RATE_LIMIT_SEC)
        obj = _fetch(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
        if not obj:
            continue
        results.append(MuseumObject(
            source="met",
            object_id=str(oid),
            title=obj.get("title", ""),
            artist=obj.get("artistDisplayName", ""),
            date_display=obj.get("objectDate", ""),
            date_start=obj.get("objectBeginDate"),
            date_end=obj.get("objectEndDate"),
            medium=obj.get("medium", ""),
            department=obj.get("department", ""),
            object_url=obj.get("objectURL", ""),
            image_url=obj.get("primaryImageSmall", "") or obj.get("primaryImage", ""),
            image_available=bool(obj.get("primaryImage")),
            accession_number=obj.get("accessionNumber", ""),
            subject_tags=[t.get("term", "") for t in (obj.get("tags") or [])],
        ))
    return results


# ---------------------------------------------------------------------------
# Art Institute of Chicago
# https://api.artic.edu/docs/
# ---------------------------------------------------------------------------

def search_aic(query: str, period: tuple = None, max_results: int = 30) -> list[MuseumObject]:
    """Search the AIC collection. No API key required."""
    fields = "id,title,artist_display,date_display,date_start,date_end,medium_display,department_title,image_id,main_reference_number,subject_titles,description"
    # AIC uses POST with Elasticsearch DSL for range queries
    base_url = "https://api.artic.edu/api/v1/artworks/search"
    print(f"  [AIC] Searching: {query!r} {period or ''}")

    if period:
        import urllib.request as _ur
        body = json.dumps({
            "q": query,
            "limit": min(max_results, 100),
            "fields": fields,
            "query": {
                "bool": {
                    "must": [{"query_string": {"query": query}}],
                    "filter": [
                        {"range": {"date_start": {"gte": period[0]}}},
                        {"range": {"date_end": {"lte": period[1]}}},
                    ],
                }
            },
        }).encode()
        req = _ur.Request(base_url, data=body, headers={**HEADERS, "Content-Type": "application/json"}, method="POST")
        try:
            with _ur.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            print(f"  [AIC] Error: {e}", file=sys.stderr)
            data = None
    else:
        data = _fetch(base_url, {"q": query, "limit": min(max_results, 100), "fields": fields})
    if not data or not data.get("data"):
        print("  [AIC] No results.")
        return []

    iiif_base = data.get("config", {}).get("iiif_url", "https://www.artic.edu/iiif/2")
    results = []
    for obj in data["data"]:
        img_id = obj.get("image_id")
        image_url = f"{iiif_base}/{img_id}/full/843,/0/default.jpg" if img_id else ""
        results.append(MuseumObject(
            source="aic",
            object_id=str(obj.get("id", "")),
            title=obj.get("title", ""),
            artist=obj.get("artist_display", ""),
            date_display=obj.get("date_display", ""),
            date_start=obj.get("date_start"),
            date_end=obj.get("date_end"),
            medium=obj.get("medium_display", ""),
            department=obj.get("department_title", ""),
            object_url=f"https://www.artic.edu/artworks/{obj.get('id')}",
            image_url=image_url,
            image_available=bool(img_id),
            accession_number=obj.get("main_reference_number", ""),
            subject_tags=obj.get("subject_titles", []),
            description=obj.get("description", "") or "",
        ))
    print(f"  [AIC] Retrieved {len(results)} records.")
    return results


# ---------------------------------------------------------------------------
# Rijksmuseum
# https://data.rijksmuseum.nl/object-metadata/api/
# No key required for basic search (key unlocks higher rate limits)
# ---------------------------------------------------------------------------

def search_rijks(query: str, period: tuple = None, max_results: int = 30) -> list[MuseumObject]:
    """Search the Rijksmuseum collection."""
    params = {
        "q": query,
        "ps": min(max_results, 100),
        "imgonly": "True",
        "format": "json",
        "culture": "en",
    }
    # Rijks date filter: century-based (16 = 16th century, 17 = 17th, etc.)
    if period:
        start_century = (period[0] // 100) + 1
        end_century = (period[1] // 100) + 1
        if start_century == end_century:
            params["f.dating.period"] = start_century
        # Multi-century: omit date filter, rely on text query

    print(f"  [Rijks] Searching: {query!r} {period or ''}")
    data = _fetch("https://www.rijksmuseum.nl/api/en/collection", params)
    if not data or not data.get("artObjects"):
        print("  [Rijks] No results.")
        return []

    results = []
    for obj in data["artObjects"]:
        img = obj.get("webImage") or {}
        results.append(MuseumObject(
            source="rijks",
            object_id=obj.get("objectNumber", ""),
            title=obj.get("title", ""),
            artist=obj.get("principalOrFirstMaker", ""),
            date_display=str(obj.get("dating", {}).get("presentingDate", "")),
            date_start=obj.get("dating", {}).get("yearEarly"),
            date_end=obj.get("dating", {}).get("yearLate"),
            medium="",
            department="",
            object_url=obj.get("links", {}).get("web", ""),
            image_url=img.get("url", ""),
            image_available=bool(img.get("url")),
            accession_number=obj.get("objectNumber", ""),
        ))
    print(f"  [Rijks] Retrieved {len(results)} records.")
    return results


# ---------------------------------------------------------------------------
# British Museum
# collection.britishmuseum.org — may be Cloudflare-blocked from servers
# Tries the collection search JSON endpoint; skips gracefully if blocked
# ---------------------------------------------------------------------------

def search_bm(query: str, period: tuple = None, max_results: int = 30) -> list[MuseumObject]:
    """
    Attempt British Museum collection search.
    Cloudflare may block this from non-browser contexts.
    Script continues without error if blocked.
    """
    params = {
        "keyword": query,
        "view": "grid",
        "sort": "",
        "page": 1,
        "pageSize": min(max_results, 100),
        "images": "true",
    }
    if period:
        params["fromDate"] = period[0]
        params["toDate"] = period[1]

    print(f"  [BM] Attempting: {query!r} {period or ''}")
    # Try the collection API JSON endpoint
    data = _fetch("https://www.britishmuseum.org/api/collection/search", params)
    if not data:
        # Fallback: try collection.britishmuseum.org SPARQL-style search
        sparql_params = {
            "query": f"""
                SELECT ?object ?title ?date ?image WHERE {{
                  ?object <http://www.w3.org/2004/02/skos/core#prefLabel> ?title .
                  FILTER(CONTAINS(LCASE(?title), LCASE("{query}")))
                }} LIMIT {min(max_results, 50)}
            """,
            "output": "json",
        }
        data = _fetch("https://collection.britishmuseum.org/sparql", sparql_params)

    if not data:
        print("  [BM] Blocked or unavailable — skipping. Use browser-source skill for BM if needed.")
        return []

    # Parse whatever structure was returned (BM API shape varies)
    results = []
    objects = data.get("hits", data.get("results", data.get("data", [])))
    for obj in objects[:max_results]:
        results.append(MuseumObject(
            source="bm",
            object_id=str(obj.get("id", obj.get("systemNumber", ""))),
            title=obj.get("title", obj.get("name", "")),
            artist=obj.get("artist", obj.get("maker", "")),
            date_display=obj.get("date", ""),
            date_start=None,
            date_end=None,
            medium=obj.get("medium", obj.get("type", "")),
            department=obj.get("department", ""),
            object_url=f"https://www.britishmuseum.org/collection/object/{obj.get('systemNumber', obj.get('id', ''))}",
            image_url=obj.get("image", ""),
            image_available=bool(obj.get("image")),
            accession_number=obj.get("systemNumber", obj.get("id", "")),
        ))
    print(f"  [BM] Retrieved {len(results)} records.")
    return results


# ---------------------------------------------------------------------------
# Europeana
# https://api.europeana.eu/ — no key required for basic searches
# ---------------------------------------------------------------------------

def search_europeana(query: str, period: tuple = None, max_results: int = 30) -> list[MuseumObject]:
    """Search Europeana — aggregates European museum collections."""
    params = {
        "query": query,
        "media": "true",
        "rows": min(max_results, 100),
        "profile": "rich",
        "qf": "TYPE:IMAGE",
    }
    if period:
        params["qf"] = [params["qf"], f"YEAR:[{period[0]} TO {period[1]}]"]

    print(f"  [Europeana] Searching: {query!r} {period or ''}")
    data = _fetch("https://api.europeana.eu/record/v2/search.json", params)
    if not data or not data.get("items"):
        print("  [Europeana] No results.")
        return []

    results = []
    for item in data["items"][:max_results]:
        title = item.get("title", [""])[0] if isinstance(item.get("title"), list) else item.get("dcTitle", [""])[0] if item.get("dcTitle") else ""
        creator = item.get("dcCreator", [""])[0] if item.get("dcCreator") else ""
        year = item.get("year", [""])[0] if item.get("year") else ""
        img = item.get("edmPreview", [""])[0] if item.get("edmPreview") else ""
        results.append(MuseumObject(
            source="europeana",
            object_id=item.get("id", ""),
            title=title,
            artist=creator,
            date_display=str(year),
            date_start=int(year) if str(year).isdigit() else None,
            date_end=None,
            medium=item.get("type", ""),
            department="",
            object_url=f"https://www.europeana.eu/item{item.get('id', '')}",
            image_url=img,
            image_available=bool(img),
            accession_number=item.get("id", ""),
        ))
    print(f"  [Europeana] Retrieved {len(results)} records.")
    return results


# ---------------------------------------------------------------------------
# Uffizi Galleries (Florence)
# https://www.uffizi.it/en/works — home of Botticelli, Raphael, Michelangelo, Titian
# Public collection data via their search API
# ---------------------------------------------------------------------------

def search_uffizi(query: str, period: tuple = None, max_results: int = 30) -> list[MuseumObject]:
    """
    Search the Uffizi Galleries collection.
    Core Italian Renaissance holdings: Botticelli, Raphael, Michelangelo, Leonardo, Titian.
    """
    params = {
        "q": query,
        "lang": "en",
        "limit": min(max_results, 50),
    }
    if period:
        params["date_from"] = period[0]
        params["date_to"] = period[1]

    print(f"  [Uffizi] Searching: {query!r} {period or ''}")
    data = _fetch("https://www.uffizi.it/api/v1/artworks/search", params)

    # Fallback: try Europeana filtered to Uffizi as data provider
    if not data:
        euro_params = {
            "query": f"{query} DATA_PROVIDER:\"Uffizi Gallery\"",
            "media": "true",
            "rows": min(max_results, 50),
            "profile": "rich",
            "qf": "TYPE:IMAGE",
        }
        if period:
            euro_params["qf"] = [euro_params["qf"], f"YEAR:[{period[0]} TO {period[1]}]"]
        data = _fetch("https://api.europeana.eu/record/v2/search.json", euro_params)
        if data and data.get("items"):
            # Re-use Europeana parser but tag source as uffizi
            results = []
            for item in data["items"][:max_results]:
                title = item.get("title", [""])[0] if isinstance(item.get("title"), list) else ""
                creator = item.get("dcCreator", [""])[0] if item.get("dcCreator") else ""
                year = item.get("year", [""])[0] if item.get("year") else ""
                img = item.get("edmPreview", [""])[0] if item.get("edmPreview") else ""
                results.append(MuseumObject(
                    source="uffizi",
                    object_id=item.get("id", ""),
                    title=title,
                    artist=creator,
                    date_display=str(year),
                    date_start=int(year) if str(year).isdigit() else None,
                    date_end=None,
                    medium="",
                    department="",
                    object_url=f"https://www.europeana.eu/item{item.get('id', '')}",
                    image_url=img,
                    image_available=bool(img),
                    accession_number=item.get("id", ""),
                ))
            print(f"  [Uffizi via Europeana] Retrieved {len(results)} records.")
            return results
        print("  [Uffizi] Unavailable — skipping.")
        return []

    objects = data.get("results", data.get("data", data.get("artworks", [])))
    results = []
    for obj in objects[:max_results]:
        img = obj.get("image", obj.get("thumbnail", ""))
        if isinstance(img, dict):
            img = img.get("url", "")
        results.append(MuseumObject(
            source="uffizi",
            object_id=str(obj.get("id", "")),
            title=obj.get("title", obj.get("name", "")),
            artist=obj.get("artist", obj.get("author", "")),
            date_display=str(obj.get("date", "")),
            date_start=obj.get("date_start") or obj.get("yearFrom"),
            date_end=obj.get("date_end") or obj.get("yearTo"),
            medium=obj.get("technique", obj.get("medium", "")),
            department=obj.get("department", "Uffizi Galleries, Florence"),
            object_url=obj.get("url", f"https://www.uffizi.it/en/works/{obj.get('id', '')}"),
            image_url=img,
            image_available=bool(img),
            accession_number=str(obj.get("inventory", obj.get("accession", obj.get("id", "")))),
        ))
    print(f"  [Uffizi] Retrieved {len(results)} records.")
    return results


# ---------------------------------------------------------------------------
# Louvre Museum
# https://collections.louvre.fr — public JSON collection API
# No API key required; critical for Renaissance, mythology, European masters
# ---------------------------------------------------------------------------

def search_louvre(query: str, period: tuple = None, max_results: int = 30) -> list[MuseumObject]:
    """Search the Louvre collection API."""
    params = {
        "q": query,
        "limit": min(max_results, 100),
        "page": 1,
    }
    if period:
        params["dates_from"] = period[0]
        params["dates_to"] = period[1]

    print(f"  [Louvre] Searching: {query!r} {period or ''}")

    # Primary: JSON search endpoint
    data = _fetch("https://collections.louvre.fr/en/api/search", params)

    # Fallback: try the search page with json=true parameter
    if not data:
        params2 = {"q": query, "json": "true"}
        data = _fetch("https://collections.louvre.fr/en/recherche", params2)

    if not data:
        print("  [Louvre] Unavailable — skipping.")
        return []

    # The Louvre API returns results under various keys depending on version
    objects = (
        data.get("results")
        or data.get("hits", {}).get("hits", [])
        or data.get("items")
        or []
    )

    results = []
    for obj in objects[:max_results]:
        # Handle both direct objects and Elasticsearch _source wrappers
        src = obj.get("_source", obj)
        ark = src.get("ark", src.get("id", ""))
        title = src.get("title", src.get("titre", src.get("objectName", "")))
        if isinstance(title, list):
            title = title[0] if title else ""
        artist = src.get("artist", src.get("auteur", src.get("principalMaker", "")))
        if isinstance(artist, list):
            artist = "; ".join(artist)
        date_disp = src.get("dated", src.get("date", src.get("dateCreated", "")))
        img = src.get("image", src.get("thumbnail", src.get("imageUrl", "")))
        if isinstance(img, dict):
            img = img.get("url", "")
        obj_url = f"https://collections.louvre.fr/ark:/{ark}" if ark else ""
        accession = src.get("inventoryNumber", src.get("reference", ark))

        results.append(MuseumObject(
            source="louvre",
            object_id=str(ark),
            title=title or "",
            artist=artist or "",
            date_display=str(date_disp) if date_disp else "",
            date_start=src.get("dateFrom") or src.get("yearStart"),
            date_end=src.get("dateTo") or src.get("yearEnd"),
            medium=src.get("materials", src.get("medium", src.get("technique", ""))),
            department=src.get("department", src.get("departement", "")),
            object_url=obj_url,
            image_url=img or "",
            image_available=bool(img),
            accession_number=str(accession) if accession else "",
        ))

    print(f"  [Louvre] Retrieved {len(results)} records.")
    return results


# ---------------------------------------------------------------------------
# Wikimedia Commons
# Critical for named Italian/Spanish masters: Botticelli, Raphael, Michelangelo,
# El Greco, Titian, Velázquez, Caravaggio — all public domain, fully indexed.
# No API key, no Cloudflare, MediaWiki API.
# ---------------------------------------------------------------------------

def search_wikimedia(query: str, period: tuple = None, max_results: int = 30) -> list[MuseumObject]:
    """
    Search Wikimedia Commons for art works.
    Particularly strong for famous named works and artists from Italian/Spanish Renaissance.
    Returns file pages with image URLs directly usable for GHB illustration candidates.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"{query} filetype:bitmap",
        "srnamespace": "6",  # File namespace
        "srlimit": min(max_results, 50),
        "format": "json",
        "utf8": "1",
    }
    print(f"  [Wikimedia] Searching: {query!r}")
    data = _fetch("https://commons.wikimedia.org/w/api.php", params)
    if not data or not data.get("query", {}).get("search"):
        print("  [Wikimedia] No results.")
        return []

    hits = data["query"]["search"]
    # Batch fetch image info
    titles = "|".join(h["title"] for h in hits[:max_results])
    info_params = {
        "action": "query",
        "titles": titles,
        "prop": "imageinfo|categories",
        "iiprop": "url|extmetadata",
        "format": "json",
    }
    info_data = _fetch("https://commons.wikimedia.org/w/api.php", info_params)
    pages = info_data.get("query", {}).get("pages", {}) if info_data else {}

    results = []
    for page in pages.values():
        if page.get("missing") is not None:
            continue
        title = page.get("title", "").replace("File:", "")
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {})
        image_url = ii.get("url", "")
        obj_url = ii.get("descriptionurl", "")

        artist = meta.get("Artist", {}).get("value", "")
        # Strip HTML from artist field
        if "<" in artist:
            import re as _re
            artist = _re.sub(r"<[^>]+>", "", artist).strip()

        import re as _re
        date_raw = meta.get("DateTimeOriginal", meta.get("Date", {})).get("value", "")
        # Strip HTML and Wikidata QS annotations from date field
        date_clean = _re.sub(r"<[^>]+>", "", date_raw).strip() if date_raw else ""
        date_clean = _re.sub(r"date QS:[^\s]+(\s+[^\s]+)*", "", date_clean).strip()
        date_year = None
        if date_clean:
            m = _re.search(r"\b(1[3-9]\d{2})\b", date_clean)
            if m:
                date_year = int(m.group(1))

        # Skip if period filter set and year is outside range
        if period and date_year:
            if date_year < period[0] or date_year > period[1]:
                continue

        description = meta.get("ImageDescription", {}).get("value", "")
        if "<" in description:
            import re as _re
            description = _re.sub(r"<[^>]+>", "", description).strip()

        results.append(MuseumObject(
            source="wikimedia",
            object_id=str(page.get("pageid", "")),
            title=title,
            artist=artist,
            date_display=date_clean,
            date_start=date_year,
            date_end=date_year,
            medium=meta.get("Medium", {}).get("value", ""),
            department="Wikimedia Commons",
            object_url=obj_url,
            image_url=image_url,
            image_available=bool(image_url),
            accession_number=str(page.get("pageid", "")),
            description=description[:300],
        ))

    print(f"  [Wikimedia] Retrieved {len(results)} records.")
    return results


# ---------------------------------------------------------------------------
# Archive.org — text/catalog fallback
# ---------------------------------------------------------------------------

def search_archive(query: str, mediatype: str = "texts", max_results: int = 20) -> list[dict]:
    """
    Search Archive.org for museum catalogs, exhibition publications, art history texts.
    Returns raw dicts (not MuseumObject — these are publications, not objects).
    """
    params = {
        "q": f"{query} AND mediatype:{mediatype}",
        "output": "json",
        "rows": max_results,
        "fl": "identifier,title,creator,date,description,subject",
    }
    print(f"  [Archive.org] Searching publications: {query!r}")
    data = _fetch("https://archive.org/advancedsearch.php", params)
    if not data:
        return []
    docs = data.get("response", {}).get("docs", [])
    print(f"  [Archive.org] Found {len(docs)} text records.")
    return docs


# ---------------------------------------------------------------------------
# Combined search
# ---------------------------------------------------------------------------

SOURCE_MAP = {
    "met": search_met,
    "aic": search_aic,
    "rijks": search_rijks,
    "uffizi": search_uffizi,
    "louvre": search_louvre,
    "wikimedia": search_wikimedia,
    "bm": search_bm,
    "europeana": search_europeana,
}

DEFAULT_SOURCES = ["met", "aic", "rijks", "wikimedia", "uffizi", "louvre", "bm", "europeana"]


def search_all(
    query: str,
    period: tuple = None,
    sources: list = None,
    max_per_source: int = 30,
    include_archive: bool = False,
) -> list[MuseumObject]:
    """Run query across all sources, return combined deduped results."""
    sources = sources or DEFAULT_SOURCES
    all_results = []
    for src in sources:
        fn = SOURCE_MAP.get(src)
        if not fn:
            print(f"  Unknown source: {src}", file=sys.stderr)
            continue
        time.sleep(RATE_LIMIT_SEC)
        try:
            results = fn(query, period=period, max_results=max_per_source)
            all_results.extend(results)
        except Exception as e:
            print(f"  [{src.upper()}] Error: {e}", file=sys.stderr)

    if include_archive:
        archive_results = search_archive(query)
        # Print summary only — archive results are publications, handled separately
        if archive_results:
            print(f"\nArchive.org text sources ({len(archive_results)} found):")
            for doc in archive_results[:5]:
                print(f"  {doc.get('title', 'Untitled')} — {doc.get('creator', '')} ({doc.get('date', '')})")
                print(f"    https://archive.org/details/{doc.get('identifier', '')}")

    return all_results


def print_summary(results: list[MuseumObject]):
    by_source = {}
    for r in results:
        by_source.setdefault(r.source, []).append(r)

    total_with_images = sum(1 for r in results if r.image_available)
    print(f"\n{'='*60}")
    print(f"RESULTS: {len(results)} objects | {total_with_images} with images")
    print(f"{'='*60}")
    for src, items in by_source.items():
        imgs = sum(1 for i in items if i.image_available)
        print(f"  {src.upper():12} {len(items):3} objects  ({imgs} with images)")
    print()

    for r in results:
        img_flag = "[IMG]" if r.image_available else "     "
        print(f"{img_flag} {r.source.upper():8} | {r.date_display or 'n.d.':12} | {r.artist or 'Unknown artist':30} | {r.title[:60]}")


def write_jsonl(results: list[MuseumObject], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in results:
            f.write(json.dumps(asdict(r)) + "\n")
    print(f"\nWrote {len(results)} records to {path}")


def write_bibtex(results: list[MuseumObject], path: str):
    header = (
        "% GHB Reference Library — Global History of Erotic Art\n"
        "% Museum object records retrieved via collection APIs\n"
        "% Import into Zotero: File > Import > BibTeX\n\n"
    )
    entries = [r.to_bibtex() for r in results]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        if Path(path).stat().st_size == 0 if Path(path).exists() else True:
            f.write(header)
        f.write("\n\n".join(entries) + "\n")
    print(f"Appended {len(entries)} BibTeX entries to {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Museum collection API search for GHB research")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--period", "-p", default=None, help="Date range, e.g. 1400-1900")
    parser.add_argument("--sources", "-s", default=",".join(DEFAULT_SOURCES),
                        help=f"Comma-separated sources: {','.join(DEFAULT_SOURCES)}")
    parser.add_argument("--max", "-n", type=int, default=30, help="Max results per source")
    parser.add_argument("--output", "-o", default=None, help="Output JSONL file path")
    parser.add_argument("--bibtex", "-b", default=None, help="BibTeX output file path")
    parser.add_argument("--archive", action="store_true", help="Also search Archive.org for texts")
    args = parser.parse_args()

    period = None
    if args.period:
        parts = args.period.split("-")
        if len(parts) == 2:
            period = (int(parts[0]), int(parts[1]))

    sources = [s.strip() for s in args.sources.split(",")]

    print(f"\nMuseum Collection Search")
    print(f"  Query:   {args.query}")
    print(f"  Period:  {period or 'any'}")
    print(f"  Sources: {sources}\n")

    results = search_all(
        args.query,
        period=period,
        sources=sources,
        max_per_source=args.max,
        include_archive=args.archive,
    )

    print_summary(results)

    if args.output:
        write_jsonl(results, args.output)

    if args.bibtex:
        write_bibtex(results, args.bibtex)

    if not args.output and not args.bibtex:
        print("\nTip: use --output results.jsonl and --bibtex GHB_bibliography.bib to save results.")

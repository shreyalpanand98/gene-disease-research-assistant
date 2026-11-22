"""Look up definitions in public NIH references using exact term matches."""

from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import re
from urllib.parse import quote, urlsplit
from xml.etree import ElementTree

import requests


def _key(text):
    return " ".join(re.findall(r"[\w]+", text.casefold()))


class _Markup(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.metadata = {}
        self.parts = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            attrs = dict(attrs)
            self.metadata[attrs.get("property") or attrs.get("name")] = attrs.get("content", "")

    def handle_data(self, data):
        self.parts.append(data)

    @property
    def text(self):
        return " ".join("".join(self.parts).split())


def _get(url, **kwargs):
    response = requests.get(url, timeout=(3, 5), allow_redirects=False, **kwargs)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    if response.status_code != 200:
        raise ValueError("Unexpected reference response status")
    return response


def _reference(title, publisher, url, text):
    return {"title": title, "publisher": publisher, "url": url, "text": " ".join(text.split())[:1800]}


def _nhgri(term):
    slug = "-".join(word if word.isupper() else word.capitalize() for word in term.split())
    url = "https://www.genome.gov/genetics-glossary/" + quote(slug, safe="-")
    response = _get(url)
    if response is None:
        return []
    tags = _Markup(response.text).metadata
    title, definition = tags.get("og:title", ""), tags.get("description", "")
    if _key(title) == _key(term) and definition:
        return [_reference(title, "NHGRI Talking Glossary", url, definition)]
    return []


def _nci(term, dictionary, audience, page):
    slug = quote(_key(term).replace(" ", "-"), safe="-")
    response = _get(f"https://webapis.cancer.gov/glossary/v1/Terms/{dictionary}/{audience}/en/{slug}")
    if response is None:
        return []
    record = response.json()
    title = record.get("termName", "")
    definition = (record.get("definition") or {}).get("text", "")
    if _key(title) == _key(term) and definition:
        url = f"https://www.cancer.gov/publications/dictionaries/{page}/def/{slug}"
        publisher = "NCI Dictionary of Cancer Terms" if audience == "Patient" else "NCI Dictionary of Genetics Terms"
        return [_reference(title, publisher, url, definition)]
    return []


def _medlineplus(term):
    response = _get("https://wsearch.nlm.nih.gov/ws/query", params={
        "db": "healthTopics", "term": f'"{term}"', "retmax": 10, "rettype": "brief",
        "tool": "helix-research-assistant",
    })
    if response is None:
        return []
    matches = {}
    for document in ElementTree.fromstring(response.content).findall("./list/document"):
        fields = {}
        for element in document.findall("content"):
            fields.setdefault(element.get("name"), []).append("".join(element.itertext()))
        title = _Markup(fields.get("title", [""])[0]).text
        names = [title, *(_Markup(alias).text for alias in fields.get("altTitle", []))]
        url = document.get("url", "")
        parsed = urlsplit(url)
        if _key(term) not in map(_key, names) or parsed.scheme != "https" or parsed.netloc != "medlineplus.gov":
            continue
        summary = fields.get("FullSummary", [""])[0]
        intro = re.search(r"<p\b[^>]*>(.*?)</p>", summary, re.I | re.S)
        text = _Markup(intro[1] if intro else summary).text
        if text:
            matches[url] = _reference(title, "MedlinePlus", url, text)
    return list(matches.values())


def lookup_definition(term):
    """Return matching references or a distinct ambiguous, missing or unavailable outcome."""
    term = " ".join(term.split())
    if not term or len(term) > 100 or not re.fullmatch(r"[\w .’'()/+–-]+", term):
        return {"status": "clarify", "sources": []}

    with ThreadPoolExecutor(max_workers=4) as executor:
        lookups = [
            executor.submit(_nhgri, term),
            executor.submit(_nci, term, "Cancer.gov", "Patient", "cancer-terms"),
            executor.submit(_nci, term, "Genetics", "HealthProfessional", "genetics-dictionary"),
            executor.submit(_medlineplus, term),
        ]
        sources = []
        failures = 0
        medline_matches = []
        technical_matches = []
        for index, lookup in enumerate(lookups):
            try:
                matches = lookup.result()
            except (requests.RequestException, ValueError, ElementTree.ParseError):
                failures += 1
                continue
            if index == 3:
                medline_matches = matches
            elif index == 2:
                technical_matches = matches
            else:
                sources.extend(matches)

    if not sources and not technical_matches and len(medline_matches) > 1:
        return {"status": "clarify", "sources": medline_matches}
    sources.extend(medline_matches if len(medline_matches) == 1 else [])
    sources.extend(technical_matches)
    status = "found" if sources else "unavailable" if failures == len(lookups) else "not_found"
    return {"status": status, "sources": sources}

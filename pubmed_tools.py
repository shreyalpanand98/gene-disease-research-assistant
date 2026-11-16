
import requests

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def search_pubmed(query: str, max_results: int = 5) -> list[str]:
    """Search PubMed and return matching article PMIDs."""

    if not query.strip():
        return []

    url = f"{BASE_URL}/esearch.fcgi"

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "relevance"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )
    response.raise_for_status()

    data = response.json()

    return data["esearchresult"]["idlist"]


def get_pubmed_details(pmids: list[str]) -> list[dict]:
    """Retrieve article metadata from PubMed."""

    if not pmids:
        return []

    url = f"{BASE_URL}/esummary.fcgi"

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )
    response.raise_for_status()

    data = response.json()

    articles = []

    for pmid in pmids:
        record = data["result"].get(pmid)

        if record is None:
            continue

        authors = [
            author["name"]
            for author in record.get("authors", [])
            if "name" in author
        ]

        article = {
            "pmid": pmid,
            "title": record.get("title", "Unknown"),
            "authors": authors,
            "publication_date": record.get("pubdate", "Unknown"),
            "journal": record.get("fulljournalname", "Unknown"),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        }

        articles.append(article)

    return articles


import xml.etree.ElementTree as ET


def get_pubmed_abstracts(pmids: list[str]) -> dict[str, str]:
    """Retrieve available PubMed abstracts by PMID."""

    if not pmids:
        return {}

    url = f"{BASE_URL}/efetch.fcgi"

    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }

    response = requests.get(
        url,
        params=params,
        timeout=20
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    abstracts = {}

    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID")

        parts = []

        for section in article.findall(
            ".//MedlineCitation/Article/Abstract/AbstractText"
        ):
            text = "".join(section.itertext()).strip()
            label = section.get("Label")

            if text:
                parts.append(f"{label}: {text}" if label else text)

        if pmid:
            abstracts[pmid] = "\n".join(parts) if parts else "Abstract unavailable"

    return abstracts


def research_pubmed(query: str, max_results: int = 3) -> list[dict]:
    """Find PubMed articles and return metadata with abstracts."""

    # Step 1: Find matching articles
    pmids = search_pubmed(query, max_results)

    if not pmids:
        return []

    # Step 2: Retrieve article information
    articles = get_pubmed_details(pmids)

    # Step 3: Retrieve abstracts
    abstracts = get_pubmed_abstracts(pmids)

    # Step 4: Combine metadata and abstracts
    for article in articles:
        pmid = article["pmid"]

        article["abstract"] = abstracts.get(
            pmid,
            "Abstract unavailable"
        )

    return articles


from pubmed_tools import get_pubmed_abstracts, search_pubmed, get_pubmed_details

query = "PKD1 AND autosomal dominant polycystic kidney disease"

try:
    print("Searching PubMed...")

    pmids = search_pubmed(query, max_results=3)
    articles = get_pubmed_details(pmids)
    abstracts = get_pubmed_abstracts(pmids)

    print(f"\nFound {len(articles)} articles\n")

    
    # Combine each article's metadata with its abstract
    for article in articles:
        pmid = article["pmid"]
        article["abstract"] = abstracts.get(
            pmid,
            "Abstract unavailable"
        )

    # Display the complete research record
    for article in articles:
        print("\n" + "=" * 60)
        print("Title:", article["title"])
        print("Date:", article["publication_date"])
        print("PMID:", article["pmid"])
        print("Abstract:", article["abstract"][:500])
        print("Source:", article["url"])

except Exception as error:
    print("Error:", error)

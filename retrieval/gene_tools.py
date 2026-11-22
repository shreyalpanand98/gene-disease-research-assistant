import requests
from retrieval.ncbi_utils import ncbi_get

gene_database = {
    "PKD1": {
        "disease": "Autosomal Dominant Polycystic Kidney Disease",
        "protein": "Polycystin-1"
    },
    "PKD2": {
        "disease": "Autosomal Dominant Polycystic Kidney Disease",
        "protein": "Polycystin-2"
    },
    "CFTR": {
        "disease": "Cystic Fibrosis",
        "protein": "CFTR Protein"
    }
}

def search_gene(gene_name):
    if gene_name in gene_database:
        return gene_database[gene_name]

    return None

def search_ncbi_gene(gene_name):
    # Step 1: Clean the user's input
    gene_name = gene_name.strip().upper()

    if not gene_name:
        return None

    # Step 2: Search NCBI for matching gene IDs
    search_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    )

    search_params = {
        "db": "gene",
        "term": f"{gene_name}[Gene Name] AND Homo sapiens[Organism]",
        "retmode": "json",
        "retmax": 20
    }

    response = requests.get(
        search_url,
        params=search_params,
        timeout=15
    )
    response.raise_for_status()

    search_data = response.json()
    gene_ids = search_data["esearchresult"]["idlist"]

    if not gene_ids:
        return None

    # Step 3: Fetch the gene details
    summary_url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    )

    summary_params = {
        "db": "gene",
        "id": ",".join(gene_ids),
        "retmode": "json"
    }

    response = requests.get(
        summary_url,
        params=summary_params,
        timeout=15
    )
    response.raise_for_status()

    summary_data = response.json()

    # Step 4: Find the exact gene symbol
    for gene_id in gene_ids:
        record = summary_data["result"][gene_id]

        if record["name"].upper() == gene_name:
            return {
                "gene_id": gene_id,
                "symbol": record["name"],
                "description": record["description"],
                "summary": record.get("summary", ""),
                "source": f"https://www.ncbi.nlm.nih.gov/gene/{gene_id}"
            }

    # Step 5: No exact match
    return None

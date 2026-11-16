# To test if the code. can call ncbi for PKD1 data.
import requests

url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

params = {
    "db": "gene",
    "term": "PKD1[Gene Name] AND Homo sapiens[Organism]",
    "retmode": "json"
}

response = requests.get(
    url,
    params=params,
    timeout=15
)

response.raise_for_status()

data = response.json()

print("NCBI Gene IDs:", data["esearchresult"]["idlist"])

# Get the gene IDs from our ESearch result
gene_ids = data["esearchresult"]["idlist"]

# Fetch the details of each matching gene
summary_url = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
)

summary_params = {
    "db": "gene",
    "id": ",".join(gene_ids),
    "retmode": "json"
}

summary_response = requests.get(
    summary_url,
    params=summary_params,
    timeout=15
)

summary_response.raise_for_status()

summary_data = summary_response.json()

search_gene = "PKD1"

matched_gene = None

for gene_id in gene_ids:
    record = summary_data["result"][gene_id]

    if record["name"].upper() == search_gene.upper():
        matched_gene = record
        break

if matched_gene:
    print("Exact gene match found!")
    print("Gene ID:", matched_gene["uid"])
    print("Official symbol:", matched_gene["name"])
    print("Description:", matched_gene["description"])
    print("Summary:", matched_gene.get("summary", "Not available"))
else:
    print("No exact gene symbol match found.")
